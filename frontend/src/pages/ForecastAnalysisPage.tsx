import { motion } from 'motion/react';
import { ForecastCharts } from '../components/ForecastCharts';
import { KPICards } from '../components/shared/KPICards';
import type { AnalysisConfig, SummaryMetrics, Risk, AnalysisResponse } from '../types';

interface ForecastAnalysisPageProps {
  config: AnalysisConfig;
  summaryMetrics: SummaryMetrics | null;
  risks: Risk[];
  forecastData?: Record<string, any[]>;
  analysisStarted: boolean;
}

export function ForecastAnalysisPage({
  config,
  summaryMetrics,
  risks,
  forecastData,
  analysisStarted,
}: ForecastAnalysisPageProps) {
  const defaultMetrics: SummaryMetrics = {
    totalRisks: 0,
    criticalRisks: 0,
    highPriorityRisks: 0,
    mediumPriorityRisks: 0,
    entitiesAffected: 0,
    averageRiskScore: 0,
    totalMitigationStrategies: 0,
    averageRiskReduction: 0,
    priorityActions: 0,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Forecast Analysis</h1>
        <p className="text-gray-600">
          View detailed forecasts for all supply chain modules
        </p>
      </div>

      {/* KPI Cards */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Performance Indicators</h2>
        <KPICards metrics={summaryMetrics || defaultMetrics} risks={risks} />
      </div>

      {/* Forecast Charts */}
      {analysisStarted ? (
        <ForecastCharts
          config={config}
          risks={risks}
          forecastData={forecastData}
        />
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <p className="text-gray-500 text-lg">
            Start an analysis from the Control Panel to view forecast data
          </p>
        </div>
      )}
    </motion.div>
  );
}

