"""
FastAPI application entry point for Supply Chain Disruption Predictor.
"""
import logging
import sys
import json
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import API_CONFIG, LOGGING_CONFIG
from schemas.models import (
    AnalysisRequest,
    AnalysisResponse,
    HealthResponse,
    ErrorResponse,
    EntityInfo,
    SupplierInfo,
    PlantInfo,
    WarehouseInfo,
    RouteInfo,
)
from services.forecast_service import ForecastService
from utils.helpers import format_timestamp

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG.get("level", "INFO")),
    format=LOGGING_CONFIG.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger = logging.getLogger(__name__)

# Global service instance
forecast_service: Optional[ForecastService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global forecast_service
    
    # Startup
    logger.info("Starting Supply Chain Predictor API...")
    forecast_service = ForecastService()
    logger.info("ForecastService initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Supply Chain Predictor API...")


# Create FastAPI app
app = FastAPI(
    title=API_CONFIG.get("title", "Supply Chain Disruption Predictor API"),
    description=API_CONFIG.get("description", "AI-powered supply chain risk prediction and mitigation system"),
    version=API_CONFIG.get("version", "1.0.0"),
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG.get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= Exception Handlers =============

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Validation Error", "message": str(exc), "details": None}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "message": str(exc), "details": None}
    )


# ============= API Endpoints =============

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": API_CONFIG.get("title"),
        "version": API_CONFIG.get("version"),
        "description": API_CONFIG.get("description"),
        "endpoints": {
            "analyze": "/api/analyze",
            "health": "/api/health",
            "entities": "/api/entities",
            "analysis": "/api/analysis/{analysis_id}"
        }
    }


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Check the health status of the API and data availability.
    
    Returns:
        HealthResponse with service status and data availability
    """
    global forecast_service
    
    if forecast_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    
    health = forecast_service.check_health()
    
    return HealthResponse(
        status="healthy" if health["all_data_available"] else "degraded",
        timestamp=format_timestamp(),
        version=API_CONFIG.get("version", "1.0.0"),
        data_status=health["data_status"]
    )


@app.post(
    "/api/analyze",
    tags=["Analysis"],
    summary="Run supply chain analysis",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid request parameters", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse}
    }
)
async def analyze(request: AnalysisRequest):
    """
    Run comprehensive supply chain disruption analysis.
    
    This endpoint:
    1. Runs Prophet forecasts for specified modules
    2. Identifies and scores risks based on forecast results
    3. Generates LLM-powered mitigation recommendations (if enabled)
    4. Returns a complete analysis report
    
    Args:
        request: AnalysisRequest with forecast parameters
        
    Returns:
        Complete analysis response with forecasts, risks, and recommendations
    """
    global forecast_service
    
    if forecast_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    
    try:
        logger.info(f"Starting analysis with horizon={request.forecast_horizon}, modules={request.modules}")
        
        # Convert module enums to strings if needed
        modules = [m.value if hasattr(m, 'value') else m for m in request.modules]
        
        result = forecast_service.run_full_analysis(
            forecast_horizon=request.forecast_horizon,
            modules=modules,
            risk_threshold=request.risk_threshold,
            include_mitigations=request.include_mitigations
        )
        
        logger.info(f"Analysis completed: {result['summary']['total_risks']} risks identified")
        
        # Ensure all datetime objects and numpy types are serialized properly
        def serialize_for_json(obj):
            """Convert non-serializable objects to JSON-compatible types."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, (np.integer, np.int64, np.int32, np.int8, np.int16)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
                return float(obj)
            elif isinstance(obj, (np.bool_, bool)):
                # Handle both numpy bool_ and Python bool
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: serialize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_for_json(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(serialize_for_json(item) for item in obj)
            elif pd.isna(obj):
                return None
            # Handle any other numpy scalar types
            elif hasattr(obj, 'item'):  # numpy scalars have .item() method
                return obj.item()
            return obj
        
        # Serialize the result
        serialized_result = serialize_for_json(result)
        
        # Validate it can be JSON serialized
        try:
            json.dumps(serialized_result)
        except (TypeError, ValueError) as json_err:
            logger.error(f"JSON serialization error: {json_err}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Response serialization failed: {str(json_err)}"
            )
        
        return serialized_result
        
    except ValueError as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get(
    "/api/entities",
    response_model=EntityInfo,
    tags=["Entities"],
    summary="Get available entities"
)
async def get_entities():
    """
    Get all available entities from the data.
    
    Returns:
        EntityInfo with lists of suppliers, plants, warehouses, routes, SKUs, and regions
    """
    global forecast_service
    
    if forecast_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    
    try:
        entities = forecast_service.get_entities()
        
        return EntityInfo(
            suppliers=[SupplierInfo(**s) for s in entities.get("suppliers", [])],
            plants=[PlantInfo(**p) for p in entities.get("plants", [])],
            warehouses=[WarehouseInfo(**w) for w in entities.get("warehouses", [])],
            routes=[RouteInfo(**r) for r in entities.get("routes", [])],
            skus=entities.get("skus", []),
            regions=entities.get("regions", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to get entities: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve entities: {str(e)}"
        )


@app.get(
    "/api/analysis/{analysis_id}",
    response_model=dict,
    tags=["Analysis"],
    summary="Retrieve cached analysis results"
)
async def get_analysis(analysis_id: str):
    """
    Retrieve a previously computed analysis by ID.
    
    Args:
        analysis_id: The unique analysis identifier
        
    Returns:
        The cached analysis result
        
    Raises:
        404: If analysis not found
    """
    global forecast_service
    
    if forecast_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    
    result = forecast_service.get_cached_analysis(analysis_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found"
        )
    
    return result


# ============= Additional Endpoints =============

@app.get(
    "/api/modules",
    tags=["Metadata"],
    summary="Get available forecast modules"
)
async def get_modules():
    """Get list of available forecast modules."""
    return {
        "modules": [
            {
                "id": "suppliers",
                "name": "Supplier Lead Times",
                "description": "Forecast supplier delivery lead times"
            },
            {
                "id": "manufacturing",
                "name": "Manufacturing Production",
                "description": "Forecast production capacity and downtime"
            },
            {
                "id": "inventory",
                "name": "Inventory Levels",
                "description": "Forecast warehouse stock levels"
            },
            {
                "id": "demand",
                "name": "Customer Demand",
                "description": "Forecast customer order volumes"
            },
            {
                "id": "transportation",
                "name": "Transportation",
                "description": "Forecast transit times and delivery performance"
            },
            {
                "id": "external",
                "name": "External Factors",
                "description": "Forecast weather, tariffs, and other external factors"
            }
        ]
    }


@app.get(
    "/api/risk-categories",
    tags=["Metadata"],
    summary="Get risk categories"
)
async def get_risk_categories():
    """Get list of risk categories and their descriptions."""
    return {
        "categories": [
            {
                "id": "supplier_delays",
                "name": "Supplier Delays",
                "description": "Risks related to supplier lead time increases",
                "impact_types": ["Production Delays", "Stockouts"]
            },
            {
                "id": "production_delays",
                "name": "Production Delays",
                "description": "Risks related to manufacturing capacity and downtime",
                "impact_types": ["Reduced Output", "Delivery Delays"]
            },
            {
                "id": "stock_shortages",
                "name": "Stock Shortages",
                "description": "Risks related to inventory levels below safety stock",
                "impact_types": ["Stockouts", "Lost Sales"]
            },
            {
                "id": "demand_volatility",
                "name": "Demand Volatility",
                "description": "Risks related to high demand uncertainty",
                "impact_types": ["Planning Difficulty", "Overstock/Understock"]
            },
            {
                "id": "transportation_issues",
                "name": "Transportation Issues",
                "description": "Risks related to transit delays and carrier issues",
                "impact_types": ["Delivery Delays", "Cost Increases"]
            },
            {
                "id": "external_factors",
                "name": "External Factors",
                "description": "Risks from weather, tariffs, and other external events",
                "impact_types": ["Supply Chain Disruption", "Cost Increases"]
            }
        ]
    }


# ============= Entry Point =============

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

