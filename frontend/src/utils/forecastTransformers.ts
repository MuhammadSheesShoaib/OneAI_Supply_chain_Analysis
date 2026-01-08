/**
 * Transformers to convert backend forecast data to chart-compatible format.
 */
import type { ForecastResult, ForecastDataPoint } from '../api/supplyChainApi';

// ==================== Chart Data Types ====================

export interface ChartDataPoint {
  day: number;
  value: number;
  upperBound?: number;
  lowerBound?: number;
  historical?: number;
  forecasted?: number;
}

export interface SupplierChartData extends ChartDataPoint {
  predicted: number;
  threshold: number;
}

export interface ManufacturingChartData extends ChartDataPoint {
  utilization: number;
  criticalThreshold: number;
}

export interface InventoryChartData extends ChartDataPoint {
  stockLevel: number;
  safetyStock: number;
  reorderPoint: number;
}

export interface DemandChartData extends ChartDataPoint {
  historical: number | null;
  forecasted: number | null;
  volatilityHigh: boolean;
}

export interface TransportationChartData {
  route: string;
  baseline: number;
  forecasted: number;
  delayed: boolean;
}

export interface ExternalFactorsChartData {
  weather: Array<{ week: string; severity: number }>;
  tariffs: Array<{ month: string; rate: number }>;
  geopolitical: Array<{ region: string; riskIndex: number }>;
}

// ==================== Transformers ====================

/**
 * Transform forecast data points to chart format.
 * If forecast_data is not available, creates a simple trend line.
 */
function transformForecastDataPoints(
  forecastData: ForecastDataPoint[] | undefined,
  horizon: number,
  historicalAvg: number,
  forecastedAvg: number
): ChartDataPoint[] {
  if (forecastData && forecastData.length > 0) {
    // Use actual forecast data
    return forecastData.map((point, idx) => ({
      day: idx,
      value: point.yhat,
      upperBound: point.yhat_upper,
      lowerBound: point.yhat_lower,
      historical: idx < forecastData.length * 0.3 ? historicalAvg : null,
      forecasted: point.yhat,
    }));
  } else {
    // Create synthetic data based on averages
    const data: ChartDataPoint[] = [];
    const changePerDay = (forecastedAvg - historicalAvg) / horizon;
    
    for (let day = 0; day <= horizon; day++) {
      const value = historicalAvg + changePerDay * day;
      const variance = Math.abs(changePerDay) * 0.2; // 20% variance
      
      data.push({
        day,
        value,
        upperBound: value + variance,
        lowerBound: value - variance,
        historical: day < horizon * 0.3 ? historicalAvg : null,
        forecasted: value,
      });
    }
    
    return data;
  }
}

/**
 * Transform supplier forecasts to chart data.
 */
export function transformSupplierForecasts(
  forecasts: ForecastResult[] | undefined,
  horizon: number
): SupplierChartData[] {
  if (!forecasts || forecasts.length === 0) {
    return [];
  }

  // Aggregate all supplier forecasts
  const allDataPoints: ChartDataPoint[] = [];
  
  forecasts.forEach((forecast) => {
    const points = transformForecastDataPoints(
      forecast.forecast_data,
      horizon,
      forecast.historical_avg,
      forecast.forecasted_avg
    );
    allDataPoints.push(...points);
  });

  // Average across all suppliers for each day
  const dayMap = new Map<number, number[]>();
  allDataPoints.forEach((point) => {
    if (!dayMap.has(point.day)) {
      dayMap.set(point.day, []);
    }
    dayMap.get(point.day)!.push(point.value);
  });

  const result: SupplierChartData[] = [];
  dayMap.forEach((values, day) => {
    const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
    result.push({
      day,
      predicted: avg,
      upperBound: avg * 1.1,
      lowerBound: avg * 0.9,
      value: avg,
      threshold: 70, // Capacity threshold
    });
  });

  return result.sort((a, b) => a.day - b.day);
}

/**
 * Transform manufacturing forecasts to chart data.
 */
export function transformManufacturingForecasts(
  forecasts: ForecastResult[] | undefined,
  horizon: number
): ManufacturingChartData[] {
  if (!forecasts || forecasts.length === 0) {
    return [];
  }

  const allDataPoints: ChartDataPoint[] = [];
  
  forecasts.forEach((forecast) => {
    const points = transformForecastDataPoints(
      forecast.forecast_data,
      horizon,
      forecast.historical_avg,
      forecast.forecasted_avg
    );
    allDataPoints.push(...points);
  });

  const dayMap = new Map<number, number[]>();
  allDataPoints.forEach((point) => {
    if (!dayMap.has(point.day)) {
      dayMap.set(point.day, []);
    }
    dayMap.get(point.day)!.push(point.value);
  });

  const result: ManufacturingChartData[] = [];
  dayMap.forEach((values, day) => {
    const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
    result.push({
      day,
      utilization: avg,
      value: avg,
      criticalThreshold: 90,
    });
  });

  return result.sort((a, b) => a.day - b.day);
}

/**
 * Transform inventory forecasts to chart data.
 */
