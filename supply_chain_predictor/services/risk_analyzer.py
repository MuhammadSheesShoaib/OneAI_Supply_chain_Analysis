"""
Risk Analyzer service for identifying and classifying supply chain risks.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.risk_scorer import RiskScorer
from utils.helpers import generate_risk_id, classify_risk_priority
from schemas.models import (
    RiskItem, AffectedEntities, ForecastedMetrics, RiskCategory
)

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """
    Risk analyzer class for identifying and classifying supply chain risks.
    
    Takes Prophet forecasts as input and applies risk detection logic
    for each category.
    """
    
    def __init__(self):
        """Initialize the RiskAnalyzer with risk scorer."""
        self.scorer = RiskScorer()
        logger.info("RiskAnalyzer initialized")
    
    def analyze_supplier_risks(
        self,
        forecasts: List[Dict[str, Any]],
        supplier_data: pd.DataFrame,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze supplier delay risks from forecasts.
        
        Args:
            forecasts: List of supplier lead time forecasts
            supplier_data: Historical supplier data
            horizon_days: Forecast horizon
            
        Returns:
            List of identified risks
        """
        risks = []
        logger.info(f"[Risk] Analyzing {len(forecasts)} supplier forecasts for risks")
        
        for forecast in forecasts:
            if forecast.get("error"):
                logger.debug(f"[Risk] Skipping forecast with error: {forecast.get('error')}")
                continue
            
            supplier_id = forecast.get("entity_id")
            component_id = forecast.get("component_id")
            entity_context = f"{supplier_id}-{component_id}"
            
            # Get historical on-time delivery rate
            supplier_history = supplier_data[
                supplier_data["supplier_id"] == supplier_id
            ]
            on_time_rate = supplier_history["on_time_delivery"].mean() if len(supplier_history) > 0 else 0.9
            
            # Calculate confidence interval width
            forecast_data = forecast.get("forecast_data", [])
            if forecast_data:
                df = pd.DataFrame(forecast_data)
                avg_width = (df["yhat_upper"] - df["yhat_lower"]).mean()
            else:
                avg_width = 0
            
            # Calculate risk score
            risk_result = self.scorer.calculate_supplier_risk_score(
                forecasted_lead_time=forecast.get("forecasted_avg", 0),
                historical_avg_lead_time=forecast.get("historical_avg", 1),
                confidence_interval_width=avg_width,
                timeline_days=horizon_days,
                on_time_delivery_rate=on_time_rate
            )
            
            if risk_result["risk_detected"]:
                # Determine root causes
                root_causes = self._identify_supplier_root_causes(
                    forecast, supplier_history, risk_result
                )
                
                risk_id = generate_risk_id()
                risk = {
                    "risk_id": risk_id,
                    "category": RiskCategory.SUPPLIER_DELAYS.value,
                    "sub_categories": ["Lead Time Increase"],
                    "impact": "Production Delays",
                    "severity": risk_result["priority"],
                    "probability": risk_result["probability"],
                    "risk_score": risk_result["risk_score"],
                    "priority": risk_result["priority"],
                    "timeline_days": horizon_days,
                    "affected_entities": {
                        "suppliers": [supplier_id],
                        "plants": [],
                        "warehouses": [],
                        "skus": [],
                        "routes": [],
                        "regions": [supplier_history["supplier_region"].iloc[0]] if "supplier_region" in supplier_history.columns and len(supplier_history) > 0 else []
                    },
                    "forecasted_metrics": [
                        {
                            "metric_name": "lead_time_days",
                            "forecasted_value": risk_result["forecasted_metrics"]["lead_time_forecast"],
                            "baseline_value": risk_result["forecasted_metrics"]["baseline_lead_time"],
                            "change_percentage": risk_result["forecasted_metrics"]["increase_percentage"]
                        }
                    ],
                    "root_causes": root_causes
                }
                risks.append(risk)
                logger.info(f"[Risk] Risk detected: {risk_id} for {entity_context}, "
                           f"score={risk_result['risk_score']:.1f}, priority={risk_result['priority']}, "
                           f"lead_time={forecast.get('historical_avg'):.1f}→{forecast.get('forecasted_avg'):.1f} days")
            else:
                logger.debug(f"[Risk] No risk detected for {entity_context} (score={risk_result.get('risk_score', 0):.1f})")
        
        logger.info(f"[Risk] Supplier risk analysis complete: {len(risks)} risks identified from {len(forecasts)} forecasts")
        return risks
    
    def analyze_production_risks(
        self,
        forecasts: List[Dict[str, Any]],
        production_data: pd.DataFrame,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze production delay/bottleneck risks.
        
        Args:
            forecasts: List of production capacity forecasts
            production_data: Historical production data
            horizon_days: Forecast horizon
            
        Returns:
            List of identified risks
        """
        risks = []
        
        for forecast in forecasts:
            if forecast.get("error"):
                continue
            
            plant_id = forecast.get("entity_id")
            sku = forecast.get("sku")
            
            # Get historical downtime
            plant_history = production_data[
                (production_data["plant_id"] == plant_id) &
                (production_data["sku"] == sku)
            ]
            historical_downtime = plant_history["downtime_hours"].mean() if len(plant_history) > 0 else 0
            
            # Get downtime forecast
            downtime_forecast = forecast.get("downtime_forecast", {})
            forecasted_downtime = downtime_forecast.get("forecasted_avg", historical_downtime)
            
            # Calculate risk score
            risk_result = self.scorer.calculate_production_risk_score(
                forecasted_utilization=forecast.get("forecasted_avg", 0),
                forecasted_downtime=forecasted_downtime,
                historical_downtime=historical_downtime,
                timeline_days=horizon_days
            )
            
            if risk_result["risk_detected"]:
                # Determine sub-categories
                sub_cats = []
                if risk_result.get("bottleneck_risk"):
                    sub_cats.append("Capacity Bottleneck")
                if risk_result.get("downtime_risk"):
                    sub_cats.append("Increased Downtime")
                
                root_causes = self._identify_production_root_causes(
                    forecast, plant_history, risk_result
                )
                
                risk = {
                    "risk_id": generate_risk_id(),
                    "category": RiskCategory.PRODUCTION_DELAYS.value,
                    "sub_categories": sub_cats,
                    "impact": "Reduced Output",
                    "severity": risk_result["priority"],
                    "probability": risk_result["probability"],
                    "risk_score": risk_result["risk_score"],
                    "priority": risk_result["priority"],
                    "timeline_days": horizon_days,
                    "affected_entities": {
                        "suppliers": [],
                        "plants": [plant_id],
                        "warehouses": [],
                        "skus": [sku],
                        "routes": [],
                        "regions": [plant_history["plant_region"].iloc[0]] if "plant_region" in plant_history.columns and len(plant_history) > 0 else []
                    },
                    "forecasted_metrics": [
                        {
                            "metric_name": "capacity_utilization",
                            "forecasted_value": risk_result["forecasted_metrics"]["capacity_utilization"],
                            "baseline_value": plant_history["capacity_utilization"].mean() if len(plant_history) > 0 else 0,
                            "change_percentage": 0
                        }
                    ],
                    "root_causes": root_causes
                }
                risks.append(risk)
        
        return risks
    
    def analyze_inventory_risks(
        self,
        inventory_forecasts: List[Dict[str, Any]],
        demand_forecasts: List[Dict[str, Any]],
        inventory_data: pd.DataFrame,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze stock shortage risks.
        
        Args:
            inventory_forecasts: List of inventory level forecasts
            demand_forecasts: List of demand forecasts
            inventory_data: Historical inventory data
            horizon_days: Forecast horizon
            
        Returns:
            List of identified risks
        """
        risks = []
        
        for inv_forecast in inventory_forecasts:
            if inv_forecast.get("error"):
                continue
            
            warehouse_id = inv_forecast.get("entity_id")
            sku = inv_forecast.get("sku")
            safety_stock = inv_forecast.get("safety_stock", 0)
            
            # Get inventory lower bound
            forecast_data = inv_forecast.get("forecast_data", [])
            inventory_lower = min([f.get("yhat_lower", float("inf")) for f in forecast_data]) if forecast_data else 0
            
            # Find matching demand forecast
            demand_upper = 0
            for demand_forecast in demand_forecasts:
                if demand_forecast.get("sku") == sku:
                    demand_data = demand_forecast.get("forecast_data", [])
                    if demand_data:
                        demand_upper = max([f.get("yhat_upper", 0) for f in demand_data])
                    break
            
            # Calculate risk score
            risk_result = self.scorer.calculate_inventory_risk_score(
                forecasted_inventory=inv_forecast.get("forecasted_avg", 0),
                safety_stock=safety_stock,
                forecasted_demand_upper=demand_upper,
                inventory_lower_bound=inventory_lower,
                timeline_days=horizon_days
            )
            
            if risk_result["risk_detected"]:
                sub_cats = []
                if risk_result.get("shortage_risk"):
                    sub_cats.append("Below Safety Stock")
                if risk_result.get("demand_exceeds_supply"):
                    sub_cats.append("Demand Exceeds Supply")
                
                wh_history = inventory_data[inventory_data["warehouse_id"] == warehouse_id]
                
                risk = {
                    "risk_id": generate_risk_id(),
                    "category": RiskCategory.STOCK_SHORTAGES.value,
                    "sub_categories": sub_cats,
                    "impact": "Stockout Risk",
                    "severity": risk_result["priority"],
                    "probability": risk_result["probability"],
                    "risk_score": risk_result["risk_score"],
                    "priority": risk_result["priority"],
                    "timeline_days": horizon_days,
                    "affected_entities": {
                        "suppliers": [],
                        "plants": [],
                        "warehouses": [warehouse_id],
                        "skus": [sku],
                        "routes": [],
                        "regions": [wh_history["warehouse_region"].iloc[0]] if "warehouse_region" in wh_history.columns and len(wh_history) > 0 else []
                    },
                    "forecasted_metrics": [
                        {
                            "metric_name": "stock_on_hand",
                            "forecasted_value": risk_result["forecasted_metrics"]["forecasted_inventory"],
                            "baseline_value": risk_result["forecasted_metrics"]["safety_stock"],
                            "change_percentage": 0
                        }
                    ],
                    "root_causes": [
                        f"Forecasted inventory ({risk_result['forecasted_metrics']['forecasted_inventory']:.0f}) below safety stock ({safety_stock:.0f})",
                        "High demand variability" if demand_upper > 0 else "Insufficient replenishment"
                    ]
                }
                risks.append(risk)
        
        return risks
    
    def analyze_demand_risks(
        self,
        forecasts: List[Dict[str, Any]],
        demand_data: pd.DataFrame,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze demand volatility risks.
        
        Args:
            forecasts: List of demand forecasts
            demand_data: Historical demand data
            horizon_days: Forecast horizon
            
        Returns:
            List of identified risks
        """
        risks = []
        
        for forecast in forecasts:
            if forecast.get("error"):
                continue
            
            region = forecast.get("entity_id")
            sku = forecast.get("sku")
            volatility = forecast.get("volatility", 0)
            
            # Get forecast bounds
            forecast_data = forecast.get("forecast_data", [])
            if forecast_data:
                df = pd.DataFrame(forecast_data)
                yhat_avg = df["yhat"].mean()
                yhat_upper_avg = df["yhat_upper"].mean()
                yhat_lower_avg = df["yhat_lower"].mean()
            else:
                continue
            
            # Calculate risk score
            risk_result = self.scorer.calculate_demand_volatility_score(
                yhat=yhat_avg,
                yhat_upper=yhat_upper_avg,
                yhat_lower=yhat_lower_avg,
                timeline_days=horizon_days
            )
            
            if risk_result["risk_detected"]:
                risk = {
                    "risk_id": generate_risk_id(),
                    "category": RiskCategory.DEMAND_VOLATILITY.value,
                    "sub_categories": ["High Forecast Uncertainty"],
                    "impact": "Planning Difficulty",
                    "severity": risk_result["priority"],
                    "probability": risk_result["probability"],
                    "risk_score": risk_result["risk_score"],
                    "priority": risk_result["priority"],
                    "timeline_days": horizon_days,
                    "affected_entities": {
                        "suppliers": [],
                        "plants": [],
                        "warehouses": [],
                        "skus": [sku],
                        "routes": [],
                        "regions": [region]
                    },
                    "forecasted_metrics": [
                        {
                            "metric_name": "demand_volatility",
                            "forecasted_value": risk_result["volatility"],
                            "baseline_value": 30,  # Threshold
                            "change_percentage": 0
                        }
                    ],
                    "root_causes": [
                        f"High demand uncertainty: ±{risk_result['volatility']:.1f}%",
                        "Seasonal fluctuations",
                        "Market unpredictability"
                    ]
                }
                risks.append(risk)
        
        return risks
    
    def analyze_transportation_risks(
        self,
        forecasts: List[Dict[str, Any]],
        transport_data: pd.DataFrame,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze transportation delay risks.
        
        Args:
            forecasts: List of transit time forecasts
            transport_data: Historical transportation data
            horizon_days: Forecast horizon
            
        Returns:
            List of identified risks
        """
        risks = []
        
        for forecast in forecasts:
            if forecast.get("error"):
                continue
            
            route_id = forecast.get("entity_id")
            
            # Get historical on-time rate
            route_history = transport_data[transport_data["route_id"] == route_id]
            on_time_rate = route_history["on_time_delivery"].mean() if len(route_history) > 0 else 0.9
            
            # Calculate risk score
            risk_result = self.scorer.calculate_transportation_risk_score(
                forecasted_transit_time=forecast.get("forecasted_avg", 0),
                baseline_transit_time=forecast.get("historical_avg", 1),
                timeline_days=horizon_days,
                on_time_rate=on_time_rate
            )
            
            if risk_result["risk_detected"]:
                # Get route details
                origin = route_history["origin"].iloc[0] if "origin" in route_history.columns and len(route_history) > 0 else ""
                destination = route_history["destination"].iloc[0] if "destination" in route_history.columns and len(route_history) > 0 else ""
                carrier = route_history["carrier_name"].iloc[0] if "carrier_name" in route_history.columns and len(route_history) > 0 else ""
                
                risk = {
                    "risk_id": generate_risk_id(),
                    "category": RiskCategory.TRANSPORTATION_ISSUES.value,
                    "sub_categories": ["Transit Delay"],
                    "impact": "Delivery Delays",
                    "severity": risk_result["priority"],
                    "probability": risk_result["probability"],
                    "risk_score": risk_result["risk_score"],
                    "priority": risk_result["priority"],
                    "timeline_days": horizon_days,
                    "affected_entities": {
                        "suppliers": [],
                        "plants": [origin] if origin.startswith("PLANT") else [],
                        "warehouses": [destination] if destination.startswith("WH") else [],
                        "skus": [],
                        "routes": [route_id],
                        "regions": []
                    },
                    "forecasted_metrics": [
                        {
                            "metric_name": "transit_time_days",
                            "forecasted_value": risk_result["forecasted_metrics"]["transit_time_forecast"],
                            "baseline_value": risk_result["forecasted_metrics"]["baseline_transit_time"],
                            "change_percentage": risk_result["forecasted_metrics"]["delay_percentage"]
                        }
                    ],
                    "root_causes": [
                        f"Transit time increase: +{risk_result['forecasted_metrics']['delay_percentage']:.1f}%",
                        f"Historical on-time rate: {on_time_rate*100:.1f}%",
                        f"Carrier: {carrier}"
                    ]
                }
                risks.append(risk)
        
        return risks
    
    def analyze_external_risks(
        self,
        forecasts: List[Dict[str, Any]],
        external_data: pd.DataFrame,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze external factor risks (weather, tariffs, etc.).
        
        Args:
            forecasts: List of external factor forecasts
            external_data: Historical external factor data
            horizon_days: Forecast horizon
            
        Returns:
            List of identified risks
        """
        risks = []
        
        for forecast in forecasts:
            if forecast.get("error"):
                continue
            
            region = forecast.get("entity_id")
            factor_type = forecast.get("metric")
            
            # Calculate risk score
            risk_result = self.scorer.calculate_external_factor_risk_score(
                factor_type=factor_type,
                forecasted_value=forecast.get("forecasted_avg", 0),
                historical_value=forecast.get("historical_avg", 0),
                timeline_days=horizon_days
            )
            
            if risk_result["risk_detected"]:
                impact_map = {
                    "weather_severity_index": "Supply Chain Disruption",
                    "tariff_rate": "Cost Increase",
                    "port_congestion_index": "Shipping Delays",
                    "fuel_price_usd": "Transportation Cost Increase",
                    "geopolitical_risk_index": "Supply Uncertainty"
                }
                
                risk = {
                    "risk_id": generate_risk_id(),
                    "category": RiskCategory.EXTERNAL_FACTORS.value,
                    "sub_categories": [risk_result.get("sub_category", factor_type)],
                    "impact": impact_map.get(factor_type, "External Disruption"),
                    "severity": risk_result["priority"],
                    "probability": risk_result["probability"],
                    "risk_score": risk_result["risk_score"],
                    "priority": risk_result["priority"],
                    "timeline_days": horizon_days,
                    "affected_entities": {
                        "suppliers": [],
                        "plants": [],
                        "warehouses": [],
                        "skus": [],
                        "routes": [],
                        "regions": [region]
                    },
                    "forecasted_metrics": [
                        {
                            "metric_name": factor_type,
                            "forecasted_value": risk_result["forecasted_metrics"]["forecasted_value"],
                            "baseline_value": risk_result["forecasted_metrics"]["historical_value"],
                            "change_percentage": 0
                        }
                    ],
                    "root_causes": [
                        f"Elevated {factor_type.replace('_', ' ')}: {risk_result['forecasted_metrics']['forecasted_value']:.2f}",
                        f"Region: {region}"
                    ]
                }
                risks.append(risk)
        
        return risks
    
    def _identify_supplier_root_causes(
        self,
        forecast: Dict[str, Any],
        history: pd.DataFrame,
        risk_result: Dict[str, Any]
    ) -> List[str]:
        """Identify root causes for supplier risks."""
        causes = []
        
        # Lead time increase
        increase_pct = risk_result.get("forecasted_metrics", {}).get("increase_percentage", 0)
        if increase_pct > 0:
            causes.append(f"Lead time increase of {increase_pct:.1f}%")
        
        # Historical on-time delivery issues
        if len(history) > 0 and "on_time_delivery" in history.columns:
            on_time_rate = history["on_time_delivery"].mean()
            if on_time_rate < 0.9:
                causes.append(f"Low historical on-time delivery rate: {on_time_rate*100:.1f}%")
        
        # Supplier region
        if len(history) > 0 and "supplier_region" in history.columns:
            region = history["supplier_region"].iloc[0]
            causes.append(f"Supplier located in {region} region")
        
        if not causes:
            causes.append("Historical performance trends indicate potential delays")
        
        return causes
    
    def _identify_production_root_causes(
        self,
        forecast: Dict[str, Any],
        history: pd.DataFrame,
        risk_result: Dict[str, Any]
    ) -> List[str]:
        """Identify root causes for production risks."""
        causes = []
        
        if risk_result.get("bottleneck_risk"):
            util = risk_result.get("forecasted_metrics", {}).get("capacity_utilization", 0)
            causes.append(f"Capacity utilization at {util*100:.1f}%")
        
        if risk_result.get("downtime_risk"):
            downtime_increase = risk_result.get("forecasted_metrics", {}).get("downtime_increase_pct", 0)
            causes.append(f"Downtime increase of {downtime_increase:.1f}%")
        
        # High defect rate
        if len(history) > 0 and "defect_rate" in history.columns:
            defect_rate = history["defect_rate"].mean()
            if defect_rate > 0.03:
                causes.append(f"Elevated defect rate: {defect_rate*100:.2f}%")
        
        if not causes:
            causes.append("Production constraints identified in forecast")
        
        return causes
    
    def aggregate_risks(
        self,
        all_risks: List[Dict[str, Any]],
        risk_threshold: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Aggregate and filter risks by threshold.
        
        Args:
            all_risks: List of all identified risks
            risk_threshold: Minimum risk score to include
            
        Returns:
            Filtered and sorted list of risks
        """
        # Filter by threshold
        filtered = [r for r in all_risks if r.get("risk_score", 0) >= risk_threshold]
        
        # Sort by risk score (descending)
        filtered.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
        
        return filtered
    
    def generate_summary(
        self,
        risks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for risks.
        
        Args:
            risks: List of risk items
            
        Returns:
            Summary dictionary
        """
        summary = {
            "total_risks": len(risks),
            "critical_risks": sum(1 for r in risks if r.get("priority") == "CRITICAL"),
            "high_risks": sum(1 for r in risks if r.get("priority") == "HIGH"),
            "medium_risks": sum(1 for r in risks if r.get("priority") == "MEDIUM"),
            "low_risks": sum(1 for r in risks if r.get("priority") == "LOW"),
            "total_entities_affected": 0
        }
        
        # Count unique affected entities
        all_entities = set()
        for risk in risks:
            entities = risk.get("affected_entities", {})
            for entity_type, entity_list in entities.items():
                all_entities.update(entity_list)
        
        summary["total_entities_affected"] = len(all_entities)
        
        return summary

