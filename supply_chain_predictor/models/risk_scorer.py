"""
Risk scoring algorithms for supply chain risk assessment.
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import RISK_THRESHOLDS, RISK_PRIORITY_THRESHOLDS
from utils.helpers import classify_risk_priority, safe_division, clamp

logger = logging.getLogger(__name__)


class RiskScorer:
    """
    Risk scoring class for calculating composite risk scores.
    
    Implements the formula:
    risk_score = (impact_severity * probability * urgency) / mitigation_readiness
    
    All components are normalized to 0-100 scale.
    """
    
    def __init__(self):
        """Initialize the RiskScorer."""
        self.thresholds = RISK_THRESHOLDS
        logger.info("RiskScorer initialized")
    
    def calculate_composite_score(
        self,
        impact_severity: float,
        probability: float,
        urgency: float,
        mitigation_readiness: float = 1.0
    ) -> float:
        """
        Calculate composite risk score.
        
        Args:
            impact_severity: Impact severity score (0-100)
            probability: Probability score (0-1)
            urgency: Urgency score based on timeline (0-100)
            mitigation_readiness: Mitigation readiness factor (0.1-1.0, higher = more ready)
            
        Returns:
            Risk score (0-100)
        """
        # Normalize inputs
        impact_severity = clamp(impact_severity, 0, 100)
        probability = clamp(probability, 0, 1)
        urgency = clamp(urgency, 0, 100)
        mitigation_readiness = clamp(mitigation_readiness, 0.1, 1.0)
        
        # Calculate raw score
        # Weight: impact 40%, probability 30%, urgency 30%
        raw_score = (
            (impact_severity * 0.4) +
            (probability * 100 * 0.3) +
            (urgency * 0.3)
        )
        
        # Adjust by mitigation readiness
        adjusted_score = raw_score / mitigation_readiness
        
        # Clamp to 0-100
        return clamp(adjusted_score, 0, 100)
    
    def calculate_supplier_risk_score(
        self,
        forecasted_lead_time: float,
        historical_avg_lead_time: float,
        confidence_interval_width: float,
        timeline_days: int,
        on_time_delivery_rate: float = 0.9
    ) -> Dict[str, Any]:
        """
        Calculate risk score for supplier delays.
        
        Args:
            forecasted_lead_time: Forecasted lead time in days
            historical_avg_lead_time: Historical average lead time
            confidence_interval_width: Width of forecast confidence interval
            timeline_days: Days until potential disruption
            on_time_delivery_rate: Historical on-time delivery rate
            
        Returns:
            Dictionary with risk score and components
        """
        threshold_multiplier = self.thresholds.get("supplier_lead_time_multiplier", 1.2)
        
        # Calculate lead time increase
        increase_ratio = safe_division(forecasted_lead_time, historical_avg_lead_time, 1.0)
        risk_detected = increase_ratio > threshold_multiplier
        
        if not risk_detected:
            return {
                "risk_detected": False,
                "risk_score": 0,
                "priority": "LOW",
                "probability": 0,
                "impact_severity": 0
            }
        
        # Calculate probability based on confidence interval
        # Narrower interval = higher confidence = higher probability
        base_probability = 0.5 + (0.5 * (1 - min(confidence_interval_width / forecasted_lead_time, 1)))
        probability = base_probability * (1 + (1 - on_time_delivery_rate))
        probability = clamp(probability, 0, 1)
        
        # Calculate impact severity based on increase magnitude
        impact_severity = min((increase_ratio - 1) * 100 * 2, 100)  # 50% increase = 100 severity
        
        # Calculate urgency based on timeline
        urgency = max(100 - timeline_days, 0)  # More urgent if sooner
        
        # Calculate readiness (lower on-time rate = less ready)
        mitigation_readiness = max(on_time_delivery_rate, 0.1)
        
        risk_score = self.calculate_composite_score(
            impact_severity, probability, urgency, mitigation_readiness
        )
        
        return {
            "risk_detected": True,
            "risk_score": round(risk_score, 2),
            "priority": classify_risk_priority(risk_score),
            "probability": round(probability, 2),
            "impact_severity": round(impact_severity, 2),
            "urgency": round(urgency, 2),
            "increase_ratio": round(increase_ratio, 2),
            "forecasted_metrics": {
                "lead_time_forecast": round(forecasted_lead_time, 2),
                "baseline_lead_time": round(historical_avg_lead_time, 2),
                "increase_percentage": round((increase_ratio - 1) * 100, 2)
            }
        }
    
    def calculate_production_risk_score(
        self,
        forecasted_utilization: float,
        forecasted_downtime: float,
        historical_downtime: float,
        timeline_days: int
    ) -> Dict[str, Any]:
        """
        Calculate risk score for production delays/bottlenecks.
        
        Args:
            forecasted_utilization: Forecasted capacity utilization (0-1)
            forecasted_downtime: Forecasted downtime hours
            historical_downtime: Historical average downtime hours
            timeline_days: Days until potential disruption
            
        Returns:
            Dictionary with risk score and components
        """
        utilization_threshold = self.thresholds.get("capacity_utilization_threshold", 0.95)
        downtime_threshold = self.thresholds.get("downtime_increase_threshold", 0.2)
        
        # Check for bottleneck risk
        bottleneck_risk = forecasted_utilization > utilization_threshold
        
        # Check for downtime increase
        downtime_increase = safe_division(
            forecasted_downtime - historical_downtime,
            historical_downtime,
            0
        )
        downtime_risk = downtime_increase > downtime_threshold
        
        if not (bottleneck_risk or downtime_risk):
            return {
                "risk_detected": False,
                "risk_score": 0,
                "priority": "LOW",
                "probability": 0,
                "impact_severity": 0
            }
        
        # Calculate probability
        probability = 0.5
        if bottleneck_risk:
            probability += 0.25 * (forecasted_utilization - utilization_threshold) / (1 - utilization_threshold)
        if downtime_risk:
            probability += 0.25 * min(downtime_increase / 0.5, 1)
        probability = clamp(probability, 0, 1)
        
        # Calculate impact severity
        impact_severity = 0
        if bottleneck_risk:
            impact_severity += 50 * ((forecasted_utilization - utilization_threshold) / (1 - utilization_threshold))
        if downtime_risk:
            impact_severity += 50 * min(downtime_increase, 1)
        impact_severity = clamp(impact_severity, 0, 100)
        
        # Urgency
        urgency = max(100 - timeline_days, 0)
        
        risk_score = self.calculate_composite_score(
            impact_severity, probability, urgency, 0.7
        )
        
        return {
            "risk_detected": True,
            "risk_score": round(risk_score, 2),
            "priority": classify_risk_priority(risk_score),
            "probability": round(probability, 2),
            "impact_severity": round(impact_severity, 2),
            "urgency": round(urgency, 2),
            "bottleneck_risk": bottleneck_risk,
            "downtime_risk": downtime_risk,
            "forecasted_metrics": {
                "capacity_utilization": round(forecasted_utilization, 4),
                "downtime_hours": round(forecasted_downtime, 2),
                "downtime_increase_pct": round(downtime_increase * 100, 2)
            }
        }
    
    def calculate_inventory_risk_score(
        self,
        forecasted_inventory: float,
        safety_stock: float,
        forecasted_demand_upper: float,
        inventory_lower_bound: float,
        timeline_days: int
    ) -> Dict[str, Any]:
        """
        Calculate risk score for stock shortages.
        
        Args:
            forecasted_inventory: Forecasted average inventory level
            safety_stock: Safety stock level
            forecasted_demand_upper: Upper bound of demand forecast
            inventory_lower_bound: Lower bound of inventory forecast
            timeline_days: Days until potential disruption
            
        Returns:
            Dictionary with risk score and components
        """
        # Check for shortage risk
        shortage_risk = forecasted_inventory < safety_stock
        
        # Cross-check with demand
        high_demand_risk = forecasted_demand_upper > inventory_lower_bound
        
        if not (shortage_risk or high_demand_risk):
            return {
                "risk_detected": False,
                "risk_score": 0,
                "priority": "LOW",
                "probability": 0,
                "impact_severity": 0
            }
        
        # Calculate probability
        probability = 0.3
        if shortage_risk:
            shortage_severity = safe_division(safety_stock - forecasted_inventory, safety_stock, 0)
            probability += 0.4 * min(shortage_severity, 1)
        if high_demand_risk:
            demand_gap = safe_division(
                forecasted_demand_upper - inventory_lower_bound,
                inventory_lower_bound,
                0
            )
            probability += 0.3 * min(demand_gap, 1)
        probability = clamp(probability, 0, 1)
        
        # Calculate impact severity
        impact_severity = 0
        if shortage_risk:
            shortage_pct = safe_division(safety_stock - forecasted_inventory, safety_stock, 0)
            impact_severity += 60 * min(shortage_pct, 1)
        if high_demand_risk:
            impact_severity += 40
        impact_severity = clamp(impact_severity, 0, 100)
        
        # Urgency
        urgency = max(100 - timeline_days, 0)
        
        risk_score = self.calculate_composite_score(
            impact_severity, probability, urgency, 0.6
        )
        
        return {
            "risk_detected": True,
            "risk_score": round(risk_score, 2),
            "priority": classify_risk_priority(risk_score),
            "probability": round(probability, 2),
            "impact_severity": round(impact_severity, 2),
            "urgency": round(urgency, 2),
            "shortage_risk": shortage_risk,
            "demand_exceeds_supply": high_demand_risk,
            "forecasted_metrics": {
                "forecasted_inventory": round(forecasted_inventory, 2),
                "safety_stock": round(safety_stock, 2),
                "inventory_gap": round(safety_stock - forecasted_inventory, 2)
            }
        }
    
    def calculate_demand_volatility_score(
        self,
        yhat: float,
        yhat_upper: float,
        yhat_lower: float,
        timeline_days: int
    ) -> Dict[str, Any]:
        """
        Calculate risk score for demand volatility.
        
        Args:
            yhat: Forecasted demand
            yhat_upper: Upper bound of forecast
            yhat_lower: Lower bound of forecast
            timeline_days: Days until potential issue
            
        Returns:
            Dictionary with risk score and components
        """
        threshold = self.thresholds.get("demand_volatility_threshold", 0.3)
        
        # Calculate volatility
        interval_width = yhat_upper - yhat_lower
        volatility = safe_division(interval_width, yhat, 0)
        
        risk_detected = volatility > threshold
        
        if not risk_detected:
            return {
                "risk_detected": False,
                "risk_score": 0,
                "priority": "LOW",
                "probability": 0,
                "impact_severity": 0
            }
        
        # Probability increases with volatility
        probability = min((volatility - threshold) / threshold + 0.5, 1)
        
        # Impact severity
        impact_severity = min(volatility * 100, 100)
        
        # Urgency
        urgency = max(100 - timeline_days, 0)
        
        risk_score = self.calculate_composite_score(
            impact_severity, probability, urgency, 0.8
        )
        
        return {
            "risk_detected": True,
            "risk_score": round(risk_score, 2),
            "priority": classify_risk_priority(risk_score),
            "probability": round(probability, 2),
            "impact_severity": round(impact_severity, 2),
            "urgency": round(urgency, 2),
            "volatility": round(volatility * 100, 2),
            "forecasted_metrics": {
                "demand_forecast": round(yhat, 2),
                "upper_bound": round(yhat_upper, 2),
                "lower_bound": round(yhat_lower, 2),
                "volatility_percentage": round(volatility * 100, 2)
            }
        }
    
    def calculate_transportation_risk_score(
        self,
        forecasted_transit_time: float,
        baseline_transit_time: float,
        timeline_days: int,
        on_time_rate: float = 0.9
    ) -> Dict[str, Any]:
        """
        Calculate risk score for transportation delays.
        
        Args:
            forecasted_transit_time: Forecasted transit time
            baseline_transit_time: Historical baseline transit time
            timeline_days: Days until shipment
            on_time_rate: Historical on-time delivery rate
            
        Returns:
            Dictionary with risk score and components
        """
        threshold = self.thresholds.get("transit_time_multiplier", 1.3)
        
        increase_ratio = safe_division(forecasted_transit_time, baseline_transit_time, 1.0)
        risk_detected = increase_ratio > threshold
        
        if not risk_detected:
            return {
                "risk_detected": False,
                "risk_score": 0,
                "priority": "LOW",
                "probability": 0,
                "impact_severity": 0
            }
        
        # Probability
        probability = 0.5 + 0.5 * (1 - on_time_rate)
        probability = clamp(probability, 0, 1)
        
        # Impact severity
        delay_pct = (increase_ratio - 1) * 100
        impact_severity = min(delay_pct * 2, 100)
        
        # Urgency
        urgency = max(100 - timeline_days, 0)
        
        risk_score = self.calculate_composite_score(
            impact_severity, probability, urgency, on_time_rate
        )
        
        return {
            "risk_detected": True,
            "risk_score": round(risk_score, 2),
            "priority": classify_risk_priority(risk_score),
            "probability": round(probability, 2),
            "impact_severity": round(impact_severity, 2),
            "urgency": round(urgency, 2),
            "forecasted_metrics": {
                "transit_time_forecast": round(forecasted_transit_time, 2),
                "baseline_transit_time": round(baseline_transit_time, 2),
                "delay_percentage": round((increase_ratio - 1) * 100, 2)
            }
        }
    
    def calculate_external_factor_risk_score(
        self,
        factor_type: str,
        forecasted_value: float,
        historical_value: float,
        timeline_days: int
    ) -> Dict[str, Any]:
        """
        Calculate risk score for external factors.
        
        Args:
            factor_type: Type of external factor
            forecasted_value: Forecasted value
            historical_value: Historical average value
            timeline_days: Days until impact
            
        Returns:
            Dictionary with risk score and components
        """
        risk_detected = False
        probability = 0
        impact_severity = 0
        sub_category = factor_type
        
        if factor_type == "weather_severity_index":
            threshold = self.thresholds.get("weather_severity_threshold", 7)
            risk_detected = forecasted_value > threshold
            if risk_detected:
                probability = min((forecasted_value - threshold) / 3, 1)
                impact_severity = min((forecasted_value / 10) * 100, 100)
                sub_category = "Weather"
                
        elif factor_type == "tariff_rate":
            threshold = self.thresholds.get("tariff_increase_threshold", 0.1)
            increase = safe_division(forecasted_value - historical_value, historical_value, 0)
            risk_detected = increase > threshold
            if risk_detected:
                probability = min(increase / 0.3, 1)
                impact_severity = min(increase * 200, 100)
                sub_category = "Trade/Tariffs"
                
        elif factor_type == "port_congestion_index":
            threshold = self.thresholds.get("port_congestion_threshold", 30)
            risk_detected = forecasted_value > threshold
            if risk_detected:
                probability = min((forecasted_value - threshold) / 20, 1)
                impact_severity = min((forecasted_value / 50) * 100, 100)
                sub_category = "Port Congestion"
                
        elif factor_type == "fuel_price_usd":
            increase = safe_division(forecasted_value - historical_value, historical_value, 0)
            risk_detected = increase > 0.15  # 15% increase
            if risk_detected:
                probability = min(increase / 0.3, 1)
                impact_severity = min(increase * 150, 100)
                sub_category = "Fuel Costs"
                
        elif factor_type == "geopolitical_risk_index":
            risk_detected = forecasted_value > 7
            if risk_detected:
                probability = min(forecasted_value / 10, 1)
                impact_severity = min(forecasted_value * 10, 100)
                sub_category = "Geopolitical"
        
        if not risk_detected:
            return {
                "risk_detected": False,
                "risk_score": 0,
                "priority": "LOW",
                "probability": 0,
                "impact_severity": 0
            }
        
        probability = clamp(probability, 0, 1)
        impact_severity = clamp(impact_severity, 0, 100)
        urgency = max(100 - timeline_days, 0)
        
        risk_score = self.calculate_composite_score(
            impact_severity, probability, urgency, 0.5
        )
        
        return {
            "risk_detected": True,
            "risk_score": round(risk_score, 2),
            "priority": classify_risk_priority(risk_score),
            "probability": round(probability, 2),
            "impact_severity": round(impact_severity, 2),
            "urgency": round(urgency, 2),
            "sub_category": sub_category,
            "forecasted_metrics": {
                "forecasted_value": round(forecasted_value, 2),
                "historical_value": round(historical_value, 2),
                "factor_type": factor_type
            }
        }


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))

