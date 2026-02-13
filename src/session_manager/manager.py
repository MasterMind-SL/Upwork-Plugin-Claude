"""Session Manager HTTP service.

Runs as a lightweight local web server that bridges the MCP server
to the Camoufox browser. Handles browser lifecycle, scraping,
and cookie management.

Endpoints:
    POST /start         - Launch browser, attempt session restore
    GET  /status        - Return session state
    POST /stop          - Close browser, save state
    POST /scrape/best-matches  - Scrape best matches
    POST /scrape/search        - Scrape search results
    POST /scrape/job-detail    - Scrape single job detail
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime

import aiosqlite
from aiohttp import web

from ..config import DB_PATH, SESSION_MANAGER_HOST, SESSION_MANAGER_PORT, ensure_dirs
from ..database.models import initialize_db
from ..database.repository import JobRepository
from ..models.job import SearchParams
from .browser import BrowserSession
from .scraper import UpworkScraper

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class SessionManager:
    """Orchestrates browser sessions and scraping operations."""

    def __init__(self):
        self.browser = BrowserSession()
        self.db: aiosqlite.Connection | None = None
        self.repo: JobRepository | None = None
        self._last_scrape_time: str | None = None

    async def setup(self):
        """Initialize database connection."""
        ensure_dirs()
        self.db = await aiosqlite.connect(str(DB_PATH))
        self.db.row_factory = aiosqlite.Row
        await initialize_db(self.db)
        self.repo = JobRepository(self.db)

    async def cleanup(self):
        """Clean up resources."""
        await self.browser.stop()
        if self.db:
            await self.db.close()

    def _get_scraper(self) -> UpworkScraper:
        """Create a scraper with current session cookies."""
        if not self.browser.is_authenticated:
            raise RuntimeError("Not authenticated. Start a session first.")
        return UpworkScraper(self.browser.cookies, self.browser.user_agent)


# ── HTTP Handlers ────────────────────────────────────────────────────────────


async def handle_start(request: web.Request) -> web.Response:
    mgr: SessionManager = request.app["manager"]
    body = await request.json() if request.content_length else {}
    headless = body.get("headless", False)

    result = await mgr.browser.start(headless=headless)
    return web.json_response(result)


async def handle_status(request: web.Request) -> web.Response:
    mgr: SessionManager = request.app["manager"]

    jobs_count = await mgr.repo.get_job_count() if mgr.repo else 0

    status = {
        "is_active": mgr.browser.is_authenticated,
        "state": "active" if mgr.browser.is_authenticated else (
            "running" if mgr.browser.is_running else "not_running"
        ),
        "cookie_count": len(mgr.browser.cookies),
        "jobs_in_cache": jobs_count,
        "last_scrape_time": mgr._last_scrape_time,
        "message": "",
    }
    return web.json_response(status)


async def handle_check_auth(request: web.Request) -> web.Response:
    mgr: SessionManager = request.app["manager"]
    result = await mgr.browser.check_auth()
    return web.json_response(result)


async def handle_stop(request: web.Request) -> web.Response:
    mgr: SessionManager = request.app["manager"]
    await mgr.browser.stop()
    return web.json_response({"message": "Session stopped. Cached data is still available."})


async def handle_scrape_best_matches(request: web.Request) -> web.Response:
    mgr: SessionManager = request.app["manager"]
    body = await request.json() if request.content_length else {}
    max_jobs = body.get("max_jobs", 20)

    if not mgr.browser.is_authenticated:
        return web.json_response(
            {"error": "Not authenticated. Call /start first."},
            status=401,
        )

    try:
        from pathlib import Path
        from ..constants import UPWORK_BEST_MATCHES_URL

        # Step 1: Navigate to Best Matches
        logger.info(f"[SCRAPE] Step 1: Navigating to {UPWORK_BEST_MATCHES_URL}")
        html = await mgr.browser.get_page_html(UPWORK_BEST_MATCHES_URL)
        logger.info(f"[SCRAPE] Step 1 done: got {len(html)} chars from get_page_html")

        # Step 2: Scroll to load more jobs
        logger.info("[SCRAPE] Step 2: Scrolling to load more jobs...")
        html = await mgr.browser.scroll_and_collect(max_scrolls=5)
        logger.info(f"[SCRAPE] Step 2 done: got {len(html)} chars after scrolling")

        # Save HTML for debugging
        debug_path = Path("data/debug_best_matches.html")
        try:
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            debug_path.write_text(html, encoding="utf-8")
            logger.info(f"[SCRAPE] Debug HTML saved to {debug_path.resolve()}")
        except Exception as e:
            logger.warning(f"[SCRAPE] Could not save debug HTML: {e}")

        # Step 3: Parse tiles + fetch details
        logger.info(f"[SCRAPE] Step 3: Parsing tiles and fetching details (max_jobs={max_jobs})...")
        logger.info(f"[SCRAPE] Cookie count for scraper: {len(mgr.browser.cookies)}")
        async with mgr._get_scraper() as scraper:
            jobs = await scraper.fetch_best_matches(max_jobs=max_jobs, browser_html=html)
        logger.info(f"[SCRAPE] Step 3 done: got {len(jobs)} jobs with full details")

        # Step 4: Save to database
        if mgr.repo:
            await mgr.repo.upsert_jobs(jobs)
            logger.info(f"[SCRAPE] Step 4: Saved {len(jobs)} jobs to database")

        mgr._last_scrape_time = datetime.utcnow().isoformat()

        summaries = [j.model_dump(exclude={"raw_html", "description"}) for j in jobs]
        return web.json_response({"jobs": summaries, "count": len(jobs)})

    except Exception as e:
        logger.error(f"Best matches scrape failed: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_scrape_search(request: web.Request) -> web.Response:
    mgr: SessionManager = request.app["manager"]
    body = await request.json() if request.content_length else {}

    try:
        params = SearchParams(**body)
    except Exception as e:
        return web.json_response({"error": f"Invalid params: {e}"}, status=400)

    if not mgr.browser.is_authenticated:
        return web.json_response(
            {"error": "Not authenticated. Call /start first."},
            status=401,
        )

    try:
        logger.info(f"[SEARCH] query='{params.query}', max_results={params.max_results}")
        async with mgr._get_scraper() as scraper:
            jobs = await scraper.search_jobs(params)
        logger.info(f"[SEARCH] Got {len(jobs)} jobs from scraper")

        if mgr.repo:
            await mgr.repo.upsert_jobs(jobs)

        mgr._last_scrape_time = datetime.utcnow().isoformat()

        summaries = [j.model_dump(exclude={"raw_html", "description"}) for j in jobs]
        return web.json_response({"jobs": summaries, "count": len(jobs)})

    except Exception as e:
        logger.error(f"Search scrape failed: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_scrape_job_detail(request: web.Request) -> web.Response:
    mgr: SessionManager = request.app["manager"]
    body = await request.json() if request.content_length else {}
    job_url = body.get("job_url", "")

    if not job_url:
        return web.json_response({"error": "job_url is required."}, status=400)

    if not mgr.browser.is_authenticated:
        return web.json_response(
            {"error": "Not authenticated. Call /start first."},
            status=401,
        )

    try:
        async with mgr._get_scraper() as scraper:
            job = await scraper.fetch_job_detail(job_url)

        if mgr.repo:
            await mgr.repo.upsert_job(job)

        return web.json_response({"job": job.model_dump(exclude={"raw_html"})})

    except Exception as e:
        logger.error(f"Job detail scrape failed: {e}")
        return web.json_response({"error": str(e)}, status=500)


# ── App Factory ──────────────────────────────────────────────────────────────


async def on_startup(app: web.Application):
    mgr = SessionManager()
    await mgr.setup()
    app["manager"] = mgr
    logger.info(f"Session Manager started on {SESSION_MANAGER_HOST}:{SESSION_MANAGER_PORT}")


async def on_cleanup(app: web.Application):
    mgr: SessionManager = app["manager"]
    await mgr.cleanup()
    logger.info("Session Manager stopped.")


def create_app() -> web.Application:
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    app.router.add_post("/start", handle_start)
    app.router.add_get("/status", handle_status)
    app.router.add_post("/check-auth", handle_check_auth)
    app.router.add_post("/stop", handle_stop)
    app.router.add_post("/scrape/best-matches", handle_scrape_best_matches)
    app.router.add_post("/scrape/search", handle_scrape_search)
    app.router.add_post("/scrape/job-detail", handle_scrape_job_detail)

    return app


def main():
    """Run the session manager as a standalone HTTP service."""
    app = create_app()
    web.run_app(app, host=SESSION_MANAGER_HOST, port=SESSION_MANAGER_PORT)


if __name__ == "__main__":
    main()
