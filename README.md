# DealPilot

AI-assisted product deal finder — hackathon demo. Parses a natural-language product
request, searches four mock retailer providers (Nike, Amazon, Walmart, eBay), matches
equivalent listings across retailers, and ranks them by total delivered price.

Runs fully locally, no auth, no cloud dependency. Azure OpenAI is an optional
enhancement (better NL parsing, ambiguous-match resolution, explanation polish) — the
app works completely without it.

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

