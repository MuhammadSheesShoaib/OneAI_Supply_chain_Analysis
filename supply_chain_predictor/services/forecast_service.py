"""
Forecast Service for orchestrating all Prophet forecasts and risk analysis.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.data_loader import DataLoader
from models.prophet_forecaster import ProphetForecaster
from services.risk_analyzer import RiskAnalyzer
from services.mitigation_service import MitigationService
from schemas.models import ModuleType
from utils.helpers import generate_analysis_id, format_timestamp

logger = logging.getLogger(__name__)


class ForecastService:
    """
    Orchestration service for running all Prophet forecasts and risk analysis.
    
    Coordinates:
    - Data loading
    - Prophet forecasts for all 6 modules
    - Risk analysis
    - Mitigation generation
    """
    
    def __init__(self):
        """Initialize the ForecastService with all components."""
        self.data_loader = DataLoader()
        self.forecaster = ProphetForecaster()
        self.risk_analyzer = RiskAnalyzer()
        self.mitigation_service = MitigationService()
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
        logger.info("ForecastService initialized")
    
    def _run_supplier_forecasts(
        self,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """Run forecasts for supplier lead times."""
        try:
            df = self.data_loader.load_supplier_lead_times()
            forecasts = []
            
            # Get unique supplier-component combinations
            combinations = df.groupby(["supplier_id", "component_id"]).size().reset_index()
            logger.info(f"[Forecast] Starting supplier forecasts: {len(combinations)} combinations, horizon={horizon_days} days")
            
            for idx, row in combinations.iterrows():
                supplier_id = row["supplier_id"]
                component_id = row["component_id"]
                entity_context = f"{supplier_id}-{component_id}"
                
                try:
                    logger.debug(f"[Forecast] Processing supplier forecast {idx+1}/{len(combinations)}: {entity_context}")
                    forecast = self.forecaster.forecast_supplier_leadtime(
                        df=df,
                        supplier_id=supplier_id,
                        component_id=component_id,
                        horizon_days=horizon_days
                    )
                    if forecast.get("error"):
                        logger.warning(f"[Forecast] Forecast returned error for {entity_context}: {forecast.get('error')}")
                    else:
                        forecasts.append(forecast)
                        logger.debug(f"[Forecast] Successfully forecasted {entity_context}")
                except Exception as e:
                    logger.warning(f"[Forecast] Failed forecast for {entity_context}: {e}", exc_info=True)
            
            logger.info(f"[Forecast] Supplier forecasts complete: {len(forecasts)}/{len(combinations)} successful")
            return forecasts
            
        except Exception as e:
            logger.error(f"[Forecast] Error in supplier forecasts: {e}", exc_info=True)
            return []
    
    def _run_manufacturing_forecasts(
        self,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """Run forecasts for manufacturing production."""
        try:
            df = self.data_loader.load_manufacturing_production()
            forecasts = []
            
            # Get unique plant-sku combinations
            combinations = df.groupby(["plant_id", "sku"]).size().reset_index()
            logger.info(f"[Forecast] Starting manufacturing forecasts: {len(combinations)} combinations")
            
            for idx, row in combinations.iterrows():
                entity_context = f"{row['plant_id']}-{row['sku']}"
                try:
                    forecast = self.forecaster.forecast_production_capacity(
                        df=df,
                        plant_id=row["plant_id"],
                        sku=row["sku"],
                        horizon_days=horizon_days
                    )
                    if not forecast.get("error"):
                        forecasts.append(forecast)
                except Exception as e:
                    logger.warning(f"[Forecast] Failed forecast for {entity_context}: {e}")
            
            return forecasts
            
        except Exception as e:
            logger.error(f"[Forecast] Error in manufacturing forecasts: {e}", exc_info=True)
            return []
    
    def _run_inventory_forecasts(
        self,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """Run forecasts for inventory levels."""
        try:
            df = self.data_loader.load_inventory_levels()
            forecasts = []
            
            # Get unique warehouse-sku combinations
            combinations = df.groupby(["warehouse_id", "sku"]).size().reset_index()
            logger.info(f"[Forecast] Starting inventory forecasts: {len(combinations)} combinations")
            
            for idx, row in combinations.iterrows():
                entity_context = f"{row['warehouse_id']}-{row['sku']}"
                try:
                    forecast = self.forecaster.forecast_inventory_levels(
                        df=df,
                        warehouse_id=row["warehouse_id"],
                        sku=row["sku"],
                        horizon_days=horizon_days
                    )
                    if not forecast.get("error"):
                        forecasts.append(forecast)
                except Exception as e:
                    logger.warning(f"[Forecast] Failed forecast for {entity_context}: {e}")
            
            return forecasts
            
        except Exception as e:
            logger.error(f"[Forecast] Error in inventory forecasts: {e}", exc_info=True)
            return []
    
    def _run_demand_forecasts(
        self,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """Run forecasts for customer demand."""
        try:
            df = self.data_loader.load_customer_demand()
            forecasts = []
            
            # Get unique region-sku combinations
            combinations = df.groupby(["region", "sku"]).size().reset_index()
            logger.info(f"[Forecast] Starting demand forecasts: {len(combinations)} combinations")
            
            for idx, row in combinations.iterrows():
                entity_context = f"{row['region']}-{row['sku']}"
                try:
                    forecast = self.forecaster.forecast_demand(
                        df=df,
                        region=row["region"],
                        sku=row["sku"],
                        horizon_days=horizon_days,
                        include_promotions=True
                    )
                    if not forecast.get("error"):
                        forecasts.append(forecast)
                except Exception as e:
                    logger.warning(f"[Forecast] Failed forecast for {entity_context}: {e}")
            
            return forecasts
            
        except Exception as e:
            logger.error(f"[Forecast] Error in demand forecasts: {e}", exc_info=True)
            return []
    
    def _run_transportation_forecasts(
        self,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """Run forecasts for transportation/transit times."""
        try:
            df = self.data_loader.load_transportation_data()
            forecasts = []
            
            # Get unique routes
            routes = df["route_id"].unique()
            logger.info(f"[Forecast] Starting transportation forecasts: {len(routes)} routes")
            
            for route_id in routes:
                try:
                    forecast = self.forecaster.forecast_transit_time(
                        df=df,
                        route_id=route_id,
                        horizon_days=horizon_days
                    )
                    if not forecast.get("error"):
                        forecasts.append(forecast)
                except Exception as e:
                    logger.warning(f"[Forecast] Failed forecast for route {route_id}: {e}")
            
            return forecasts
            
        except Exception as e:
            logger.error(f"[Forecast] Error in transportation forecasts: {e}", exc_info=True)
            return []
    
    def _run_external_forecasts(
        self,
        horizon_days: int
    ) -> List[Dict[str, Any]]:
        """Run forecasts for external factors."""
        try:
            df = self.data_loader.load_external_factors()
            forecasts = []
            
            # Get unique regions
            regions = df["region"].unique()
            
            # Factor types to forecast
            factor_types = [
                "weather_severity_index",
                "tariff_rate",
                "port_congestion_index",
                "fuel_price_usd"
            ]
            
            total_combinations = len(regions) * len([f for f in factor_types if f in df.columns])
            logger.info(f"[Forecast] Starting external factor forecasts: {len(regions)} regions, {total_combinations} total combinations")
            
            for region in regions:
                for factor_type in factor_types:
                    if factor_type in df.columns:
                        entity_context = f"{region}-{factor_type}"
                        try:
                            forecast = self.forecaster.forecast_external_factors(
                                df=df,
                                region=region,
                                factor_type=factor_type,
                                horizon_days=horizon_days
                            )
                            if not forecast.get("error"):
                                forecasts.append(forecast)
                        except Exception as e:
                            logger.warning(f"[Forecast] Failed forecast for {entity_context}: {e}")
            
            return forecasts
            
        except Exception as e:
            logger.error(f"[Forecast] Error in external forecasts: {e}", exc_info=True)
            return []
    
    def run_forecasts(
        self,
        horizon_days: int,
        modules: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run forecasts for specified modules.
        
        Args:
            horizon_days: Forecast horizon in days
            modules: List of module names to forecast
            
        Returns:
            Dictionary of forecasts by module
        """
        forecasts = {}
        
        module_functions = {
            "suppliers": self._run_supplier_forecasts,
            "manufacturing": self._run_manufacturing_forecasts,
            "inventory": self._run_inventory_forecasts,
            "demand": self._run_demand_forecasts,
            "transportation": self._run_transportation_forecasts,
            "external": self._run_external_forecasts,
        }
        
        for module in modules:
            if module in module_functions:
                logger.info(f"[Forecast] ===== Starting {module.upper()} module forecasts =====")
                try:
                    forecasts[module] = module_functions[module](horizon_days)
                    logger.info(f"[Forecast] ===== {module.upper()} module complete: {len(forecasts[module])} forecasts =====")
                except Exception as e:
                    logger.error(f"[Forecast] ===== {module.upper()} module failed: {e} =====", exc_info=True)
                    forecasts[module] = []
        
        return forecasts
    
    def analyze_risks(
        self,
        forecasts: Dict[str, List[Dict[str, Any]]],
        horizon_days: int,
        risk_threshold: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Analyze risks from forecasts.
        
        Args:
            forecasts: Dictionary of forecasts by module
            horizon_days: Forecast horizon
            risk_threshold: Minimum risk score to include
            
        Returns:
            List of identified risks
        """
        all_risks = []
        
        # Load data for risk analysis
        try:
            logger.debug(f"[Risk] Loading historical data for risk analysis")
            supplier_data = self.data_loader.load_supplier_lead_times()
            production_data = self.data_loader.load_manufacturing_production()
            inventory_data = self.data_loader.load_inventory_levels()
            demand_data = self.data_loader.load_customer_demand()
            transport_data = self.data_loader.load_transportation_data()
            external_data = self.data_loader.load_external_factors()
            logger.debug(f"[Risk] Historical data loaded successfully")
        except Exception as e:
            logger.error(f"[Risk] Error loading data for risk analysis: {e}", exc_info=True)
            return []
        
        # Analyze each module
        if "suppliers" in forecasts and forecasts["suppliers"]:
            logger.debug(f"[Risk] Analyzing {len(forecasts['suppliers'])} supplier forecasts")
            risks = self.risk_analyzer.analyze_supplier_risks(
                forecasts["suppliers"],
                supplier_data,
                horizon_days
            )
            all_risks.extend(risks)
            logger.debug(f"[Risk] Supplier risks: {len(risks)} identified")
        
        if "manufacturing" in forecasts and forecasts["manufacturing"]:
            logger.debug(f"[Risk] Analyzing {len(forecasts['manufacturing'])} manufacturing forecasts")
            risks = self.risk_analyzer.analyze_production_risks(
                forecasts["manufacturing"],
                production_data,
                horizon_days
            )
            all_risks.extend(risks)
            logger.debug(f"[Risk] Manufacturing risks: {len(risks)} identified")
        
        if "inventory" in forecasts and forecasts["inventory"]:
            demand_forecasts = forecasts.get("demand", [])
            logger.debug(f"[Risk] Analyzing {len(forecasts['inventory'])} inventory forecasts with {len(demand_forecasts)} demand forecasts")
            risks = self.risk_analyzer.analyze_inventory_risks(
                forecasts["inventory"],
                demand_forecasts,
                inventory_data,
                horizon_days
            )
            all_risks.extend(risks)
            logger.debug(f"[Risk] Inventory risks: {len(risks)} identified")
        
        if "demand" in forecasts and forecasts["demand"]:
            logger.debug(f"[Risk] Analyzing {len(forecasts['demand'])} demand forecasts")
            risks = self.risk_analyzer.analyze_demand_risks(
                forecasts["demand"],
                demand_data,
                horizon_days
            )
            all_risks.extend(risks)
            logger.debug(f"[Risk] Demand risks: {len(risks)} identified")
        
        if "transportation" in forecasts and forecasts["transportation"]:
            logger.debug(f"[Risk] Analyzing {len(forecasts['transportation'])} transportation forecasts")
            risks = self.risk_analyzer.analyze_transportation_risks(
                forecasts["transportation"],
                transport_data,
                horizon_days
            )
            all_risks.extend(risks)
            logger.debug(f"[Risk] Transportation risks: {len(risks)} identified")
        
        if "external" in forecasts and forecasts["external"]:
            logger.debug(f"[Risk] Analyzing {len(forecasts['external'])} external factor forecasts")
            risks = self.risk_analyzer.analyze_external_risks(
                forecasts["external"],
                external_data,
                horizon_days
            )
            all_risks.extend(risks)
            logger.debug(f"[Risk] External risks: {len(risks)} identified")
        
        # Aggregate and filter
        logger.info(f"[Risk] Total risks before filtering: {len(all_risks)} (threshold={risk_threshold})")
        filtered_risks = self.risk_analyzer.aggregate_risks(all_risks, risk_threshold)
        logger.info(f"[Risk] Risks after filtering: {len(filtered_risks)} (removed {len(all_risks) - len(filtered_risks)})")
        
        return filtered_risks
    
    def add_mitigations(
        self,
        risks: List[Dict[str, Any]],
        include_mitigations: bool = True,
        max_risks: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Add mitigation strategies to risks.
        
        Args:
            risks: List of risk dictionaries
            include_mitigations: Whether to generate mitigations
            max_risks: Maximum number of risks to generate mitigations for
            
        Returns:
            Risks with mitigations added
        """
        if not include_mitigations:
            for risk in risks:
                risk["mitigations"] = []
            return risks
        
        # Generate mitigations for top risks
        risks_to_process = min(len(risks), max_risks)
        logger.info(f"[Mitigation] Generating mitigations for {risks_to_process} risks (max_risks={max_risks})")
        
        for i, risk in enumerate(risks[:max_risks]):
            risk_id = risk.get('risk_id', 'UNKNOWN')
            risk_category = risk.get('category', 'Unknown')
            risk_score = risk.get('risk_score', 0)
            
            try:
                logger.debug(f"[Mitigation] Processing risk {i+1}/{risks_to_process}: {risk_id} ({risk_category}, score={risk_score:.1f})")
                mitigations = self.mitigation_service.generate_mitigations(risk)
                risk["mitigations"] = mitigations
                logger.info(f"[Mitigation] Generated {len(mitigations)} strategies for {risk_id}")
            except Exception as e:
                logger.error(f"[Mitigation] Error generating mitigations for {risk_id}: {e}", exc_info=True)
                risk["mitigations"] = []
        
        # Empty mitigations for remaining risks
        if len(risks) > max_risks:
            logger.debug(f"[Mitigation] Skipping mitigations for {len(risks) - max_risks} lower-priority risks")
            for risk in risks[max_risks:]:
                risk["mitigations"] = []
        
        total_mitigations = sum(len(r.get("mitigations", [])) for r in risks)
        logger.info(f"[Mitigation] Mitigation generation complete: {total_mitigations} total strategies across {len(risks)} risks")
        
        return risks
    
    def generate_recommendations(
        self,
        risks: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate categorized action recommendations.
        
        Args:
            risks: List of analyzed risks
            
        Returns:
            Dictionary with immediate, short_term, and long_term actions
        """
        recommendations = {
            "immediate_actions": [],
            "short_term_actions": [],
            "long_term_actions": []
        }
        
        for risk in risks:
            risk_id = risk.get("risk_id")
            priority = risk.get("priority", "MEDIUM")
            timeline = risk.get("timeline_days", 30)
            category = risk.get("category", "")
            
            # Categorize based on priority and timeline
            if priority == "CRITICAL" or timeline <= 7:
                recommendations["immediate_actions"].append({
                    "action": f"Address {category}: {risk.get('impact', 'Risk identified')}",
                    "priority": priority,
                    "related_risks": [risk_id]
                })
            elif priority == "HIGH" or timeline <= 21:
                recommendations["short_term_actions"].append({
                    "action": f"Monitor and plan for {category}",
                    "priority": priority,
                    "related_risks": [risk_id]
                })
            else:
                recommendations["long_term_actions"].append({
                    "action": f"Prepare contingency for {category}",
                    "priority": priority,
                    "related_risks": [risk_id]
                })
        
        # Limit recommendations
        recommendations["immediate_actions"] = recommendations["immediate_actions"][:5]
        recommendations["short_term_actions"] = recommendations["short_term_actions"][:5]
        recommendations["long_term_actions"] = recommendations["long_term_actions"][:5]
        
        return recommendations
    
    def run_full_analysis(
        self,
        forecast_horizon: int = 45,
        modules: Optional[List[str]] = None,
        risk_threshold: int = 50,
        include_mitigations: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete supply chain analysis.
        
        Args:
            forecast_horizon: Days to forecast
            modules: Modules to analyze (all if None)
            risk_threshold: Minimum risk score
            include_mitigations: Whether to include LLM mitigations
            
        Returns:
            Complete analysis response
        """
        analysis_id = generate_analysis_id()
        timestamp = format_timestamp()
        
        logger.info(f"[Analysis] ========================================")
        logger.info(f"[Analysis] Starting analysis {analysis_id}")
        logger.info(f"[Analysis] Parameters: horizon={forecast_horizon} days, modules={modules}, "
                   f"risk_threshold={risk_threshold}, mitigations={'enabled' if include_mitigations else 'disabled'}")
        logger.info(f"[Analysis] ========================================")
        
        # Default to all modules
        if modules is None:
            modules = ["suppliers", "manufacturing", "inventory", "demand", "transportation", "external"]
        
        # Run forecasts
        logger.info(f"[Forecast] ===== Starting forecast generation for {len(modules)} modules =====")
        forecasts = self.run_forecasts(forecast_horizon, modules)
        
        # Log forecast summary
        total_forecasts = sum(len(f) for f in forecasts.values())
        logger.info(f"[Forecast] ===== Forecast generation complete: {total_forecasts} total forecasts =====")
        for module, module_forecasts in forecasts.items():
            if module_forecasts:
                logger.info(f"[Forecast]   {module}: {len(module_forecasts)} forecasts")
        
        # Analyze risks
        logger.info(f"[Risk] ===== Starting risk analysis (threshold={risk_threshold}) =====")
        risks = self.analyze_risks(forecasts, forecast_horizon, risk_threshold)
        logger.info(f"[Risk] ===== Risk analysis complete: {len(risks)} risks identified =====")
        
        # Add mitigations
        if include_mitigations:
            logger.info(f"[Mitigation] ===== Generating mitigations for {min(len(risks), 10)} top risks =====")
        risks = self.add_mitigations(risks, include_mitigations)
        if include_mitigations:
            total_mitigations = sum(len(r.get("mitigations", [])) for r in risks)
            logger.info(f"[Mitigation] ===== Mitigation generation complete: {total_mitigations} strategies generated =====")
        
        # Generate summary
        logger.debug(f"[Summary] Generating analysis summary for {len(risks)} risks")
        summary = self.risk_analyzer.generate_summary(risks)
        logger.info(f"[Summary] Analysis summary: {summary['total_risks']} total risks "
                   f"(Critical={summary['critical_risks']}, High={summary['high_risks']}, "
                   f"Medium={summary['medium_risks']}, Low={summary['low_risks']})")
        
        # Generate recommendations
        logger.debug(f"[Recommendations] Generating action recommendations")
        recommendations = self.generate_recommendations(risks)
        total_recommendations = (len(recommendations.get('immediate_actions', [])) +
                                len(recommendations.get('short_term_actions', [])) +
                                len(recommendations.get('long_term_actions', [])))
        logger.info(f"[Recommendations] Generated {total_recommendations} recommendations "
                   f"(Immediate={len(recommendations.get('immediate_actions', []))}, "
                   f"Short-term={len(recommendations.get('short_term_actions', []))}, "
                   f"Long-term={len(recommendations.get('long_term_actions', []))})")
        
        # Include forecast data for frontend charts
        # Note: This includes the full forecast_data array with all daily predictions
        clean_forecasts = {}
        for module, module_forecasts in forecasts.items():
            clean_forecasts[module] = []
            for f in module_forecasts:
                # Keep all forecast data including forecast_data array
                # This contains predictions for each day (30-60 days based on user input)
                clean_f = f.copy()
                # Ensure forecast_data is properly formatted
                if "forecast_data" in clean_f and clean_f["forecast_data"]:
                    # Convert DataFrame to list of dicts if needed
                    if isinstance(clean_f["forecast_data"], pd.DataFrame):
                        clean_f["forecast_data"] = clean_f["forecast_data"].to_dict("records")
                    # Add forecast_points count for reference
                    clean_f["forecast_points"] = len(clean_f["forecast_data"])
                clean_forecasts[module].append(clean_f)
        
        result = {
            "analysis_id": analysis_id,
            "timestamp": timestamp,
            "forecast_horizon": forecast_horizon,
            "summary": summary,
            "forecasts": clean_forecasts,
            "risks": risks,
            "recommendations": recommendations
        }
        
        # Cache result
        self._analysis_cache[analysis_id] = result
        
        logger.info(f"[Analysis] ========================================")
        logger.info(f"[Analysis] Analysis {analysis_id} COMPLETED")
        logger.info(f"[Analysis] Summary: {summary['total_risks']} risks, {total_forecasts} forecasts, "
                   f"{total_recommendations} recommendations")
        logger.info(f"[Analysis] ========================================")
        
        return result
    
    def get_cached_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a cached analysis result."""
        return self._analysis_cache.get(analysis_id)
    
    def get_entities(self) -> Dict[str, Any]:
        """Get all available entities."""
        return self.data_loader.get_entities()
    
    def check_health(self) -> Dict[str, Any]:
        """Check service health."""
        data_status = self.data_loader.check_data_availability()
        return {
            "data_status": data_status,
            "all_data_available": all(data_status.values())
        }

