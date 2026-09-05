# DealPilot

AI-assisted product deal finder — hackathon demo. Parses a natural-language product
request, searches four mock retailer providers (Nike, Amazon, Walmart, eBay), matches
equivalent listings across retailers, and ranks them by total delivered price.

Runs fully locally, no auth, no cloud dependency. **DEMO MODE is on by default** (see
below) so it never depends on a network call, an AI provider, or live retailer data —
Azure OpenAI / an OpenAI-compatible endpoint is an optional enhancement (better NL
parsing, ambiguous-match resolution, explanation polish) that only activates if you
explicitly turn DEMO MODE off and configure it.

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

> Note: if PowerShell's execution policy blocks `.venv\Scripts\Activate.ps1`, skip
> activation entirely and call `.venv\Scripts\python.exe` directly as shown above.

Health check: http://localhost:8000/api/health

Optional: copy `.env.example` to `.env` and fill in Azure OpenAI settings to enable AI features.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

> Note: if plain `npm` is blocked by PowerShell's execution policy (unsigned `.ps1`
> script), use `npm.cmd` instead for both commands above.

Dev server: http://localhost:5173

## Running the full demo

Start the backend and frontend (each in its own terminal) using the commands above,
then open http://localhost:5173 and try one of the example queries, e.g.:

> Find Nike Pegasus 41 men's size 10 black under $120

## DEMO MODE

`DEMO_MODE` (in `backend/.env`, default `true`) forces every search to run fully
deterministically: no AI client is ever constructed, no matter what Azure/OpenAI
settings happen to be present in the environment. Every request still goes through the
real pipeline — intent parsing, provider selection, the four mock providers, product
matching, and ranking — it just never calls out to an external AI provider while it's
on. Combined with the mock provider data (`backend/app/data/`), this means the demo
can never fail because of a retailer API, network problem, rate limit, or changing
inventory. Set `DEMO_MODE=false` (and configure Azure/OpenAI settings) to exercise AI
MODE instead.

Three fixed queries are used as the demo script and are covered by
`backend/tests/test_search_endpoint.py`:

1. **`Find Nike Pegasus 41 men's size 10 black under $120`** — a fully-specified query;
   demonstrates exact-SKU matching across all four retailers into a single group.
2. **`Find Nike Air Max 270 men's size 10`** — no color/price given; demonstrates that a
   deliberately similar product ("Air Max 270 React") is correctly excluded, and that an
   out-of-stock listing (Walmart) is still shown but never picked as the best deal.
3. **`Find the cheapest Nike running shoe under $100`** — no specific model; demonstrates
   ranking picking the single cheapest listing across multiple distinct Nike running-shoe
   products (only the Pegasus 40 line qualifies under $100).

