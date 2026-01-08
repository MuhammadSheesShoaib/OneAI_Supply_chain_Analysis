"""
Utility helper functions for the Supply Chain Predictor.
"""
import uuid
from datetime import datetime
from typing import Optional

from config import RISK_PRIORITY_THRESHOLDS


def generate_risk_id() -> str:
    """Generate a unique risk identifier."""
    return f"R-{uuid.uuid4().hex[:8].upper()}"


def generate_analysis_id() -> str:
    """Generate a unique analysis identifier."""
    return f"A-{uuid.uuid4().hex[:12].upper()}"


def calculate_percentage_change(current: float, baseline: float) -> float:
    """
    Calculate the percentage change between current and baseline values.
    
    Args:
        current: Current value
        baseline: Baseline/historical value
        
    Returns:
        Percentage change as a decimal (e.g., 0.25 for 25% increase)
    """
    if baseline == 0:
        return 0.0 if current == 0 else float('inf')
    return (current - baseline) / baseline


def classify_risk_priority(risk_score: float) -> str:
    """
    Classify risk priority based on risk score.
    
    Args:
        risk_score: Risk score value (0-100)
        
    Returns:
        Priority classification: CRITICAL, HIGH, MEDIUM, or LOW
    """
    if risk_score >= RISK_PRIORITY_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    elif risk_score >= RISK_PRIORITY_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif risk_score >= RISK_PRIORITY_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: The numerator
        denominator: The denominator
        default: Default value if division is not possible
        
    Returns:
        Result of division or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime object to ISO format string.
    
    Args:
        dt: Datetime object (uses current time if None)
        
    Returns:
        ISO formatted timestamp string
    """
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between minimum and maximum bounds.
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def round_to_precision(value: float, precision: int = 2) -> float:
    """
    Round a value to specified decimal precision.
    
    Args:
        value: Value to round
        precision: Number of decimal places
        
    Returns:
        Rounded value
    """
    return round(value, precision)

