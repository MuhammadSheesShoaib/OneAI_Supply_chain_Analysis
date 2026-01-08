import { motion } from 'motion/react';
import { RiskTable } from '../components/RiskTable';
import { KPICards } from '../components/shared/KPICards';
import type { SummaryMetrics, Risk } from '../types';

interface RiskAnalysisPageProps {
  summaryMetrics: SummaryMetrics | null;
  risks: Risk[];
  onViewRiskDetails: (risk: Risk) => void;
  analysisStarted: boolean;
}

export function RiskAnalysisPage({
  summaryMetrics,
  risks,
  onViewRiskDetails,
  analysisStarted,
}: RiskAnalysisPageProps) {
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Risk Analysis Table</h1>
        <p className="text-gray-600">
          Comprehensive view of all identified risks with filtering and sorting capabilities
        </p>
      </div>

      {/* KPI Cards */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Performance Indicators</h2>
        <KPICards metrics={summaryMetrics || defaultMetrics} risks={risks} />
      </div>

      {/* Risk Table */}
      {analysisStarted ? (
        <RiskTable risks={risks} onViewDetails={onViewRiskDetails} />
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <p className="text-gray-500 text-lg">
            Start an analysis from the Control Panel to view risk data
          </p>
        </div>
      )}
    </motion.div>
  );
}

