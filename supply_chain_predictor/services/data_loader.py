"""
Data Loader service for loading and preprocessing CSV data files.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_FILES

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Data loader class for loading and preprocessing supply chain CSV data.
    
    Handles all 6 data sources:
    - Supplier lead times
    - Manufacturing production
    - Inventory levels
    - Customer demand
    - Transportation data
    - External factors
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the DataLoader.
        
        Args:
            data_dir: Optional custom data directory path
        """
        self.data_files = DATA_FILES if data_dir is None else self._build_paths(data_dir)
        self._cache: Dict[str, pd.DataFrame] = {}
        logger.info("DataLoader initialized")
    
    def _build_paths(self, data_dir: Path) -> Dict[str, Path]:
        """Build file paths from custom data directory."""
        return {
            "supplier_lead_times": data_dir / "supplier_lead_time_data.csv",
            "manufacturing_production": data_dir / "manufacturing_production.csv",
            "inventory_levels": data_dir / "inventory_levels.csv",
            "customer_demand": data_dir / "customer_demand.csv",
            "transportation_data": data_dir / "transportation_data.csv",
            "external_factors": data_dir / "external_factors.csv",
        }
    
    def _validate_dataframe(self, df: pd.DataFrame, required_columns: List[str], name: str) -> bool:
        """
        Validate that a DataFrame has required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            name: Name of the data source for error messages
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns in {name}: {missing}")
        return True
    
    def _parse_dates(self, df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
        """
        Parse date column to datetime.
        
        Args:
            df: DataFrame with date column
            date_column: Name of the date column
            
        Returns:
            DataFrame with parsed dates
        """
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        # Remove rows with invalid dates
        invalid_dates = df[date_column].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Removed {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=[date_column])
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame, numeric_strategy: str = "median") -> pd.DataFrame:
        """
        Handle missing values in DataFrame.
        
        Args:
            df: DataFrame to clean
            numeric_strategy: Strategy for numeric columns ('mean', 'median', 'zero')
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Handle numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isna().any():
                if numeric_strategy == "median":
                    df[col] = df[col].fillna(df[col].median())
                elif numeric_strategy == "mean":
                    df[col] = df[col].fillna(df[col].mean())
                else:
                    df[col] = df[col].fillna(0)
        
        # Handle categorical columns - forward fill then backward fill
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].isna().any():
                df[col] = df[col].ffill().bfill()
        
        return df
    
    def _handle_outliers(
        self, 
        df: pd.DataFrame, 
        columns: List[str], 
        method: str = "iqr",
        threshold: float = 1.5
    ) -> pd.DataFrame:
        """
        Handle outliers in specified columns.
        
        Args:
            df: DataFrame to clean
            columns: Columns to check for outliers
            method: Method to use ('iqr' or 'zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            DataFrame with outliers handled
        """
        df = df.copy()
        
        for col in columns:
            if col not in df.columns:
                continue
                
            if method == "iqr":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                # Cap outliers instead of removing
                df[col] = df[col].clip(lower=lower, upper=upper)
            elif method == "zscore":
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    z_scores = np.abs((df[col] - mean) / std)
                    df.loc[z_scores > threshold, col] = df[col].median()
        
        return df
    
    def load_supplier_lead_times(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load and preprocess supplier lead time data.
        
        Columns: date, supplier_id, supplier_name, component_id, component_name,
                 lead_time_days, order_quantity, on_time_delivery, supplier_tier, supplier_region
        
        Returns:
            Preprocessed DataFrame
        """
        cache_key = "supplier_lead_times"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        try:
            df = pd.read_csv(self.data_files["supplier_lead_times"])
            
            required_cols = [
                "date", "supplier_id", "supplier_name", "component_id",
                "lead_time_days", "order_quantity", "on_time_delivery"
            ]
            self._validate_dataframe(df, required_cols, "supplier_lead_times")
            
            df = self._parse_dates(df)
            df = self._handle_missing_values(df)
            df = self._handle_outliers(df, ["lead_time_days", "order_quantity"])
            
            # Ensure on_time_delivery is binary
            df["on_time_delivery"] = df["on_time_delivery"].astype(int).clip(0, 1)
            
            # Sort by date
            df = df.sort_values("date").reset_index(drop=True)
            
            self._cache[cache_key] = df
            logger.info(f"Loaded {len(df)} supplier lead time records")
            return df.copy()
            
        except FileNotFoundError:
            logger.error(f"Supplier lead times file not found: {self.data_files['supplier_lead_times']}")
            raise
        except Exception as e:
            logger.error(f"Error loading supplier lead times: {e}")
            raise
    
    def load_manufacturing_production(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load and preprocess manufacturing production data.
        
        Columns: date, plant_id, plant_name, plant_region, sku, units_produced,
                 production_capacity, capacity_utilization, downtime_hours,
                 cycle_time_hours, defect_rate
        
        Returns:
            Preprocessed DataFrame
        """
        cache_key = "manufacturing_production"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        try:
            df = pd.read_csv(self.data_files["manufacturing_production"])
            
            required_cols = [
                "date", "plant_id", "plant_name", "sku", "units_produced",
                "production_capacity", "capacity_utilization", "downtime_hours"
            ]
            self._validate_dataframe(df, required_cols, "manufacturing_production")
            
            df = self._parse_dates(df)
            df = self._handle_missing_values(df)
            df = self._handle_outliers(df, ["units_produced", "downtime_hours", "cycle_time_hours"])
            
            # Ensure capacity_utilization is between 0 and 1
            df["capacity_utilization"] = df["capacity_utilization"].clip(0, 1.5)
            
            # Ensure defect_rate is between 0 and 1
            if "defect_rate" in df.columns:
                df["defect_rate"] = df["defect_rate"].clip(0, 1)
            
            df = df.sort_values("date").reset_index(drop=True)
            
            self._cache[cache_key] = df
            logger.info(f"Loaded {len(df)} manufacturing production records")
            return df.copy()
            
        except FileNotFoundError:
            logger.error(f"Manufacturing production file not found")
            raise
        except Exception as e:
            logger.error(f"Error loading manufacturing production: {e}")
            raise
    
    def load_inventory_levels(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load and preprocess inventory levels data.
        
        Columns: date, warehouse_id, warehouse_name, warehouse_region, sku,
                 stock_on_hand, safety_stock, reorder_point, inbound_qty,
                 outbound_qty, days_of_supply
        
        Returns:
            Preprocessed DataFrame
        """
        cache_key = "inventory_levels"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        try:
            df = pd.read_csv(self.data_files["inventory_levels"])
            
            required_cols = [
                "date", "warehouse_id", "warehouse_name", "sku",
                "stock_on_hand", "safety_stock", "reorder_point"
            ]
            self._validate_dataframe(df, required_cols, "inventory_levels")
            
            df = self._parse_dates(df)
            df = self._handle_missing_values(df)
            
            # Ensure non-negative values for quantities
            qty_cols = ["stock_on_hand", "safety_stock", "reorder_point", "inbound_qty", "outbound_qty"]
            for col in qty_cols:
                if col in df.columns:
                    df[col] = df[col].clip(lower=0)
            
            df = df.sort_values("date").reset_index(drop=True)
            
            self._cache[cache_key] = df
            logger.info(f"Loaded {len(df)} inventory level records")
            return df.copy()
            
        except FileNotFoundError:
            logger.error(f"Inventory levels file not found")
            raise
        except Exception as e:
            logger.error(f"Error loading inventory levels: {e}")
            raise
    
    def load_customer_demand(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load and preprocess customer demand data.
        
        Columns: date, region, customer_segment, sku, order_quantity,
                 revenue, is_promotional, season
        
        Returns:
            Preprocessed DataFrame
        """
        cache_key = "customer_demand"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        try:
            df = pd.read_csv(self.data_files["customer_demand"])
            
            required_cols = ["date", "region", "sku", "order_quantity"]
            self._validate_dataframe(df, required_cols, "customer_demand")
            
            df = self._parse_dates(df)
            df = self._handle_missing_values(df)
            df = self._handle_outliers(df, ["order_quantity", "revenue"])
            
            # Ensure is_promotional is binary
            if "is_promotional" in df.columns:
                df["is_promotional"] = df["is_promotional"].astype(int).clip(0, 1)
            
            # Ensure non-negative values
            df["order_quantity"] = df["order_quantity"].clip(lower=0)
            if "revenue" in df.columns:
                df["revenue"] = df["revenue"].clip(lower=0)
            
            df = df.sort_values("date").reset_index(drop=True)
            
            self._cache[cache_key] = df
            logger.info(f"Loaded {len(df)} customer demand records")
            return df.copy()
            
        except FileNotFoundError:
            logger.error(f"Customer demand file not found")
            raise
        except Exception as e:
            logger.error(f"Error loading customer demand: {e}")
            raise
    
    def load_transportation_data(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load and preprocess transportation data.
        
        Columns: date, route_id, origin, destination, carrier_id, carrier_name,
                 transit_time_days, cost, on_time_delivery, mode, distance_km
        
        Returns:
            Preprocessed DataFrame
        """
        cache_key = "transportation_data"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        try:
            df = pd.read_csv(self.data_files["transportation_data"])
            
            required_cols = [
                "date", "route_id", "origin", "destination",
                "transit_time_days", "on_time_delivery"
            ]
            self._validate_dataframe(df, required_cols, "transportation_data")
            
            df = self._parse_dates(df)
            df = self._handle_missing_values(df)
            df = self._handle_outliers(df, ["transit_time_days", "cost"])
            
            # Ensure on_time_delivery is binary
            df["on_time_delivery"] = df["on_time_delivery"].astype(int).clip(0, 1)
            
            # Ensure non-negative values
            df["transit_time_days"] = df["transit_time_days"].clip(lower=0)
            if "cost" in df.columns:
                df["cost"] = df["cost"].clip(lower=0)
            
            df = df.sort_values("date").reset_index(drop=True)
            
            self._cache[cache_key] = df
            logger.info(f"Loaded {len(df)} transportation records")
            return df.copy()
            
        except FileNotFoundError:
            logger.error(f"Transportation data file not found")
            raise
        except Exception as e:
            logger.error(f"Error loading transportation data: {e}")
            raise
    
    def load_external_factors(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load and preprocess external factors data.
        
        Columns: date, region, weather_severity_index, temperature_celsius,
                 precipitation_mm, tariff_rate, fuel_price_usd,
                 geopolitical_risk_index, port_congestion_index
        
        Returns:
            Preprocessed DataFrame
        """
        cache_key = "external_factors"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        try:
            df = pd.read_csv(self.data_files["external_factors"])
            
            required_cols = ["date", "region", "weather_severity_index"]
            self._validate_dataframe(df, required_cols, "external_factors")
            
            df = self._parse_dates(df)
            df = self._handle_missing_values(df)
            
            # Clip weather severity index
            df["weather_severity_index"] = df["weather_severity_index"].clip(0, 10)
            
            # Ensure non-negative values for various indices
            if "port_congestion_index" in df.columns:
                df["port_congestion_index"] = df["port_congestion_index"].clip(lower=0)
            if "fuel_price_usd" in df.columns:
                df["fuel_price_usd"] = df["fuel_price_usd"].clip(lower=0)
            if "tariff_rate" in df.columns:
                df["tariff_rate"] = df["tariff_rate"].clip(0, 1)
            
            df = df.sort_values("date").reset_index(drop=True)
            
            self._cache[cache_key] = df
            logger.info(f"Loaded {len(df)} external factor records")
            return df.copy()
            
        except FileNotFoundError:
            logger.error(f"External factors file not found")
            raise
        except Exception as e:
            logger.error(f"Error loading external factors: {e}")
            raise
    
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load all data sources.
        
        Returns:
            Dictionary of all DataFrames
        """
        return {
            "supplier_lead_times": self.load_supplier_lead_times(),
            "manufacturing_production": self.load_manufacturing_production(),
            "inventory_levels": self.load_inventory_levels(),
            "customer_demand": self.load_customer_demand(),
            "transportation_data": self.load_transportation_data(),
            "external_factors": self.load_external_factors(),
        }
    
    def get_entities(self) -> Dict[str, List]:
        """
        Get all unique entities from the data.
        
        Returns:
            Dictionary of entity lists
        """
        entities = {
            "suppliers": [],
            "plants": [],
            "warehouses": [],
            "routes": [],
            "skus": set(),
            "regions": set(),
        }
        
        try:
            # Suppliers
            supplier_df = self.load_supplier_lead_times()
            suppliers = supplier_df.drop_duplicates(subset=["supplier_id"])[
                ["supplier_id", "supplier_name", "supplier_tier", "supplier_region"]
            ].to_dict("records")
            for s in suppliers:
                components = supplier_df[supplier_df["supplier_id"] == s["supplier_id"]]["component_id"].unique().tolist()
                s["components"] = components
            entities["suppliers"] = suppliers
            
            # Plants
            mfg_df = self.load_manufacturing_production()
            plants = mfg_df.drop_duplicates(subset=["plant_id"])[
                ["plant_id", "plant_name", "plant_region"]
            ].to_dict("records")
            for p in plants:
                skus = mfg_df[mfg_df["plant_id"] == p["plant_id"]]["sku"].unique().tolist()
                p["skus"] = skus
            entities["plants"] = plants
            
            # Warehouses
            inv_df = self.load_inventory_levels()
            warehouses = inv_df.drop_duplicates(subset=["warehouse_id"])[
                ["warehouse_id", "warehouse_name", "warehouse_region"]
            ].to_dict("records")
            for w in warehouses:
                skus = inv_df[inv_df["warehouse_id"] == w["warehouse_id"]]["sku"].unique().tolist()
                w["skus"] = skus
            entities["warehouses"] = warehouses
            
            # Routes
            trans_df = self.load_transportation_data()
            routes = trans_df.drop_duplicates(subset=["route_id"])[
                ["route_id", "origin", "destination", "carrier_id", "carrier_name", "mode"]
            ].to_dict("records")
            entities["routes"] = routes
            
            # Collect all SKUs
            for df in [mfg_df, inv_df, self.load_customer_demand()]:
                if "sku" in df.columns:
                    entities["skus"].update(df["sku"].unique())
            entities["skus"] = list(entities["skus"])
            
            # Collect all regions
            for df_name in ["customer_demand", "external_factors"]:
                df = getattr(self, f"load_{df_name}")()
                if "region" in df.columns:
                    entities["regions"].update(df["region"].unique())
            entities["regions"] = list(entities["regions"])
            
        except Exception as e:
            logger.error(f"Error getting entities: {e}")
        
        return entities
    
    def check_data_availability(self) -> Dict[str, bool]:
        """
        Check availability of all data files.
        
        Returns:
            Dictionary of data source availability
        """
        availability = {}
        for name, path in self.data_files.items():
            availability[name] = Path(path).exists()
        return availability
    
    def clear_cache(self):
        """Clear the data cache."""
        self._cache.clear()
        logger.info("Data cache cleared")

