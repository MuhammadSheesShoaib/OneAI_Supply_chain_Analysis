import { motion } from 'motion/react';
import { MitigationPanel } from '../components/MitigationPanel';
import { KPICards } from '../components/shared/KPICards';
import type { SummaryMetrics, Risk } from '../types';

interface MitigationActionPlanPageProps {
  summaryMetrics: SummaryMetrics | null;
  risks: Risk[];
  analysisStarted: boolean;
}

export function MitigationActionPlanPage({
  summaryMetrics,
  risks,
  analysisStarted,
}: MitigationActionPlanPageProps) {
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Mitigation Action Plan</h1>
        <p className="text-gray-600">
          View and manage mitigation strategies organized by timeline
        </p>
      </div>

      {/* KPI Cards */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Performance Indicators</h2>
        <KPICards metrics={summaryMetrics || defaultMetrics} risks={risks} />
      </div>

      {/* Mitigation Panel */}
      {analysisStarted ? (
        <MitigationPanel risks={risks} />
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <p className="text-gray-500 text-lg">
            Start an analysis from the Control Panel to view mitigation strategies
          </p>
        </div>
      )}
    </motion.div>
  );
}

