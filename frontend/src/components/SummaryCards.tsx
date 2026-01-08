import { useState } from 'react';
import { motion } from 'motion/react';
import {
  AlertTriangle,
  AlertOctagon,
  AlertCircle,
  Info,
  Building2,
  TrendingUp,
} from 'lucide-react';
import type { SummaryMetrics, Risk } from '../types';
import { KPIDetailModal } from './KPIDetailModal';

interface SummaryCardsProps {
  metrics: SummaryMetrics;
  risks?: Risk[];
}

export function SummaryCards({ metrics, risks = [] }: SummaryCardsProps) {
  const [selectedKPI, setSelectedKPI] = useState<string | null>(null);
  const cards = [
    {
      label: 'Total Risks Detected',
      value: metrics.totalRisks,
      icon: AlertTriangle,
      bgColor: 'bg-blue-50',
      iconColor: 'text-[#1769FF]',
      textColor: 'text-[#1769FF]',
    },
    {
      label: 'Critical Risks',
      value: metrics.criticalRisks,
      icon: AlertOctagon,
      bgColor: 'bg-red-50',
      iconColor: 'text-red-600',
      textColor: 'text-red-600',
    },
    {
      label: 'High Priority Risks',
      value: metrics.highPriorityRisks,
      icon: AlertCircle,
      bgColor: 'bg-orange-50',
      iconColor: 'text-orange-600',
      textColor: 'text-orange-600',
    },
    {
      label: 'Medium Priority Risks',
      value: metrics.mediumPriorityRisks,
      icon: Info,
      bgColor: 'bg-yellow-50',
      iconColor: 'text-yellow-600',
      textColor: 'text-yellow-600',
    },
    {
      label: 'Entities Affected',
      value: metrics.entitiesAffected,
      icon: Building2,
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
      textColor: 'text-purple-600',
    },
    {
      label: 'Average Risk Score',
      value: metrics.averageRiskScore,
      icon: TrendingUp,
      bgColor: 'bg-indigo-50',
      iconColor: 'text-indigo-600',
      textColor: 'text-indigo-600',
    },
  ];

  const getKPIValue = (label: string) => {
    switch (label) {
      case 'Total Risks Detected':
        return metrics.totalRisks;
      case 'Critical Risks':
        return metrics.criticalRisks;
      case 'High Priority Risks':
        return metrics.highPriorityRisks;
      case 'Medium Priority Risks':
        return metrics.mediumPriorityRisks;
      case 'Entities Affected':
        return metrics.entitiesAffected;
      case 'Average Risk Score':
        return metrics.averageRiskScore;
      default:
        return 0;
    }
  };

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card, index) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -4, boxShadow: '0 10px 25px rgba(0,0,0,0.1)' }}
            onClick={() => setSelectedKPI(card.label)}
            className={`${card.bgColor} rounded-lg shadow-md p-6 transition-all cursor-pointer`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-gray-600 text-sm mb-2">{card.label}</p>
                <p className={`text-4xl ${card.textColor} mb-1`}>
                  {card.value}
                </p>
              </div>
              <div className={`${card.iconColor} bg-white rounded-lg p-3 shadow-sm`}>
                <card.icon className="w-6 h-6" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* KPI Detail Modal */}
      {selectedKPI && (
        <KPIDetailModal
          kpiType={selectedKPI}
          value={getKPIValue(selectedKPI)}
          risks={risks}
          onClose={() => setSelectedKPI(null)}
        />
      )}
    </>
  );
}
