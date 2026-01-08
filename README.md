# Supply Chain Disruption Predictor

AI-powered supply chain risk prediction and mitigation system with a modern web dashboard.

## Project Structure

```
OneAI/
├── frontend/              # React + TypeScript frontend (Vite)
├── supply_chain_predictor/  # Python FastAPI backend
└── data/                 # CSV data files for analysis
```

## Prerequisites

### Backend Requirements
- **Python 3.10+** (recommended: Python 3.10 or 3.11)
- **pip** (Python package manager)

### Frontend Requirements
- **Node.js 18+** (recommended: Node.js 18 or 20)
- **npm** (comes with Node.js)

## Quick Start

### 1. Backend Setup

#### Step 1: Navigate to backend directory
```bash
cd supply_chain_predictor
```

#### Step 2: Create a virtual environment (recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Python dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Set up environment variables (optional)
Create a `.env` file in the `supply_chain_predictor` directory if you want to use Groq API for LLM-powered mitigations:

```env
GROQ_API_KEY=your_groq_api_key_here
```

**Note:** The application will work without the Groq API key, but mitigation recommendations will be limited.

#### Step 5: Verify data files are available
Make sure the following CSV files exist in the `../data/` directory (relative to `supply_chain_predictor`):
- `supplier_lead_time.csv`
- `manufacturing_production.csv`
- `inventory_levels.csv`
- `customer_demand.csv`
- `transportation_data.csv`
- `external_factors.csv`

#### Step 6: Start the backend server
```bash
# Option 1: Using Python directly
python main.py

# Option 2: Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at: **http://localhost:8000**

You can verify it's running by visiting:
- API root: http://localhost:8000/
- Health check: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs (Swagger UI)

---

### 2. Frontend Setup

#### Step 1: Navigate to frontend directory
Open a **new terminal window** (keep the backend running) and navigate to:
```bash
cd frontend
```

#### Step 2: Install Node.js dependencies
```bash
npm install
```

#### Step 3: Start the development server
```bash
npm run dev
```

The frontend will be available at: **http://localhost:3000**

The Vite dev server is configured to proxy API requests from `/api` to `http://localhost:8000`, so the frontend will automatically connect to the backend.

---

## Running Both Services

### Option 1: Two Terminal Windows (Recommended)

**Terminal 1 - Backend:**
```bash
cd supply_chain_predictor
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # macOS/Linux
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Using a Process Manager

You can use tools like `concurrently` or `npm-run-all` to run both services with a single command. Add this to your root `package.json`:

```json
{
  "scripts": {
    "dev:backend": "cd supply_chain_predictor && python main.py",
    "dev:frontend": "cd frontend && npm run dev",
    "dev": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\""
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
```

Then run:
```bash
npm install concurrently
npm run dev
```

---

## API Endpoints

The backend provides the following main endpoints:

- `GET /` - API information
- `GET /api/health` - Health check
- `GET /api/modules` - Available forecast modules
- `GET /api/entities` - Available entities (suppliers, plants, warehouses, etc.)
- `POST /api/analyze` - Run supply chain analysis
- `GET /api/analysis/{analysis_id}` - Retrieve cached analysis

Full API documentation is available at: http://localhost:8000/docs

---

## Troubleshooting

### Backend Issues

**Problem: Port 8000 is already in use**
```bash
# Find and kill the process using port 8000
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# On macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

**Problem: Module not found errors**
- Make sure you're in the virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

**Problem: Data file not found**
- Verify CSV files exist in the `data/` directory (one level up from `supply_chain_predictor`)
- Check the file paths in `supply_chain_predictor/config.py`

**Problem: Prophet installation issues**
- Prophet requires a C++ compiler. On Windows, install Visual Studio Build Tools
- Alternative: Use conda instead of pip: `conda install -c conda-forge prophet`

### Frontend Issues

**Problem: Port 3000 is already in use**
- Vite will automatically try the next available port (3001, 3002, etc.)
- Or change the port in `frontend/vite.config.ts`

**Problem: Cannot connect to backend API**
- Verify the backend is running on http://localhost:8000
- Check the proxy configuration in `frontend/vite.config.ts`
- Make sure CORS is enabled in the backend (it should be by default)

**Problem: npm install fails**
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules` and `package-lock.json`, then reinstall
- Make sure you're using Node.js 18+

### General Issues

**Problem: Changes not reflecting**
- Backend: Restart the server (Ctrl+C and run again)
- Frontend: Vite has hot-reload, but if issues persist, restart the dev server

**Problem: CORS errors in browser**
- The backend is configured to allow all origins (`*`) by default
- If you still see CORS errors, check `supply_chain_predictor/main.py` CORS configuration

---

## Development Notes

### Backend
- Uses **FastAPI** for the REST API
- Uses **Prophet** for time series forecasting
- Uses **Groq API** (optional) for LLM-powered mitigation recommendations
- Data files are expected in the `data/` directory at the project root

### Frontend
- Built with **React 18** + **TypeScript**
- Uses **Vite** as the build tool
- Uses **Radix UI** components
- Uses **Recharts** for data visualization
- API calls are proxied through Vite dev server to avoid CORS issues

### Data Files
The application requires CSV files with specific formats. Make sure your data files have the correct columns as expected by the data loader service.

---

## Production Build

### Build Frontend
```bash
cd frontend
npm run build
```

The built files will be in `frontend/build/`

### Run Backend in Production
```bash
cd supply_chain_predictor
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

For production, consider:
- Using a reverse proxy (nginx, Caddy)
- Setting up proper CORS origins
- Using environment variables for configuration
- Setting up proper logging
- Using a process manager (PM2, supervisor)

---

## License

[Add your license information here]

## Support

For issues and questions, please [create an issue in the repository](link-to-your-repo).

