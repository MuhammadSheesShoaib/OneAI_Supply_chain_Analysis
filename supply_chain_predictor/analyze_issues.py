"""Analyze supplier forecast issues and data fluctuations."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.data_loader import DataLoader
from models.prophet_forecaster import ProphetForecaster
import pandas as pd
import numpy as np

print("=" * 80)
print("ISSUE ANALYSIS: Supplier Forecasts & Data Fluctuation")
print("=" * 80)

# Initialize services
dl = DataLoader()
pf = ProphetForecaster()

# 1. Check if data loads correctly
print("\n1. DATA LOADING CHECK")
print("-" * 80)
try:
    df = dl.load_supplier_lead_times()
    print(f"[OK] Data loaded successfully: {len(df)} rows")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Unique suppliers: {df['supplier_id'].nunique()}")
    print(f"   Unique components: {df['component_id'].nunique()}")
except Exception as e:
    print(f"[ERROR] Data loading failed: {e}")
    sys.exit(1)

# 2. Check supplier-component combinations
print("\n2. SUPPLIER-COMPONENT COMBINATIONS")
print("-" * 80)
combinations = df.groupby(['supplier_id', 'component_id']).size().reset_index()
combinations.columns = ['supplier_id', 'component_id', 'count']
print(f"Total combinations: {len(combinations)}")
for _, row in combinations.iterrows():
    print(f"  {row['supplier_id']}-{row['component_id']}: {row['count']} records")

# 3. Test forecast for each combination
print("\n3. FORECAST TESTING")
print("-" * 80)
forecasts_successful = 0
forecasts_failed = 0

for _, row in combinations.iterrows():
    supplier_id = row['supplier_id']
    component_id = row['component_id']
    count = row['count']
    
    print(f"\nTesting: {supplier_id} - {component_id} ({count} records)")
    
    # Check if enough data
    if count < 30:
        print(f"  [WARNING] Insufficient data (<30 points)")
        forecasts_failed += 1
        continue
    
    # Filter data
    filtered = df[
        (df['supplier_id'] == supplier_id) & 
        (df['component_id'] == component_id)
    ]
    
    print(f"  Filtered rows: {len(filtered)}")
    print(f"  Lead time range: {filtered['lead_time_days'].min()}-{filtered['lead_time_days'].max()}")
    print(f"  Lead time mean: {filtered['lead_time_days'].mean():.2f}")
    
    # Try forecast
    try:
        result = pf.forecast_supplier_leadtime(
            df=df,
            supplier_id=supplier_id,
            component_id=component_id,
            horizon_days=45
        )
        
        if result.get('error'):
            print(f"  [ERROR] Forecast returned error: {result.get('error')}")
            forecasts_failed += 1
        else:
            forecast_data = result.get('forecast_data', [])
            print(f"  [SUCCESS] Forecast successful!")
            print(f"     Entity: {result.get('entity_id')}")
            print(f"     Historical avg: {result.get('historical_avg')}")
            print(f"     Forecasted avg: {result.get('forecasted_avg')}")
            print(f"     Forecast data points: {len(forecast_data)}")
            forecasts_successful += 1
            
    except Exception as e:
        print(f"  [ERROR] Forecast failed: {e}")
        import traceback
        traceback.print_exc()
        forecasts_failed += 1

print(f"\nForecast Summary: {forecasts_successful} successful, {forecasts_failed} failed")

# 4. Data Fluctuation Analysis
print("\n4. DATA FLUCTUATION ANALYSIS")
print("-" * 80)

for _, row in combinations.iterrows():
    supplier_id = row['supplier_id']
    component_id = row['component_id']
    
    filtered = df[
        (df['supplier_id'] == supplier_id) & 
        (df['component_id'] == component_id)
    ].sort_values('date')
    
    if len(filtered) < 30:
        continue
    
    lead_times = filtered['lead_time_days'].values
    dates = filtered['date'].values
    
    # Calculate statistics
    mean = lead_times.mean()
    std = lead_times.std()
    cv = std / mean if mean > 0 else 0
    min_val = lead_times.min()
    max_val = lead_times.max()
    
    # Calculate daily changes
    changes = np.diff(lead_times)
    avg_change = np.abs(changes).mean()
    max_change = np.abs(changes).max()
    
    # Trend analysis
    first_quarter = lead_times[:len(lead_times)//4].mean()
    last_quarter = lead_times[-len(lead_times)//4:].mean()
    trend_pct = ((last_quarter - first_quarter) / first_quarter * 100) if first_quarter > 0 else 0
    
    # Fluctuation assessment
    if cv < 0.1:
        fluctuation = "LOW"
    elif cv < 0.3:
        fluctuation = "MODERATE"
    else:
        fluctuation = "HIGH"
    
    print(f"\n{supplier_id} - {component_id}:")
    print(f"  Records: {len(filtered)}")
    print(f"  Mean: {mean:.2f} days")
    print(f"  Std Dev: {std:.2f} days")
    print(f"  Range: {min_val}-{max_val} days")
    print(f"  Coefficient of Variation: {cv:.3f}")
    print(f"  Fluctuation Level: {fluctuation}")
    print(f"  Avg Daily Change: {avg_change:.2f} days")
    print(f"  Max Daily Change: {max_change:.2f} days")
    print(f"  Trend: {trend_pct:+.1f}% ({'increasing' if trend_pct > 5 else 'decreasing' if trend_pct < -5 else 'stable'})")
    print(f"  Days with change >5: {(np.abs(changes) > 5).sum()}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

