# DealPilot

**DealPilot** is an AI-powered shopping intelligence engine for hackathons and live demos. It accepts natural-language product requests, queries multiple retailer mock APIs (Nike, Amazon, Walmart, eBay), normalizes product listings, matches equivalent items across stores, and ranks deals by true total delivered price (item price + shipping).

---

## Key Features

- 🧠 **Natural Language Product Understanding** — Extracts brand, model, gender, size, color, max price, and category.
- 🏬 **Smart Store Selection** — Intelligently selects and prioritizes relevant retailers (e.g. prioritizing Nike's official store for Nike queries).
- 🔗 **Robust Cross-Store Product Matching** — Normalizes manufacturer SKUs and calculates weighted feature similarity to group identical products.
- 💰 **True Cost Deal Ranking** — Calculates total delivered cost (price + shipping) and ranks cheapest item, cheapest delivered, official store, and best overall deal.
- 💡 **Transparent Explanations** — Explains *why* the deal was recommended with verifiable facts.
- ⚡ **100% Reliable DEMO MODE** — Default offline mode runs fully deterministically with zero risk of external API outages, rate limits, or network lag.
- 🤖 **Optional AI MODE** — Compatible with Azure OpenAI or any OpenAI-compatible endpoint (OpenAI, Azure AI Foundry, Ollama, vLLM).

---

## Prerequisites

Before starting, ensure you have the following installed on your machine:

- **Python**: `3.10` or higher (`3.12` recommended)
- **Node.js**: `18.0` or higher (with `npm`)
- **Git**
- **VS Code** (recommended, with **GitHub Copilot** extension)

> **Docker is NOT required.** Everything runs locally in native Python virtualenv and Node environments.

---

## Quick Start (One-Click Setup & Launch)

### Windows (CMD or PowerShell)

1. **One-Click Setup** (run once to create `.venv`, install packages, and set up `.env`):
   ```cmd
   .\setup.cmd
   ```

2. **One-Click Launch** (starts backend on `:8000` and frontend on `:5173` in separate windows):
   ```cmd
   .\start.cmd
   ```

### macOS / Linux / WSL

1. **One-Click Setup**:
   ```bash
   chmod +x setup.sh start.sh
   ./setup.sh
   ```

2. **One-Click Launch**:
   ```bash
   ./start.sh
   ```

---

## Manual Step-by-Step Setup

If you prefer to run commands manually:

### 1. Backend Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

*(On macOS/Linux, replace `.venv\Scripts\` with `.venv/bin/`)*

### 2. Frontend Setup

```powershell
cd frontend
npm.cmd install
```

*(On macOS/Linux, use plain `npm install`)*

---

## Environment & DEMO MODE Setup

The backend configuration is managed via `backend/.env` (created automatically from `backend/.env.example` during setup).

### DEMO MODE (Default: `DEMO_MODE=true`)

By default, **`DEMO_MODE=true`** is enabled. In DEMO MODE:
- DealPilot operates **100% deterministically** using local regex parsing, catalog matching, and rule-based ranking.
- No external AI API calls are made.
- Search requests are instant and guaranteed to succeed offline without network dependency, rate limits, or API key management.

### AI MODE (Optional: `DEMO_MODE=false`)

To enable live AI features (enhanced natural-language parsing fallback, ambiguous match tie-breaking, and AI-polished explanations):

1. Set `DEMO_MODE=false` in `backend/.env`.
2. Configure your Azure OpenAI or OpenAI-compatible credentials:

```ini
DEMO_MODE=false

# Option A: Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Option B: Any OpenAI-compatible endpoint (OpenAI, Local AI Foundry, Ollama)
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o

AI_TIMEOUT_SECONDS=5
```

> **Safety Guarantee**: If an AI request fails, times out, or returns invalid JSON, DealPilot automatically and silently falls back to deterministic rules. The application will never crash due to an AI service interruption.

---

## Running Backend & Frontend Individually

### Starting the Backend

From the repository root:

```powershell
# Windows
.\start-backend.cmd

# Or manually:
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

- **API Root**: [http://localhost:8000](http://localhost:8000)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Starting the Frontend

From the repository root:

```powershell
# Windows
.\start-frontend.cmd

# Or manually:
cd frontend
npm.cmd run dev
```

- **Web App**: [http://localhost:5173](http://localhost:5173)

---

## Running in VS Code (with GitHub Copilot)

DealPilot includes pre-configured `.vscode/` settings and tasks for a smooth VS Code development experience.

### VS Code Build & Launch Tasks

1. Open the project folder in VS Code (`code .`).
2. Press `Ctrl+Shift+B` (or `Cmd+Shift+B` on macOS) or run `Terminal -> Run Build Task...`.
3. Select **`Start Full Stack (DealPilot)`**.
4. VS Code will launch both the FastAPI backend and Vite frontend in parallel terminal tabs.

### Available Tasks (`Ctrl+Shift+P` -> `Tasks: Run Task`):
- **`Start Full Stack (DealPilot)`**: Starts both backend and frontend.
- **`Start Backend`**: Launches the FastAPI uvicorn server.
- **`Start Frontend`**: Launches the Vite React dev server.
- **`Run Backend Tests`**: Executes `pytest` test suite.
- **`Run Frontend Build & Lint`**: Runs ESLint and Vite TypeScript build.

---

## Sample Search Queries for Demos

Use these test queries during live demonstrations or video recordings:

### Query 1: Exact Product Search
> `"Find Nike Pegasus 41 men's size 10 black under $120"`
- **Demonstrates**: Exact SKU normalization (`DV3853-001`), multi-retailer search across all 4 stores (Nike, Amazon, Walmart, eBay), and identifying Walmart as the cheapest delivered deal ($106.40).

### Query 2: Product Variant Separation & Stock Handling
> `"Find Nike Air Max 270 men's size 10"`
- **Demonstrates**: Disambiguation (properly separates "Air Max 270" from the similar "Air Max 270 React"), handling out-of-stock listings (Walmart is out of stock so eBay/Nike/Amazon win).

### Query 3: Category-Level Best Deal Search
> `"Find the cheapest Nike running shoe under $100"`
- **Demonstrates**: Cross-product category ranking — searches all Nike running shoes under $100 (filters out Pegasus 41 at $112+, identifies Pegasus 40 at $86.98 on eBay as the overall winner).

---

## Running Tests

DealPilot includes comprehensive test suites for both backend and frontend.

### Backend Tests (138 Pytest unit & integration tests)

```powershell
cd backend
.venv\Scripts\python.exe -m pytest
```

Coverage includes:
- Product model validation (`test_models.py`)
- Regex and AI natural-language parser (`test_parser.py`)
- Deterministic store selector (`test_provider_selector.py`)
- Retailer provider inventory filtering (`test_providers.py`, `test_catalog_data.py`)
- Feature-weighted matcher & tie-breaker (`test_matcher.py`)
- Total-cost deal ranking (`test_ranking.py`)
- Natural-language explainer (`test_explainer.py`)
- FastAPI endpoints & error handling (`test_search_endpoint.py`, `test_health.py`)
- AI client abstraction & fallback (`test_ai_client.py`)

### Frontend Type-Checking & Linting

```powershell
cd frontend
npm.cmd run lint
npm.cmd run build
```

---

## Troubleshooting & Common Gotchas

### 1. Windows PowerShell Execution Policy Error
**Symptom**: Running `.ps1` scripts or `npm` fails with `PSSecurityException` or `UnauthorizedAccess`.  
**Fix**: Use the provided `.cmd` wrapper scripts (`.\setup.cmd`, `.\start.cmd`, `.\start-backend.cmd`, `.\start-frontend.cmd`), or call `npm.cmd` and `.venv\Scripts\python.exe` directly.

### 2. Frontend Cannot Connect to Backend
**Symptom**: Search displays an error: *"Something went wrong reaching DealPilot. Is the backend running on port 8000?"*  
**Fix**: Ensure the FastAPI server is running on `http://localhost:8000`. Test `http://localhost:8000/api/health` in your browser.

### 3. Port Conflicts (`8000` or `5173` in use)
**Symptom**: Uvicorn or Vite fails to start due to port in use.  
**Fix**: Kill existing process using port `8000` or `5173`:
```powershell
# Find and stop process on port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### 4. Re-initializing Python Virtual Environment
If your `.venv` gets corrupted:
```powershell
cd backend
Remove-Item -Recurse -Force .venv
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## Repository Structure

```
dealpilot/
├── README.md                  # Project overview & documentation
├── setup.cmd / setup.sh       # One-click setup scripts (Windows / Unix)
├── start.cmd / start.sh       # One-click launch scripts (Windows / Unix)
├── start-backend.cmd          # Backend launcher
├── start-frontend.cmd         # Frontend launcher
├── .vscode/                   # VS Code tasks & workspace settings
│   ├── settings.json
│   └── tasks.json
├── backend/
│   ├── .env.example           # Environment template
│   ├── requirements.txt       # Python dependencies
│   ├── app/
│   │   ├── main.py            # FastAPI entry point & CORS configuration
│   │   ├── config.py          # App settings & DEMO_MODE toggle
│   │   ├── data/              # Mock catalog & retailer inventory JSON
│   │   ├── models/            # Pydantic data models
│   │   ├── routers/           # API router endpoints
│   │   └── services/          # Parser, selector, matcher, ranking, explainer, AI client
│   └── tests/                 # 138 Pytest test cases
└── frontend/
    ├── package.json           # React & Vite dependencies
    ├── vite.config.ts         # Vite configuration
    └── src/
        ├── App.tsx            # Main React component
        ├── api/client.ts      # API fetch client
        ├── components/        # Modern UI components
        ├── pages/Home.tsx     # Home page layout
        ├── types/             # TypeScript interfaces
        └── utils/             # Listing helpers & formatting
```


