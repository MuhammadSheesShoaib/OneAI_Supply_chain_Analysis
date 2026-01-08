import { motion } from 'motion/react';
import { Clock, DollarSign, TrendingDown } from 'lucide-react';
import type { Risk, MitigationStrategy } from '../types';

interface MitigationPanelProps {
  risks: Risk[];
}

export function MitigationPanel({ risks }: MitigationPanelProps) {
  // Group all mitigation strategies by timeline
  const allStrategies: MitigationStrategy[] = risks.flatMap(
    (risk) => risk.mitigationStrategies
  );

  const strategiesByTimeline = {
    Immediate: allStrategies.filter((s) => s.timeline === 'Immediate'),
    'Short-term': allStrategies.filter((s) => s.timeline === 'Short-term'),
    'Long-term': allStrategies.filter((s) => s.timeline === 'Long-term'),
  };

  const getTimelineColor = (timeline: string) => {
    const colors: Record<string, string> = {
      Immediate: 'border-red-500 bg-red-50',
      'Short-term': 'border-orange-500 bg-orange-50',
      'Long-term': 'border-blue-500 bg-blue-50',
    };
    return colors[timeline] || 'border-gray-300 bg-gray-50';
  };

  const getTimelineHeaderColor = (timeline: string) => {
    const colors: Record<string, string> = {
      Immediate: 'bg-red-500',
      'Short-term': 'bg-orange-500',
      'Long-term': 'bg-blue-500',
    };
    return colors[timeline] || 'bg-gray-500';
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-white rounded-lg shadow-md p-6"
    >
      <h2 className="text-2xl mb-6">Mitigation Action Plan</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {Object.entries(strategiesByTimeline).map(([timeline, strategies]) => (
          <div key={timeline} className="space-y-3">
            {/* Column Header */}
            <div
              className={`${getTimelineHeaderColor(
                timeline
              )} text-white rounded-lg p-4 shadow-sm`}
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg">{timeline}</h3>
                <span className="bg-white bg-opacity-30 px-3 py-1 rounded-full text-sm">
                  {strategies.length}
                </span>
              </div>
              <p className="text-sm text-white text-opacity-90 mt-1">
                {timeline === 'Immediate' && '<7 days'}
                {timeline === 'Short-term' && '7-30 days'}
                {timeline === 'Long-term' && '>30 days'}
              </p>
            </div>

            {/* Strategy Cards */}
            <div className="space-y-3">
              {strategies.length === 0 ? (
                <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                  No strategies in this timeline
                </div>
              ) : (
                strategies.map((strategy, idx) => (
                  <motion.div
                    key={strategy.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    whileHover={{ y: -2, boxShadow: '0 8px 20px rgba(0,0,0,0.1)' }}
                    className={`border-2 rounded-lg p-4 ${getTimelineColor(
                      timeline
                    )} cursor-pointer transition-all`}
                  >
                    {/* Risk ID Badge */}
                    <code className="text-xs bg-white px-2 py-1 rounded text-gray-600">
                      {strategy.riskId}
                    </code>

                    {/* Strategy Name */}
                    <h4 className="mt-2 mb-2">{strategy.name}</h4>

                    {/* Description */}
                    <p className="text-sm text-gray-600 mb-3">
                      {strategy.description}
                    </p>

                    {/* Metrics */}
                    <div className="space-y-2 mb-3">
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-gray-500" />
                        <span className="text-gray-700">{strategy.timelineDays}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <DollarSign className="w-4 h-4 text-gray-500" />
                        <span className="text-gray-700">{strategy.cost}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <TrendingDown className="w-4 h-4 text-green-600" />
                        <span className="text-gray-700">
                          Risk reduction: {strategy.riskReduction}%
                        </span>
                      </div>
                    </div>

                  </motion.div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-6 bg-gray-50 rounded-lg p-4 flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm">Total Mitigation Strategies</p>
          <p className="text-2xl text-[#1769FF]">{allStrategies.length}</p>
        </div>
        <div>
          <p className="text-gray-600 text-sm">Average Risk Reduction</p>
          <p className="text-2xl text-green-600">
            {allStrategies.length > 0
              ? Math.round(
                  allStrategies.reduce((sum, s) => sum + s.riskReduction, 0) /
                    allStrategies.length
                )
              : 0}
            %
          </p>
        </div>
        <div>
          <p className="text-gray-600 text-sm">Priority Actions</p>
          <p className="text-2xl text-red-600">
            {strategiesByTimeline.Immediate.length}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
