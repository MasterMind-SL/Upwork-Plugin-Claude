---
name: analyze
description: Analyze Upwork job market requirements from cached data. Use when the user wants to understand skill demand, market trends, budget ranges, or asks "what skills are in demand", "market analysis", "what should I learn".
---

# Analyze Upwork Job Market

Analyze cached job data to identify market trends and requirements.

## Steps

1. **Check data**: Call `tool_get_scraping_stats` to see if there's enough cached data.
   - If total_jobs < 5: suggest fetching more jobs first with best-matches or search.

2. **Analyze**: Call `tool_analyze_market_requirements(skill_focus="$ARGUMENTS", top_n=20)`.

3. **Present insights** clearly:

   ### Skills in Demand
   Show top 10 skills as a ranked list with percentages.

   ### Budget Landscape
   Show budget distribution and averages.

   ### Experience Levels
   Show the breakdown (entry vs intermediate vs expert).

   ### Key Takeaways
   - What skills appear most frequently together?
   - What's the sweet spot for budget/rates?
   - What experience level has the most opportunities?

4. **Actionable advice**: Based on the analysis, suggest:
   - Skills the user should highlight
   - Skills to learn to increase competitiveness
   - Optimal rate/budget positioning
