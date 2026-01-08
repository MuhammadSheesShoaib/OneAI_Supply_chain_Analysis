"""
Pydantic models for API request/response validation.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ModuleType(str, Enum):
    """Available forecast modules."""
    SUPPLIERS = "suppliers"
    MANUFACTURING = "manufacturing"
    INVENTORY = "inventory"
    DEMAND = "demand"
    TRANSPORTATION = "transportation"
    EXTERNAL = "external"


class RiskPriority(str, Enum):
    """Risk priority levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskCategory(str, Enum):
    """Risk categories."""
    SUPPLIER_DELAYS = "Supplier Delays"
    PRODUCTION_DELAYS = "Production Delays"
    STOCK_SHORTAGES = "Stock Shortages"
    DEMAND_VOLATILITY = "Demand Volatility"
    TRANSPORTATION_ISSUES = "Transportation Issues"
    EXTERNAL_FACTORS = "External Factors"


# ============= Request Models =============

class AnalysisRequest(BaseModel):
    """Request model for supply chain analysis."""
    forecast_horizon: int = Field(
        default=45,
        ge=30,
        le=60,
        description="Forecast horizon in days (30-60)"
    )
    modules: List[ModuleType] = Field(
        default=[
            ModuleType.SUPPLIERS,
            ModuleType.MANUFACTURING,
            ModuleType.INVENTORY,
            ModuleType.DEMAND,
            ModuleType.TRANSPORTATION,
            ModuleType.EXTERNAL,
        ],
        description="Modules to analyze"
    )
    risk_threshold: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Minimum risk score to include in results"
    )
    include_mitigations: bool = Field(
        default=True,
        description="Whether to include LLM-generated mitigation strategies"
    )

    class Config:
        use_enum_values = True


# ============= Forecast Models =============

class ForecastDataPoint(BaseModel):
    """Single forecast data point."""
    ds: datetime = Field(description="Forecast date")
    yhat: float = Field(description="Predicted value")
    yhat_lower: float = Field(description="Lower bound of prediction")
    yhat_upper: float = Field(description="Upper bound of prediction")
    trend: Optional[float] = Field(default=None, description="Trend component")


class ForecastResult(BaseModel):
    """Forecast result for a specific entity."""
    entity_id: str = Field(description="Entity identifier")
    entity_name: Optional[str] = Field(default=None, description="Entity name")
    metric: str = Field(description="Metric being forecasted")
    historical_avg: float = Field(description="Historical average value")
    forecasted_avg: float = Field(description="Forecasted average value")
    forecast_data: List[ForecastDataPoint] = Field(description="Forecast data points")
    change_percentage: float = Field(description="Percentage change from historical")


class ModuleForecast(BaseModel):
    """Forecast results for a module."""
    module: str = Field(description="Module name")
    forecasts: List[ForecastResult] = Field(description="List of forecasts")


# ============= Risk Models =============

class AffectedEntities(BaseModel):
    """Entities affected by a risk."""
    suppliers: List[str] = Field(default_factory=list)
    plants: List[str] = Field(default_factory=list)
    warehouses: List[str] = Field(default_factory=list)
    skus: List[str] = Field(default_factory=list)
    routes: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)


class ForecastedMetrics(BaseModel):
    """Forecasted metrics associated with a risk."""
    metric_name: str = Field(description="Name of the metric")
    forecasted_value: float = Field(description="Forecasted value")
    baseline_value: float = Field(description="Baseline/historical value")
    change_percentage: float = Field(description="Percentage change")
    additional_data: Optional[Dict[str, Any]] = Field(default=None)


class MitigationStrategy(BaseModel):
    """LLM-generated mitigation strategy."""
    strategy_name: str = Field(description="Name of the strategy")
    action_steps: List[str] = Field(description="Numbered action steps")
    timeline_days: int = Field(description="Implementation timeline in days")
    estimated_cost: float = Field(description="Estimated cost in USD")
    risk_reduction: float = Field(description="Expected risk reduction percentage")
    dependencies: List[str] = Field(default_factory=list, description="Prerequisites")
    pros: List[str] = Field(default_factory=list, description="Advantages")
    cons: List[str] = Field(default_factory=list, description="Disadvantages")


