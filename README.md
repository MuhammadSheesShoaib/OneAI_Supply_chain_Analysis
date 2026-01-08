# Supply Chain Disruption Predictor

AI-powered supply chain risk prediction and mitigation system with a modern web dashboard.

## Prerequisites

- **Python 3.10+** and **pip**
- **Node.js 18+** and **npm**

## Setup

### Backend Setup

1. Navigate to backend directory:
```bash
cd supply_chain_predictor
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Create `.env` file for Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

5. Verify data files exist in `../data/` directory:
- `supplier_lead_time.csv`
- `manufacturing_production.csv`
- `inventory_levels.csv`
- `customer_demand.csv`
- `transportation_data.csv`
- `external_factors.csv`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

Use **two separate terminal windows**:

### Terminal 1 - Backend:
```bash
cd supply_chain_predictor
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # macOS/Linux
python main.py
```

Backend will be available at: **http://localhost:8000**

### Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Frontend will be available at: **http://localhost:3000**

The frontend automatically connects to the backend through the configured proxy.

## Troubleshooting

**Port already in use:**
- Backend (port 8000): Kill the process using the port or change the port in `main.py`
- Frontend (port 3000): Vite will automatically use the next available port

**Module not found:**
- Make sure virtual environment is activated
- Reinstall: `pip install -r requirements.txt`

**Cannot connect to backend:**
- Verify backend is running on http://localhost:8000
- Check that both terminals are running
