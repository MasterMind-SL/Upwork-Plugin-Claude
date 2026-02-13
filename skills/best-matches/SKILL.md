---
name: best-matches
description: Fetch and display your Upwork Best Matches. Use when the user wants to see their personalized job recommendations from Upwork, or mentions "best matches", "my jobs", "job recommendations".
---

# Fetch Upwork Best Matches

Fetch the user's personalized Upwork Best Matches using the MCP tools.

## Steps

1. **Check session**: Call `tool_session_status` to check if the browser session is authenticated.
   - If state is "active": proceed to step 2.
   - Otherwise: Call `tool_start_session(headless=false)`. A browser window will open. Tell the user to log in to Upwork and solve any CAPTCHAs. When the user confirms, call `tool_check_auth` to verify.

2. **Fetch jobs**: Call `tool_fetch_best_matches(max_jobs=$ARGUMENTS or 20, force_refresh=true)`.

3. **Present results** as a clean numbered list with:
   - Job title (bold)
   - Budget / hourly rate
   - Experience level
   - Top 5 skills required
   - Number of proposals
   - URL link

4. **Offer next steps**: Ask if they want to:
   - See full details on a specific job
   - Analyze what skills these jobs demand
   - Get portfolio project suggestions based on these jobs
