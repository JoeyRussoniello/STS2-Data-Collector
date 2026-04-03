You are building a minimal Flask web application frontend for the STS2 community stats project.

Goal:
Design and implement the full Flask app structure for a dashboard website that uses an existing stats API. The app should feel polished but minimal, and should be designed like a modern video-game stats dashboard in the style of tracker.gg, op.gg, u.gg, or similar game stat-tracking sites. Clean cards, strong information hierarchy, dark-mode friendly, game-adjacent visual design, but not overbuilt.

Similar reference websites:

- STS 1: <https://public.tableau.com/app/profile/terrence.miller/viz/TerrenceMiller-STS-DataSchool/DataSchoolApp> (for how to display ideas, and future direction)
- UI Style (Can change color pallete): <http://dribbble.com/shots/21198290-ValNFT-NFT-Dashboard-Concept>

Important constraints:

- Do not redesign the backend API unless absolutely necessary.
  - Refer to **<https://sts2-data-collector-production.up.railway.app/docs#/public>** on how to access data, particularly through /api/stats
- The task is primarily frontend/app-structure oriented.
- Use Flask for the web app.
- Use uv for dependency management, not raw .venv and requirements.txt
- No need for auth.
- No need for heavy JS frameworks unless truly necessary.
- Optimize for a simple, maintainable server-rendered Flask app with light client-side enhancement if useful.
- Prefer requests to raw urllib for codebase simplicity
- The result should work locally first.

Project context:
This project is for a Slay the Spire 2 community database. A separate collector uploads completed runs to a shared backend. The website should let users:

1. view overall community/global database stats
2. enter their Steam ID
3. visit a shareable player page immediately via URL

Core routes:

- `/dashboard`
- `/dashboard/<steam_id>`

Required route behavior:

1. `/dashboard`
   - This is the public global dashboard for the entire database.
   - It should show overall/global stats using the existing stats API.
   - It should also contain a minimal UI to enter a Steam ID.
   - Submitting the Steam ID should redirect to `/dashboard/<steam_id>`.

2. `/dashboard/<steam_id>`
   - This is the player-specific dashboard page.
   - It should show stats for an individual player.
   - It must be directly shareable so a user can click a link and land immediately on their own stats page.

Design direction:

- Visual inspiration can be similar to tracker.gg, op.gg, u.gg, or other well-known video game stats dashboards.
- Prioritize:
  - dark theme or dark-theme-ready design
  - compact but readable stat cards
  - clean sections
  - minimal clutter
  - obvious hierarchy
  - strong dashboard feel
- Avoid excessive ornamentation.
- Keep it modern, polished, and game-centric.
- Responsive enough for desktop and mobile.

MVP content requirements:

For `/dashboard` (global dashboard):

- Header/title for the site/dashboard
- Short explanation of what the data is
- Steam ID input field and submit button near the top
- Summary cards for the entire database, such as:
  - total runs
  - total players
  - overall win rate
  - total wins / losses
  - most played character
  - latest upload date if available
- Character win rates section
- Top cards section
- Recent trends section (daily trends or similar)
- Good empty/error/loading states

For `/dashboard/<steam_id>` (player dashboard):

- Player header with Steam ID context
- Summary cards such as:
  - total runs
  - wins
  - losses
  - win rate
  - most played character
  - highest ascension
- Character breakdown section
- Recent runs section
- Top cards section
- Trends section
- Clear empty state if this Steam ID has no data
- Clear error state if lookup fails

Technical implementation expectations:

- Build the Flask app structure cleanly.
- Create reusable templates/components/partials where sensible.
- Use Jinja templates for rendering.
- Organize CSS cleanly and professionally.
- Keep the code easy to extend.
- If the API does not perfectly match the frontend needs, isolate API-calling logic cleanly so it can be changed later.
- Prefer a maintainable architecture over hacks.

What to produce:

- A complete frontend-oriented Flask app structure
- Templates for both dashboard routes
- Styling that gives a modern game-stats-dashboard feel
- Helper/API service layer for calling the existing stats API
- Routing logic
- Error handling and empty states
- A minimal but polished local-first experience

API usage expectations:

- Use the existing stats API wherever possible for global dashboard data.
- For player dashboard data, use existing player-scoped endpoints if they exist.
- If player-scoped endpoints do not exist, structure the frontend so the data-fetching layer clearly shows what endpoints are assumed/needed.
- Do not overcomplicate the solution.

Product intent:

- `/dashboard` should answer: “What does the community dataset look like right now?”
- `/dashboard/<steam_id>` should answer: “What do my runs/stats look like?”
- The player page should be good enough that a client/README link can send someone there directly and it feels immediately useful.

Implementation priorities:

1. Build `/dashboard` global community dashboard
2. Add Steam ID input and redirect behavior
3. Build `/dashboard/<steam_id>` player dashboard
4. Add polished card-based layout and styling
5. Add empty/error/loading states
6. Make templates reusable and clean
7. Make the app easy to extend later

Coding style:

- Be practical and opinionated.
- Choose good defaults instead of asking unnecessary questions.
- Keep the UI minimal but high quality.
- Favor clarity, maintainability, and tasteful dashboard design.

When implementing:

- First inspect the current API surface and map the routes to available endpoints.
- Then create the Flask app structure.
- Then build the templates and styling.
- Then wire data into the views.
- Then improve UX states and polish.

Deliver something that already feels like a real stats site, even if it is still MVP-sized.