class RiskItem(BaseModel):
    """Individual risk item."""
    risk_id: str = Field(description="Unique risk identifier")
    category: str = Field(description="Risk category")
    sub_categories: List[str] = Field(default_factory=list, description="Sub-categories")
    impact: str = Field(description="Business impact description")
    severity: str = Field(description="Severity level")
    probability: float = Field(ge=0, le=1, description="Probability (0-1)")
    risk_score: float = Field(ge=0, le=100, description="Risk score (0-100)")
    priority: str = Field(description="Priority classification")
    timeline_days: int = Field(description="Days until potential disruption")
    affected_entities: AffectedEntities = Field(description="Affected entities")
    forecasted_metrics: List[ForecastedMetrics] = Field(description="Related metrics")
    root_causes: List[str] = Field(description="Contributing factors")
    mitigations: List[MitigationStrategy] = Field(
        default_factory=list,
        description="Mitigation strategies"
    )


# ============= Response Models =============

class AnalysisSummary(BaseModel):
    """Summary of analysis results."""
    total_risks: int = Field(description="Total number of risks identified")
    critical_risks: int = Field(description="Number of critical risks")
    high_risks: int = Field(description="Number of high priority risks")
    medium_risks: int = Field(description="Number of medium priority risks")
    low_risks: int = Field(description="Number of low priority risks")
    total_entities_affected: int = Field(description="Total unique entities affected")


class ActionRecommendation(BaseModel):
    """Action recommendation."""
    action: str = Field(description="Recommended action")
    priority: str = Field(description="Priority level")
    related_risks: List[str] = Field(description="Related risk IDs")


class Recommendations(BaseModel):
    """Categorized recommendations."""
    immediate_actions: List[ActionRecommendation] = Field(
        default_factory=list,
        description="Actions to take immediately"
    )
    short_term_actions: List[ActionRecommendation] = Field(
        default_factory=list,
        description="Actions for short term (1-2 weeks)"
    )
    long_term_actions: List[ActionRecommendation] = Field(
        default_factory=list,
        description="Actions for long term (2+ weeks)"
    )


class AnalysisResponse(BaseModel):
    """Complete analysis response."""
    analysis_id: str = Field(description="Unique analysis identifier")
    timestamp: str = Field(description="Analysis timestamp")
    forecast_horizon: int = Field(description="Forecast horizon in days")
    summary: AnalysisSummary = Field(description="Analysis summary")
    forecasts: Dict[str, List[ForecastResult]] = Field(description="Forecasts by module")
    risks: List[RiskItem] = Field(description="Identified risks")
    recommendations: Recommendations = Field(description="Recommendations")


# ============= Entity Models =============

class SupplierInfo(BaseModel):
    """Supplier entity information."""
    supplier_id: str
    supplier_name: str
    supplier_tier: str
    supplier_region: str
    components: List[str]


class PlantInfo(BaseModel):
    """Manufacturing plant information."""
    plant_id: str
    plant_name: str
    plant_region: str
    skus: List[str]


class WarehouseInfo(BaseModel):
    """Warehouse entity information."""
    warehouse_id: str
    warehouse_name: str
    warehouse_region: str
    skus: List[str]


class RouteInfo(BaseModel):
    """Transportation route information."""
    route_id: str
    origin: str
    destination: str
    carrier_id: str
    carrier_name: str
    mode: str


class EntityInfo(BaseModel):
    """All available entities."""
    suppliers: List[SupplierInfo] = Field(default_factory=list)
    plants: List[PlantInfo] = Field(default_factory=list)
    warehouses: List[WarehouseInfo] = Field(default_factory=list)
    routes: List[RouteInfo] = Field(default_factory=list)
    skus: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)


# ============= Utility Models =============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Service status")
    timestamp: str = Field(description="Current timestamp")
    version: str = Field(description="API version")
    data_status: Dict[str, bool] = Field(description="Data availability status")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")


class CachedAnalysis(BaseModel):
    """Cached analysis result."""
    analysis_id: str
    created_at: str
    expires_at: str
    response: AnalysisResponse

