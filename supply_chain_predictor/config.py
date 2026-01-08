"""
Configuration module for Supply Chain Predictor.
Contains API keys, thresholds, and other configurable parameters.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data"

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_TEMPERATURE = 0.7
GROQ_MAX_TOKENS = 2000
GROQ_MAX_RETRIES = 3

# Prophet Configuration
PROPHET_CONFIG = {
    "yearly_seasonality": True,
    "weekly_seasonality": True,
    "daily_seasonality": False,
    "seasonality_mode": "multiplicative",
    "changepoint_prior_scale": 0.05,
    "interval_width": 0.95,
}

# Risk Thresholds
RISK_THRESHOLDS = {
    # Supplier Risk Thresholds
    "supplier_lead_time_multiplier": 1.2,  # Lead time > historical_avg * 1.2 = risk
    
    # Production Risk Thresholds
    "capacity_utilization_threshold": 0.95,  # Capacity > 95% = bottleneck risk
    "downtime_increase_threshold": 0.2,  # 20% increase in downtime = risk
    
    # Inventory Risk Thresholds
    "safety_stock_threshold": 1.0,  # Inventory below safety stock = shortage risk
    
    # Demand Volatility Thresholds
    "demand_volatility_threshold": 0.3,  # (upper - lower) / yhat > 30% = volatility risk
    
    # Transportation Risk Thresholds
    "transit_time_multiplier": 1.3,  # Transit time > baseline * 1.3 = delay risk
    
    # External Factor Thresholds
    "weather_severity_threshold": 7,  # Weather severity > 7 = weather risk
    "tariff_increase_threshold": 0.1,  # Tariff increase > 10% = trade risk
    "port_congestion_threshold": 30,  # Port congestion index > 30 = congestion risk
}

# Risk Score Classification
RISK_PRIORITY_THRESHOLDS = {
    "CRITICAL": 90,
    "HIGH": 70,
    "MEDIUM": 50,
    "LOW": 0,
}

# Forecast Configuration
FORECAST_CONFIG = {
    "min_horizon_days": 30,
    "max_horizon_days": 60,
    "default_horizon_days": 45,
    "min_data_points": 30,  # Minimum data points required for Prophet
}

# Data File Paths
DATA_FILES = {
    "supplier_lead_times": DATA_DIR / "supplier_lead_time.csv",  # Fixed: was supplier_lead_time_data.csv
    "manufacturing_production": DATA_DIR / "manufacturing_production.csv",
    "inventory_levels": DATA_DIR / "inventory_levels.csv",
    "customer_demand": DATA_DIR / "customer_demand.csv",
    "transportation_data": DATA_DIR / "transportation_data.csv",
    "external_factors": DATA_DIR / "external_factors.csv",
}

# API Configuration
API_CONFIG = {
    "title": "Supply Chain Disruption Predictor API",
    "description": "AI-powered supply chain risk prediction and mitigation system",
    "version": "1.0.0",
    "cors_origins": ["*"],
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

