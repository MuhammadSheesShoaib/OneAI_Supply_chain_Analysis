import { motion } from 'motion/react';
import { ControlPanel } from '../components/ControlPanel';
import { KPICards } from '../components/shared/KPICards';
import type { AnalysisConfig, SummaryMetrics, Risk } from '../types';

interface ControlPanelPageProps {
  config: AnalysisConfig;
  onConfigChange: (config: AnalysisConfig) => void;
  onStartAnalysis: () => void;
  analysisStarted: boolean;
  isLoading: boolean;
  summaryMetrics: SummaryMetrics | null;
  risks: Risk[];
}

export function ControlPanelPage({
  config,
  onConfigChange,
  onStartAnalysis,
  analysisStarted,
  isLoading,
  summaryMetrics,
  risks,
}: ControlPanelPageProps) {
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Control Panel</h1>
        <p className="text-gray-600">
          Configure analysis parameters and start the supply chain risk analysis
        </p>
      </div>

      {/* Control Panel */}
      <ControlPanel
        config={config}
        onConfigChange={onConfigChange}
        onStartAnalysis={onStartAnalysis}
        analysisStarted={analysisStarted}
        isLoading={isLoading}
      />

      {/* KPI Cards */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Performance Indicators</h2>
        <KPICards metrics={summaryMetrics || defaultMetrics} risks={risks} />
      </div>
    </motion.div>
  );
}

