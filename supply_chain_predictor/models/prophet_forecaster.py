"""
Prophet-based forecasting module for supply chain metrics.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

# Prophet import with suppressed logging
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from prophet import Prophet

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PROPHET_CONFIG, FORECAST_CONFIG

logger = logging.getLogger(__name__)


class ProphetForecaster:
    """
    Prophet-based forecasting class for supply chain metrics.
    
    Provides forecasting methods for:
    - Supplier lead times
    - Production capacity
    - Inventory levels
    - Customer demand
    - Transit times
    - External factors
    """
    
    def __init__(self):
        """Initialize the ProphetForecaster with model cache."""
        self._model_cache: Dict[str, Prophet] = {}
        self._forecast_cache: Dict[str, pd.DataFrame] = {}
        logger.info("ProphetForecaster initialized")
    
    def _create_prophet_model(
        self,
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
        add_regressors: Optional[List[str]] = None
    ) -> Prophet:
        """
        Create a configured Prophet model.
        
        Args:
            yearly_seasonality: Enable yearly seasonality
            weekly_seasonality: Enable weekly seasonality
            daily_seasonality: Enable daily seasonality
            add_regressors: List of regressor column names
            
        Returns:
            Configured Prophet model
        """
        model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            seasonality_mode=PROPHET_CONFIG.get("seasonality_mode", "multiplicative"),
            changepoint_prior_scale=PROPHET_CONFIG.get("changepoint_prior_scale", 0.05),
            interval_width=PROPHET_CONFIG.get("interval_width", 0.95),
        )
        
        if add_regressors:
            for regressor in add_regressors:
                model.add_regressor(regressor)
        
        return model
    
    def _prepare_prophet_data(
        self,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        regressor_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Prepare data in Prophet format (ds, y columns).
        
        Args:
            df: Input DataFrame
            date_col: Name of date column
            target_col: Name of target column
            regressor_cols: Optional list of regressor columns
            
        Returns:
            DataFrame in Prophet format
        """
        prophet_df = pd.DataFrame({
            "ds": pd.to_datetime(df[date_col]),
            "y": df[target_col].astype(float)
        })
        
        if regressor_cols:
            for col in regressor_cols:
                if col in df.columns:
                    prophet_df[col] = df[col].astype(float)
        
        # Remove any NaN values
        prophet_df = prophet_df.dropna()
        
        return prophet_df
    
    def _validate_data(self, df: pd.DataFrame, min_points: int = None) -> bool:
        """
        Validate data has sufficient points for forecasting.
        
        Args:
            df: DataFrame to validate
            min_points: Minimum required data points
            
        Returns:
            True if valid
            
        Raises:
            ValueError if insufficient data
        """
        min_points = min_points or FORECAST_CONFIG.get("min_data_points", 30)
        if len(df) < min_points:
            raise ValueError(
                f"Insufficient data points: {len(df)} < {min_points} required"
            )
        return True
    
    def _generate_cache_key(self, *args) -> str:
        """Generate a cache key from arguments."""
        return "_".join(str(arg) for arg in args)
    
    def _fit_and_forecast(
        self,
        df: pd.DataFrame,
        horizon_days: int,
        model: Prophet,
        cache_key: Optional[str] = None,
        future_regressors: Optional[pd.DataFrame] = None,
        entity_context: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fit Prophet model and generate forecast.
        
        Args:
            df: Training data in Prophet format
            horizon_days: Number of days to forecast
            model: Prophet model instance
            cache_key: Optional cache key for model
            future_regressors: Optional DataFrame with future regressor values
            entity_context: Optional context string for logging (e.g., "SUP001-COMP_A")
            
        Returns:
            Forecast DataFrame
        """
        try:
            # Suppress Prophet output
            import logging as prophet_logging
            prophet_logging.getLogger('prophet').setLevel(prophet_logging.WARNING)
            prophet_logging.getLogger('cmdstanpy').setLevel(prophet_logging.WARNING)
            
            data_points = len(df)
            first_date = df['ds'].min()
            last_date = df['ds'].max()
            
            if entity_context:
                logger.info(f"[Prophet] Training model for {entity_context}: {data_points} data points, "
                          f"date range {first_date.date()} to {last_date.date()}, horizon={horizon_days} days")
            
            # Fit model
            model.fit(df)
            
            if entity_context:
                logger.debug(f"[Prophet] Model trained successfully for {entity_context}")
            
            # Cache model if key provided
            if cache_key:
                self._model_cache[cache_key] = model
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=horizon_days, freq='D')
            
            # Add regressors to future if provided
            if future_regressors is not None:
                for col in future_regressors.columns:
                    if col != 'ds':
                        # For future dates, use last known values or provided values
                        future = future.merge(
                            future_regressors[['ds', col]], 
                            on='ds', 
                            how='left'
                        )
                        # Forward fill any missing values
                        future[col] = future[col].ffill().bfill()
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Return only future dates
            forecast = forecast[forecast['ds'] > last_date]
            forecast_points = len(forecast)
            
            if entity_context:
                avg_pred = forecast['yhat'].mean()
                avg_lower = forecast['yhat_lower'].mean()
                avg_upper = forecast['yhat_upper'].mean()
                logger.info(f"[Prophet] Forecast generated for {entity_context}: {forecast_points} points, "
                          f"avg_pred={avg_pred:.2f}, range=[{avg_lower:.2f}, {avg_upper:.2f}]")
            
            return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend']]
            
        except Exception as e:
            if entity_context:
                logger.error(f"[Prophet] Forecast failed for {entity_context}: {e}", exc_info=True)
            else:
                logger.error(f"[Prophet] Forecast failed: {e}", exc_info=True)
            raise
    
    def forecast_supplier_leadtime(
        self,
        df: pd.DataFrame,
        supplier_id: str,
        component_id: str,
        horizon_days: int
    ) -> Dict[str, Any]:
        """
        Forecast supplier lead time.
        
        Args:
            df: Supplier lead time DataFrame
            supplier_id: Supplier identifier
            component_id: Component identifier
            horizon_days: Forecast horizon in days
            
        Returns:
            Dictionary with forecast results
        """
        entity_context = f"{supplier_id}-{component_id}"
        cache_key = self._generate_cache_key("supplier", supplier_id, component_id)
        
        # Filter data
        filtered = df[
            (df["supplier_id"] == supplier_id) & 
            (df["component_id"] == component_id)
        ].copy()
        
        if len(filtered) < FORECAST_CONFIG.get("min_data_points", 30):
            logger.warning(f"[Prophet] Insufficient data for {entity_context}: {len(filtered)} points (need {FORECAST_CONFIG.get('min_data_points', 30)})")
            return self._create_empty_forecast_result(supplier_id, "lead_time_days")
        
        # Prepare data
        prophet_df = self._prepare_prophet_data(filtered, "date", "lead_time_days")
        
        # Create and fit model
        model = self._create_prophet_model(
            yearly_seasonality=True,
            weekly_seasonality=False
        )
        
        # Generate forecast
        forecast = self._fit_and_forecast(prophet_df, horizon_days, model, cache_key, entity_context=entity_context)
        
        # Calculate statistics
        historical_avg = prophet_df["y"].mean()
        forecasted_avg = forecast["yhat"].mean()
        change_pct = (forecasted_avg - historical_avg) / historical_avg if historical_avg > 0 else 0
        
        logger.info(f"[Prophet] Supplier forecast complete for {entity_context}: "
                   f"historical={historical_avg:.2f} days, forecasted={forecasted_avg:.2f} days, "
                   f"change={change_pct*100:+.1f}%")
        
        return {
            "entity_id": supplier_id,
            "entity_name": filtered["supplier_name"].iloc[0] if "supplier_name" in filtered.columns else None,
            "metric": "lead_time_days",
            "historical_avg": round(historical_avg, 2),
            "forecasted_avg": round(forecasted_avg, 2),
            "change_percentage": round(change_pct * 100, 2),
            "forecast_data": forecast.to_dict("records"),
            "component_id": component_id
        }
    
    def forecast_production_capacity(
        self,
        df: pd.DataFrame,
        plant_id: str,
        sku: str,
        horizon_days: int
    ) -> Dict[str, Any]:
        """
        Forecast production capacity utilization and downtime.
        
        Args:
            df: Manufacturing production DataFrame
            plant_id: Plant identifier
            sku: SKU identifier
            horizon_days: Forecast horizon in days
            
        Returns:
            Dictionary with forecast results
        """
        entity_context = f"{plant_id}-{sku}"
        cache_key = self._generate_cache_key("production", plant_id, sku)
        
        # Filter data
        filtered = df[
            (df["plant_id"] == plant_id) & 
            (df["sku"] == sku)
        ].copy()
        
        if len(filtered) < FORECAST_CONFIG.get("min_data_points", 30):
            logger.warning(f"[Prophet] Insufficient data for {entity_context}: {len(filtered)} points")
            return self._create_empty_forecast_result(plant_id, "capacity_utilization")
        
        # Forecast capacity utilization
        prophet_df = self._prepare_prophet_data(filtered, "date", "capacity_utilization")
        model = self._create_prophet_model(yearly_seasonality=True, weekly_seasonality=True)
        capacity_forecast = self._fit_and_forecast(prophet_df, horizon_days, model, f"{cache_key}_capacity", 
                                                   entity_context=f"{entity_context}-capacity")
        
        # Forecast downtime
        prophet_df_downtime = self._prepare_prophet_data(filtered, "date", "downtime_hours")
        model_downtime = self._create_prophet_model(yearly_seasonality=True, weekly_seasonality=True)
        downtime_forecast = self._fit_and_forecast(prophet_df_downtime, horizon_days, model_downtime, 
                                                   f"{cache_key}_downtime", entity_context=f"{entity_context}-downtime")
        
        # Calculate statistics
        historical_capacity = filtered["capacity_utilization"].mean()
        forecasted_capacity = capacity_forecast["yhat"].mean()
        historical_downtime = filtered["downtime_hours"].mean()
        forecasted_downtime = downtime_forecast["yhat"].mean()
        capacity_change = (forecasted_capacity - historical_capacity) / historical_capacity * 100 if historical_capacity > 0 else 0
        
        logger.info(f"[Prophet] Manufacturing forecast complete for {entity_context}: "
                   f"capacity={historical_capacity:.3f}→{forecasted_capacity:.3f} ({capacity_change:+.1f}%), "
                   f"downtime={historical_downtime:.1f}→{forecasted_downtime:.1f} hours")
        
        return {
            "entity_id": plant_id,
            "entity_name": filtered["plant_name"].iloc[0] if "plant_name" in filtered.columns else None,
            "metric": "capacity_utilization",
            "historical_avg": round(historical_capacity, 4),
            "forecasted_avg": round(forecasted_capacity, 4),
            "change_percentage": round(capacity_change, 2),
            "forecast_data": capacity_forecast.to_dict("records"),
            "sku": sku,
            "downtime_forecast": {
                "historical_avg": round(historical_downtime, 2),
                "forecasted_avg": round(forecasted_downtime, 2),
                "forecast_data": downtime_forecast.to_dict("records")
            }
        }
    
    def forecast_inventory_levels(
        self,
        df: pd.DataFrame,
        warehouse_id: str,
        sku: str,
        horizon_days: int
    ) -> Dict[str, Any]:
        """
        Forecast inventory levels.
        
        Args:
            df: Inventory levels DataFrame
            warehouse_id: Warehouse identifier
            sku: SKU identifier
            horizon_days: Forecast horizon in days
            
        Returns:
            Dictionary with forecast results
        """
        cache_key = self._generate_cache_key("inventory", warehouse_id, sku)
        
        # Filter data
        filtered = df[
            (df["warehouse_id"] == warehouse_id) & 
            (df["sku"] == sku)
        ].copy()
        
        entity_context = f"{warehouse_id}-{sku}"
        
        if len(filtered) < FORECAST_CONFIG.get("min_data_points", 30):
            logger.warning(f"[Prophet] Insufficient data for {entity_context}: {len(filtered)} points")
            return self._create_empty_forecast_result(warehouse_id, "stock_on_hand")
        
        # Prepare data
        prophet_df = self._prepare_prophet_data(filtered, "date", "stock_on_hand")
        
        # Create and fit model
        model = self._create_prophet_model(
            yearly_seasonality=True,
            weekly_seasonality=True
        )
        
        # Generate forecast
        forecast = self._fit_and_forecast(prophet_df, horizon_days, model, cache_key, entity_context=entity_context)
        
        # Get safety stock level
        safety_stock = filtered["safety_stock"].iloc[-1]
        
        # Calculate statistics
        historical_avg = prophet_df["y"].mean()
        forecasted_avg = forecast["yhat"].mean()
        min_forecasted = forecast["yhat_lower"].min()
        change_pct = (forecasted_avg - historical_avg) / historical_avg * 100 if historical_avg > 0 else 0
        stockout_risk = min_forecasted < safety_stock
        
        logger.info(f"[Prophet] Inventory forecast complete for {entity_context}: "
                   f"stock={historical_avg:.0f}→{forecasted_avg:.0f} ({change_pct:+.1f}%), "
                   f"safety_stock={safety_stock:.0f}, stockout_risk={'YES' if stockout_risk else 'NO'}")
        
        return {
            "entity_id": warehouse_id,
            "entity_name": filtered["warehouse_name"].iloc[0] if "warehouse_name" in filtered.columns else None,
            "metric": "stock_on_hand",
            "historical_avg": round(historical_avg, 2),
            "forecasted_avg": round(forecasted_avg, 2),
            "change_percentage": round(change_pct, 2),
            "forecast_data": forecast.to_dict("records"),
            "sku": sku,
            "safety_stock": safety_stock,
            "min_forecasted": round(min_forecasted, 2),
            "below_safety_stock": min_forecasted < safety_stock
        }
    
    def forecast_demand(
        self,
        df: pd.DataFrame,
        region: str,
        sku: str,
        horizon_days: int,
        include_promotions: bool = True
    ) -> Dict[str, Any]:
        """
        Forecast customer demand with optional promotional regressors.
        
        Args:
            df: Customer demand DataFrame
            region: Region identifier
            sku: SKU identifier
            horizon_days: Forecast horizon in days
            include_promotions: Whether to include promotional effects
            
        Returns:
            Dictionary with forecast results
        """
        cache_key = self._generate_cache_key("demand", region, sku, include_promotions)
        
        # Filter data
        filtered = df[
            (df["region"] == region) & 
            (df["sku"] == sku)
        ].copy()
        
        entity_context = f"{region}-{sku}"
        
        if len(filtered) < FORECAST_CONFIG.get("min_data_points", 30):
            logger.warning(f"[Prophet] Insufficient data for {entity_context}: {len(filtered)} points")
            return self._create_empty_forecast_result(region, "order_quantity")
        
        # Prepare data with promotional regressor if available
        regressors = ["is_promotional"] if include_promotions and "is_promotional" in filtered.columns else None
        prophet_df = self._prepare_prophet_data(
            filtered, "date", "order_quantity", regressors
        )
        
        # Create model with regressors
        model = self._create_prophet_model(
            yearly_seasonality=True,
            weekly_seasonality=True,
            add_regressors=regressors
        )
        
        # Prepare future regressors (assume no promotions in future by default)
        future_regressors = None
        if regressors:
            last_date = filtered["date"].max()
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=horizon_days,
                freq='D'
            )
            future_regressors = pd.DataFrame({
                'ds': future_dates,
                'is_promotional': 0  # Conservative assumption
            })
        
        # Generate forecast
        forecast = self._fit_and_forecast(
            prophet_df, horizon_days, model, cache_key, future_regressors, entity_context=entity_context
        )
        
        # Calculate statistics
        historical_avg = prophet_df["y"].mean()
        forecasted_avg = forecast["yhat"].mean()
        volatility = (forecast["yhat_upper"] - forecast["yhat_lower"]).mean() / forecasted_avg if forecasted_avg > 0 else 0
        change_pct = (forecasted_avg - historical_avg) / historical_avg * 100 if historical_avg > 0 else 0
        
        logger.info(f"[Prophet] Demand forecast complete for {entity_context}: "
                   f"demand={historical_avg:.0f}→{forecasted_avg:.0f} ({change_pct:+.1f}%), "
                   f"volatility={volatility*100:.1f}% {'[HIGH]' if volatility > 0.3 else ''}")
        
        return {
            "entity_id": region,
            "entity_name": region,
            "metric": "order_quantity",
            "historical_avg": round(historical_avg, 2),
            "forecasted_avg": round(forecasted_avg, 2),
            "change_percentage": round(change_pct, 2),
            "forecast_data": forecast.to_dict("records"),
            "sku": sku,
            "volatility": round(volatility * 100, 2),
            "high_volatility": volatility > 0.3
        }
    
    def forecast_transit_time(
        self,
        df: pd.DataFrame,
        route_id: str,
        horizon_days: int
    ) -> Dict[str, Any]:
        """
        Forecast transit times for a route.
        
        Args:
            df: Transportation data DataFrame
            route_id: Route identifier
            horizon_days: Forecast horizon in days
            
        Returns:
            Dictionary with forecast results
        """
        cache_key = self._generate_cache_key("transit", route_id)
        
        # Filter data
        filtered = df[df["route_id"] == route_id].copy()
        
        entity_context = route_id
        
        if len(filtered) < FORECAST_CONFIG.get("min_data_points", 30):
            logger.warning(f"[Prophet] Insufficient data for route {entity_context}: {len(filtered)} points")
            return self._create_empty_forecast_result(route_id, "transit_time_days")
        
        # Prepare data
        prophet_df = self._prepare_prophet_data(filtered, "date", "transit_time_days")
        
        # Create and fit model
        model = self._create_prophet_model(
            yearly_seasonality=True,
            weekly_seasonality=True
        )
        
        # Generate forecast
        forecast = self._fit_and_forecast(prophet_df, horizon_days, model, cache_key, entity_context=entity_context)
        
        # Calculate statistics
        historical_avg = prophet_df["y"].mean()
        forecasted_avg = forecast["yhat"].mean()
        max_forecasted = forecast["yhat_upper"].max()
        change_pct = (forecasted_avg - historical_avg) / historical_avg * 100 if historical_avg > 0 else 0
        delay_risk = forecasted_avg > historical_avg * 1.3
        
        route_name = f"{filtered['origin'].iloc[0]} → {filtered['destination'].iloc[0]}" if "origin" in filtered.columns else route_id
        logger.info(f"[Prophet] Transportation forecast complete for {route_name}: "
                   f"transit={historical_avg:.1f}→{forecasted_avg:.1f} days ({change_pct:+.1f}%), "
                   f"max={max_forecasted:.1f} days, delay_risk={'YES' if delay_risk else 'NO'}")
        
        return {
            "entity_id": route_id,
            "entity_name": route_name,
            "metric": "transit_time_days",
            "historical_avg": round(historical_avg, 2),
            "forecasted_avg": round(forecasted_avg, 2),
            "change_percentage": round(change_pct, 2),
            "forecast_data": forecast.to_dict("records"),
            "max_forecasted": round(max_forecasted, 2),
            "delay_risk": delay_risk
        }
    
    def forecast_external_factors(
        self,
        df: pd.DataFrame,
        region: str,
        factor_type: str,
        horizon_days: int
    ) -> Dict[str, Any]:
        """
        Forecast external factors (weather, tariffs, etc.).
        
        Args:
            df: External factors DataFrame
            region: Region identifier
            factor_type: Type of factor to forecast (e.g., 'weather_severity_index')
            horizon_days: Forecast horizon in days
            
        Returns:
            Dictionary with forecast results
        """
        cache_key = self._generate_cache_key("external", region, factor_type)
        
        # Valid factor types
        valid_factors = [
            "weather_severity_index", "tariff_rate", "fuel_price_usd",
            "port_congestion_index", "geopolitical_risk_index"
        ]
        
        if factor_type not in valid_factors:
            raise ValueError(f"Invalid factor_type: {factor_type}. Must be one of {valid_factors}")
        
        # Filter data
        filtered = df[df["region"] == region].copy()
        
        entity_context = f"{region}-{factor_type}"
        
        if len(filtered) < FORECAST_CONFIG.get("min_data_points", 30):
            logger.warning(f"[Prophet] Insufficient data for {entity_context}: {len(filtered)} points")
            return self._create_empty_forecast_result(region, factor_type)
        
        if factor_type not in filtered.columns:
            logger.warning(f"[Prophet] Factor {factor_type} not in data for {region}")
            return self._create_empty_forecast_result(region, factor_type)
        
        # Prepare data
        prophet_df = self._prepare_prophet_data(filtered, "date", factor_type)
        
        # Create and fit model
        model = self._create_prophet_model(
            yearly_seasonality=True,
            weekly_seasonality=False
        )
        
        # Generate forecast
        forecast = self._fit_and_forecast(prophet_df, horizon_days, model, cache_key, entity_context=entity_context)
        
        # Calculate statistics
        historical_avg = prophet_df["y"].mean()
        forecasted_avg = forecast["yhat"].mean()
        max_forecasted = forecast["yhat_upper"].max()
        change_pct = (forecasted_avg - historical_avg) / historical_avg * 100 if historical_avg > 0 else 0
        
        logger.info(f"[Prophet] External factor forecast complete for {entity_context}: "
                   f"value={historical_avg:.2f}→{forecasted_avg:.2f} ({change_pct:+.1f}%), max={max_forecasted:.2f}")
        
        return {
            "entity_id": region,
            "entity_name": region,
            "metric": factor_type,
            "historical_avg": round(historical_avg, 2),
            "forecasted_avg": round(forecasted_avg, 2),
            "change_percentage": round((forecasted_avg - historical_avg) / historical_avg * 100, 2) if historical_avg > 0 else 0,
            "forecast_data": forecast.to_dict("records"),
            "max_forecasted": round(max_forecasted, 2)
        }
    
    def _create_empty_forecast_result(
        self,
        entity_id: str,
        metric: str
    ) -> Dict[str, Any]:
        """Create an empty forecast result for insufficient data cases."""
        return {
            "entity_id": entity_id,
            "entity_name": None,
            "metric": metric,
            "historical_avg": 0,
            "forecasted_avg": 0,
            "change_percentage": 0,
            "forecast_data": [],
            "error": "Insufficient data for forecasting"
        }
    
    def clear_cache(self):
        """Clear model and forecast caches."""
        self._model_cache.clear()
        self._forecast_cache.clear()
        logger.info("Forecast caches cleared")

