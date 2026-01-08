import { useState, useMemo } from 'react';
import { motion } from 'motion/react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import {
  Package,
  Factory,
  Warehouse,
  TrendingUp,
  Truck,
  Globe,
  AlertCircle,
} from 'lucide-react';
import type { AnalysisConfig, Risk } from '../types';
import type { ForecastResult } from '../api/supplyChainApi';
import {
  transformSupplierForecasts,
  transformManufacturingForecasts,
  transformInventoryForecasts,
  transformDemandForecasts,
  transformTransportationForecasts,
  transformExternalFactorsForecasts,
} from '../utils/forecastTransformers';

interface ForecastChartsProps {
  config: AnalysisConfig;
  risks: Risk[];
  forecastData?: Record<string, ForecastResult[]>;
}

type TabType =
  | 'suppliers'
  | 'manufacturing'
  | 'inventory'
  | 'demand'
  | 'transportation'
  | 'externalFactors';

const MODULE_TO_API_KEY: Record<string, string> = {
  suppliers: 'suppliers',
  manufacturing: 'manufacturing',
  inventory: 'inventory',
  demand: 'demand',
  transportation: 'transportation',
  externalFactors: 'external',
};

export function ForecastCharts({ config, risks, forecastData }: ForecastChartsProps) {
  const tabs = [
    { key: 'suppliers', label: 'Suppliers', icon: Package },
    { key: 'manufacturing', label: 'Manufacturing', icon: Factory },
    { key: 'inventory', label: 'Inventory', icon: Warehouse },
    { key: 'demand', label: 'Demand', icon: TrendingUp },
    { key: 'transportation', label: 'Transportation', icon: Truck },
    { key: 'externalFactors', label: 'External Factors', icon: Globe },
  ].filter((tab) => config.modules[tab.key as keyof typeof config.modules]);

  const [activeTab, setActiveTab] = useState<TabType>(tabs[0]?.key as TabType);

  if (tabs.length === 0) return null;

  // Get forecast data for active tab
  const activeModuleKey = MODULE_TO_API_KEY[activeTab];
  const activeForecasts = forecastData?.[activeModuleKey] || [];

  // Show message if no data
  if (!forecastData || Object.keys(forecastData).length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-lg shadow-md p-6"
      >
        <div className="flex flex-col items-center justify-center py-12 text-gray-500">
          <AlertCircle className="w-12 h-12 mb-4" />
          <p className="text-lg">No forecast data available</p>
          <p className="text-sm mt-2">Run an analysis to see forecast charts</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-white rounded-lg shadow-md p-6"
    >
      <h2 className="text-2xl mb-6">Forecast Analysis</h2>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-200">
        {tabs.map((tab) => {
          const moduleKey = MODULE_TO_API_KEY[tab.key];
          const hasData = forecastData?.[moduleKey] && forecastData[moduleKey].length > 0;
          
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as TabType)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-all ${
                activeTab === tab.key
                  ? 'border-[#1769FF] text-[#1769FF]'
                  : 'border-transparent text-gray-600 hover:text-[#1769FF]'
              } ${!hasData ? 'opacity-50' : ''}`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              {!hasData && <span className="text-xs">(No data)</span>}
            </button>
          );
        })}
      </div>

      {/* Chart Content */}
      <div className="min-h-[400px]">
        {activeForecasts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <AlertCircle className="w-12 h-12 mb-4" />
            <p>No forecast data available for {tabs.find(t => t.key === activeTab)?.label}</p>
          </div>
        ) : (
          <>
            {activeTab === 'suppliers' && (
              <SuppliersChart
                forecasts={activeForecasts}
                horizon={config.forecastHorizon}
              />
            )}
            {activeTab === 'manufacturing' && (
              <ManufacturingChart
                forecasts={activeForecasts}
                horizon={config.forecastHorizon}
              />
            )}
            {activeTab === 'inventory' && (
              <InventoryChart
                forecasts={activeForecasts}
                horizon={config.forecastHorizon}
              />
            )}
            {activeTab === 'demand' && (
              <DemandChart
                forecasts={activeForecasts}
                horizon={config.forecastHorizon}
              />
            )}
            {activeTab === 'transportation' && (
              <TransportationChart forecasts={activeForecasts} />
            )}
            {activeTab === 'externalFactors' && (
              <ExternalFactorsChart
                forecasts={activeForecasts}
                horizon={config.forecastHorizon}
              />
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}

function SuppliersChart({
  forecasts,
  horizon,
}: {
  forecasts: ForecastResult[];
  horizon: number;
}) {
  const data = useMemo(
    () => transformSupplierForecasts(forecasts, horizon),
    [forecasts, horizon]
  );

  if (data.length === 0) {
    return <div className="text-center py-8 text-gray-500">No supplier forecast data</div>;
  }

  return (
    <div>
      <h3 className="text-lg mb-4">Supplier Lead Time Forecast with Confidence Intervals</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="day"
            label={{ value: 'Days', position: 'insideBottom', offset: -5 }}
          />
          <YAxis label={{ value: 'Lead Time (days)', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
          />
          <Legend />
          <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" label="Threshold" />
          <Line
            type="monotone"
            dataKey="upperBound"
            stroke="#93c5fd"
            strokeWidth={1}
            dot={false}
            name="Upper Bound"
          />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#1769FF"
            strokeWidth={3}
            dot={false}
            name="Predicted Lead Time"
          />
          <Line
            type="monotone"
            dataKey="lowerBound"
            stroke="#93c5fd"
            strokeWidth={1}
            dot={false}
            name="Lower Bound"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function ManufacturingChart({
  forecasts,
  horizon,
}: {
  forecasts: ForecastResult[];
  horizon: number;
}) {
  const data = useMemo(
    () => transformManufacturingForecasts(forecasts, horizon),
    [forecasts, horizon]
  );

  if (data.length === 0) {
    return <div className="text-center py-8 text-gray-500">No manufacturing forecast data</div>;
  }

  return (
    <div>
      <h3 className="text-lg mb-4">Manufacturing Capacity Utilization</h3>
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="day"
            label={{ value: 'Days', position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            label={{ value: 'Utilization (%)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
          />
          <Legend />
          <ReferenceLine
            y={90}
            stroke="#ef4444"
            strokeDasharray="3 3"
            label="Critical Threshold"
          />
          <Area
            type="monotone"
            dataKey="utilization"
            stroke="#1769FF"
            fill="#1769FF"
            fillOpacity={0.3}
            name="Capacity Utilization"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function InventoryChart({
  forecasts,
  horizon,
}: {
  forecasts: ForecastResult[];
  horizon: number;
}) {
  const data = useMemo(
    () => transformInventoryForecasts(forecasts, horizon),
    [forecasts, horizon]
  );

  if (data.length === 0) {
    return <div className="text-center py-8 text-gray-500">No inventory forecast data</div>;
  }

  return (
    <div>
      <h3 className="text-lg mb-4">Inventory Levels vs Safety Stock</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="day"
            label={{ value: 'Days', position: 'insideBottom', offset: -5 }}
          />
          <YAxis label={{ value: 'Units', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="stockLevel"
            stroke="#1769FF"
            strokeWidth={3}
            name="Stock Level"
          />
          <Line
            type="monotone"
            dataKey="safetyStock"
            stroke="#ef4444"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Safety Stock"
          />
          <Line
            type="monotone"
            dataKey="reorderPoint"
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Reorder Point"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function DemandChart({
  forecasts,
  horizon,
}: {
  forecasts: ForecastResult[];
  horizon: number;
}) {
  const data = useMemo(
    () => transformDemandForecasts(forecasts, horizon),
    [forecasts, horizon]
  );

  if (data.length === 0) {
    return <div className="text-center py-8 text-gray-500">No demand forecast data</div>;
  }

  return (
    <div>
      <h3 className="text-lg mb-4">Demand Forecast - Historical vs Predicted</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="day"
            label={{ value: 'Days', position: 'insideBottom', offset: -5 }}
          />
          <YAxis label={{ value: 'Units', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="historical"
            stroke="#10b981"
            strokeWidth={2}
            name="Historical Demand"
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="forecasted"
            stroke="#1769FF"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Forecasted Demand"
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-sm text-gray-600 mt-2">
        * Highlighted periods indicate high volatility
      </p>
    </div>
  );
}

function TransportationChart({ forecasts }: { forecasts: ForecastResult[] }) {
  const data = useMemo(
    () => transformTransportationForecasts(forecasts),
    [forecasts]
  );

  if (data.length === 0) {
    return <div className="text-center py-8 text-gray-500">No transportation forecast data</div>;
  }

  return (
    <div>
      <h3 className="text-lg mb-4">Transit Time Comparison by Route</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="route" />
          <YAxis label={{ value: 'Days', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
          />
          <Legend />
          <Bar dataKey="baseline" fill="#10b981" name="Baseline Transit Time" />
          <Bar
            dataKey="forecasted"
            fill={(entry: any) => (entry.delayed ? '#ef4444' : '#1769FF')}
            name="Forecasted Transit Time"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function ExternalFactorsChart({
  forecasts,
  horizon,
}: {
  forecasts: ForecastResult[];
  horizon: number;
}) {
  const data = useMemo(
    () => transformExternalFactorsForecasts(forecasts, horizon),
    [forecasts, horizon]
  );

  if (data.weather.length === 0 && data.tariffs.length === 0 && data.geopolitical.length === 0) {
    return <div className="text-center py-8 text-gray-500">No external factors forecast data</div>;
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg">External Risk Factors</h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weather Severity */}
        {data.weather.length > 0 && (
          <div>
            <h4 className="mb-3">Weather Severity Index</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data.weather}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
                />
                <Bar
                  dataKey="severity"
                  fill="#1769FF"
                  radius={[8, 8, 0, 0]}
                  name="Severity"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Tariff Rates */}
        {data.tariffs.length > 0 && (
          <div>
            <h4 className="mb-3">Tariff Rate Trends</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data.tariffs}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
                />
                <Line
                  type="monotone"
                  dataKey="rate"
                  stroke="#1769FF"
                  strokeWidth={3}
                  name="Tariff Rate (%)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Geopolitical Risk */}
        {data.geopolitical.length > 0 && (
          <div className="lg:col-span-2">
            <h4 className="mb-3">Geopolitical Risk Index by Region</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data.geopolitical} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="region" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
                />
                <Bar
                  dataKey="riskIndex"
                  fill="#1769FF"
                  radius={[0, 8, 8, 0]}
                  name="Risk Index"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
