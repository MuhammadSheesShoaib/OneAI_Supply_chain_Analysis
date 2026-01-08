import { motion, AnimatePresence } from 'motion/react';
import { X, AlertTriangle, AlertOctagon, AlertCircle, Info, Building2, TrendingUp, Shield, Target, CheckCircle2 } from 'lucide-react';
import type { Risk, Priority } from '../types';

interface KPIDetailModalProps {
  kpiType: string;
  value: number;
  risks: Risk[];
  onClose: () => void;
}

export function KPIDetailModal({ kpiType, value, risks, onClose }: KPIDetailModalProps) {
  const getKPIInfo = () => {
    switch (kpiType) {
      case 'Total Risks Detected':
        return {
          title: 'Total Risks Detected',
          description: 'This represents the total number of risks identified across all supply chain modules.',
          icon: AlertTriangle,
          iconColor: 'text-[#1769FF]',
          bgColor: 'bg-blue-50',
          filteredRisks: risks,
        };
      case 'Critical Risks':
        return {
          title: 'Critical Risks',
          description: 'Risks that require immediate attention and have the highest impact on operations.',
          icon: AlertOctagon,
          iconColor: 'text-red-600',
          bgColor: 'bg-red-50',
          filteredRisks: risks.filter((r) => r.priority === 'Critical'),
        };
      case 'High Priority Risks':
        return {
          title: 'High Priority Risks',
          description: 'Risks that need prompt action to prevent escalation to critical status.',
          icon: AlertCircle,
          iconColor: 'text-orange-600',
          bgColor: 'bg-orange-50',
          filteredRisks: risks.filter((r) => r.priority === 'High'),
        };
      case 'Medium Priority Risks':
        return {
          title: 'Medium Priority Risks',
          description: 'Risks that should be monitored and addressed in the near term.',
          icon: Info,
          iconColor: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          filteredRisks: risks.filter((r) => r.priority === 'Medium'),
        };
      case 'Entities Affected':
        return {
          title: 'Entities Affected',
          description: 'Total number of unique entities (suppliers, plants, warehouses, etc.) impacted by identified risks.',
          icon: Building2,
          iconColor: 'text-purple-600',
          bgColor: 'bg-purple-50',
          filteredRisks: risks,
        };
      case 'Average Risk Score':
        return {
          title: 'Average Risk Score',
          description: 'The average risk score across all identified risks. Higher scores indicate greater potential impact.',
          icon: TrendingUp,
          iconColor: 'text-indigo-600',
          bgColor: 'bg-indigo-50',
          filteredRisks: risks,
        };
      case 'Total Mitigation Strategies':
        return {
          title: 'Total Mitigation Strategies',
          description: 'Total number of mitigation strategies generated across all identified risks.',
          icon: Shield,
          iconColor: 'text-green-600',
          bgColor: 'bg-green-50',
          filteredRisks: risks,
        };
      case 'Average Risk Reduction':
        return {
          title: 'Average Risk Reduction',
          description: 'Average percentage of risk reduction expected from all mitigation strategies.',
          icon: Target,
          iconColor: 'text-teal-600',
          bgColor: 'bg-teal-50',
          filteredRisks: risks,
        };
      case 'Priority Actions':
        return {
          title: 'Priority Actions',
          description: 'Number of immediate and short-term mitigation actions that require urgent attention.',
          icon: CheckCircle2,
          iconColor: 'text-pink-600',
          bgColor: 'bg-pink-50',
          filteredRisks: risks,
        };
      default:
        return {
          title: kpiType,
          description: 'Detailed information about this metric.',
          icon: Info,
          iconColor: 'text-gray-600',
          bgColor: 'bg-gray-50',
          filteredRisks: risks,
        };
    }
  };

  const kpiInfo = getKPIInfo();
  const Icon = kpiInfo.icon;

  const getPriorityColor = (priority: Priority) => {
    const colors = {
      Critical: 'bg-red-100 text-red-800 border-red-300',
      High: 'bg-orange-100 text-orange-800 border-orange-300',
      Medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      Low: 'bg-green-100 text-green-800 border-green-300',
    };
    return colors[priority];
  };

  // Calculate unique entities affected
  const getUniqueEntities = () => {
    const entities = new Set<string>();
    risks.forEach((risk) => {
      risk.affectedEntities.forEach((entity) => entities.add(entity));
    });
    return Array.from(entities);
  };

  // Calculate average risk score
  const getAverageRiskScore = () => {
    if (risks.length === 0) return 0;
    const sum = risks.reduce((acc, risk) => acc + risk.riskScore, 0);
    return (sum / risks.length).toFixed(1);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className={`relative ${kpiInfo.bgColor} rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col`}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center gap-4">
              <div className={`${kpiInfo.iconColor} bg-white rounded-lg p-3 shadow-sm`}>
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{kpiInfo.title}</h2>
                <p className="text-gray-600 mt-1">{kpiInfo.description}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors p-2 hover:bg-white rounded-lg"
              aria-label="Close modal"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Value Display */}
            <div className="mb-6">
              <div className="bg-white rounded-lg p-6 shadow-sm">
                  <div className="flex items-baseline gap-2">
                  <span className={`text-5xl font-bold ${kpiInfo.iconColor}`}>
                    {kpiType === 'Average Risk Score' 
                      ? getAverageRiskScore() 
                      : typeof value === 'number' 
                      ? value.toLocaleString() 
                      : value}
                  </span>
                  {kpiType === 'Average Risk Score' && (
                    <span className="text-gray-500 text-lg">/ 100</span>
                  )}
                  {kpiType === 'Average Risk Reduction' && (
                    <span className="text-gray-500 text-lg">%</span>
                  )}
                </div>
                <p className="text-gray-600 mt-2">
                  {kpiType === 'Entities Affected'
                    ? `Unique entities: ${getUniqueEntities().length}`
                    : kpiType === 'Average Risk Score'
                    ? `Based on ${risks.length} risk${risks.length !== 1 ? 's' : ''}`
                    : kpiType === 'Total Mitigation Strategies'
                    ? `Across ${risks.length} risk${risks.length !== 1 ? 's' : ''}`
                    : kpiType === 'Average Risk Reduction'
                    ? `Average reduction across all strategies`
                    : kpiType === 'Priority Actions'
                    ? `Immediate and short-term actions requiring attention`
                    : typeof value === 'number'
                    ? `${value} risk${value !== 1 ? 's' : ''} identified`
                    : `${value} identified`}
                </p>
              </div>
            </div>

            {/* Additional Information */}
            {kpiType === 'Entities Affected' && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Affected Entities</h3>
                <div className="bg-white rounded-lg p-4 shadow-sm">
                  <div className="flex flex-wrap gap-2">
                    {getUniqueEntities().length > 0 ? (
                      getUniqueEntities().map((entity, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                        >
                          {entity}
                        </span>
                      ))
                    ) : (
                      <p className="text-gray-500">No entities affected</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Risk List */}
            {kpiInfo.filteredRisks.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {kpiType === 'Total Risks Detected'
                    ? 'All Identified Risks'
                    : kpiType === 'Entities Affected'
                    ? 'Risks by Entity'
                    : kpiType === 'Average Risk Score'
                    ? 'All Risks (Score Breakdown)'
                    : kpiType === 'Total Mitigation Strategies'
                    ? 'Risks with Mitigation Strategies'
                    : kpiType === 'Average Risk Reduction'
                    ? 'Risks with Risk Reduction Data'
                    : kpiType === 'Priority Actions'
                    ? 'Risks with Priority Actions'
                    : `${kpiInfo.title} List`}
                </h3>
                <div className="space-y-3">
                  {kpiInfo.filteredRisks.map((risk) => (
                    <div
                      key={risk.id}
                      className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span
                              className={`px-2 py-1 rounded text-xs font-semibold border ${getPriorityColor(
                                risk.priority
                              )}`}
                            >
                              {risk.priority}
                            </span>
                            <span className="text-sm text-gray-500">
                              Score: {risk.riskScore.toFixed(1)}
                            </span>
                          </div>
                          <h4 className="font-semibold text-gray-900 mb-1">{risk.title}</h4>
                          <p className="text-sm text-gray-600 mb-2">{risk.impact}</p>
                          <div className="flex flex-wrap gap-2">
                            <span className="text-xs text-gray-500">
                              Category: {risk.category}
                            </span>
                            {risk.affectedEntities.length > 0 && (
                              <span className="text-xs text-gray-500">
                                Entities: {risk.affectedEntities.slice(0, 3).join(', ')}
                                {risk.affectedEntities.length > 3 && '...'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {kpiInfo.filteredRisks.length === 0 && kpiType !== 'Entities Affected' && (
              <div className="bg-white rounded-lg p-8 text-center">
                <Icon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No risks found for this category</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