export function transformInventoryForecasts(
  forecasts: ForecastResult[] | undefined,
  horizon: number
): InventoryChartData[] {
  if (!forecasts || forecasts.length === 0) {
    return [];
  }

  const allDataPoints: ChartDataPoint[] = [];
  
  forecasts.forEach((forecast) => {
    const points = transformForecastDataPoints(
      forecast.forecast_data,
      horizon,
      forecast.historical_avg,
      forecast.forecasted_avg
    );
    allDataPoints.push(...points);
  });

  const dayMap = new Map<number, number[]>();
  allDataPoints.forEach((point) => {
    if (!dayMap.has(point.day)) {
      dayMap.set(point.day, []);
    }
    dayMap.get(point.day)!.push(point.value);
  });

  // Calculate safety stock (typically 20% of average)
  const avgValue = forecasts.reduce((sum, f) => sum + f.historical_avg, 0) / forecasts.length;
  const safetyStock = avgValue * 0.2;
  const reorderPoint = avgValue * 0.3;

  const result: InventoryChartData[] = [];
  dayMap.forEach((values, day) => {
    const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
    result.push({
      day,
      stockLevel: avg,
      safetyStock,
      reorderPoint,
      value: avg,
    });
  });

  return result.sort((a, b) => a.day - b.day);
}

/**
 * Transform demand forecasts to chart data.
 */
export function transformDemandForecasts(
  forecasts: ForecastResult[] | undefined,
  horizon: number
): DemandChartData[] {
  if (!forecasts || forecasts.length === 0) {
    return [];
  }

  const allDataPoints: ChartDataPoint[] = [];
  
  forecasts.forEach((forecast) => {
    const points = transformForecastDataPoints(
      forecast.forecast_data,
      horizon,
      forecast.historical_avg,
      forecast.forecasted_avg
    );
    allDataPoints.push(...points);
  });

  const dayMap = new Map<number, { historical: number[]; forecasted: number[] }>();
  allDataPoints.forEach((point) => {
    if (!dayMap.has(point.day)) {
      dayMap.set(point.day, { historical: [], forecasted: [] });
    }
    const dayData = dayMap.get(point.day)!;
    if (point.historical !== null) {
      dayData.historical.push(point.historical);
    }
    if (point.forecasted !== null) {
      dayData.forecasted.push(point.forecasted);
    }
  });

  const result: DemandChartData[] = [];
  dayMap.forEach((dayData, day) => {
    const historical = dayData.historical.length > 0
      ? dayData.historical.reduce((sum, v) => sum + v, 0) / dayData.historical.length
      : null;
    const forecasted = dayData.forecasted.length > 0
      ? dayData.forecasted.reduce((sum, v) => sum + v, 0) / dayData.forecasted.length
      : null;
    
    // High volatility if there's a big difference
    const volatilityHigh = historical !== null && forecasted !== null
      ? Math.abs(forecasted - historical) / historical > 0.3
      : false;

    result.push({
      day,
      historical,
      forecasted,
      volatilityHigh,
      value: forecasted || historical || 0,
    });
  });

  return result.sort((a, b) => a.day - b.day);
}

/**
 * Transform transportation forecasts to chart data.
 */
export function transformTransportationForecasts(
  forecasts: ForecastResult[] | undefined
): TransportationChartData[] {
  if (!forecasts || forecasts.length === 0) {
    return [];
  }

  return forecasts.map((forecast) => ({
    route: forecast.entity_name || forecast.entity_id,
    baseline: forecast.historical_avg,
    forecasted: forecast.forecasted_avg,
    delayed: forecast.forecasted_avg > forecast.historical_avg * 1.1,
  }));
}

/**
 * Transform external factors forecasts to chart data.
 */
export function transformExternalFactorsForecasts(
  forecasts: ForecastResult[] | undefined,
  horizon: number
): ExternalFactorsChartData {
  if (!forecasts || forecasts.length === 0) {
    return {
      weather: [],
      tariffs: [],
      geopolitical: [],
    };
  }

  const weather: Array<{ week: string; severity: number }> = [];
  const tariffs: Array<{ month: string; rate: number }> = [];
  const geopolitical: Array<{ region: string; riskIndex: number }> = [];

  forecasts.forEach((forecast) => {
    const metric = forecast.metric.toLowerCase();
    
    if (metric.includes('weather')) {
      const weeks = Math.ceil(horizon / 7);
      for (let i = 0; i < weeks; i++) {
        weather.push({
          week: `W${i + 1}`,
          severity: Math.min(forecast.forecasted_avg / 10, 10), // Normalize to 1-10
        });
      }
    } else if (metric.includes('tariff')) {
      const months = Math.ceil(horizon / 30);
      for (let i = 0; i < months; i++) {
        tariffs.push({
          month: `M${i + 1}`,
          rate: forecast.forecasted_avg,
        });
      }
    } else if (metric.includes('geopolitical') || metric.includes('port')) {
      geopolitical.push({
        region: forecast.entity_name || forecast.entity_id,
        riskIndex: Math.min(forecast.forecasted_avg * 10, 100),
      });
    }
  });

  return { weather, tariffs, geopolitical };
}

