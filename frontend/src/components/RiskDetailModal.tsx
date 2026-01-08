import { motion, AnimatePresence } from 'motion/react';
import { X, AlertCircle, TrendingUp, DollarSign, Clock, CheckCircle } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import type { Risk, Priority } from '../types';
import { useState } from 'react';

interface RiskDetailModalProps {
  risk: Risk;
  onClose: () => void;
}

export function RiskDetailModal({ risk, onClose }: RiskDetailModalProps) {
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null);

  const getPriorityColor = (priority: Priority) => {
    const colors = {
      Critical: 'bg-red-100 text-red-800 border-red-300',
      High: 'bg-orange-100 text-orange-800 border-orange-300',
      Medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      Low: 'bg-green-100 text-green-800 border-green-300',
    };
    return colors[priority];
  };

  const getGaugeColor = (score: number) => {
    if (score >= 90) return '#dc2626';
    if (score >= 70) return '#f97316';
    if (score >= 50) return '#eab308';
    return '#22c55e';
  };

  // Generate mini chart data from forecasted metrics
  const chartData = risk.forecastedMetrics[0]
    ? Array.from({ length: 30 }, (_, i) => ({
        day: i,
        value:
          risk.forecastedMetrics[0].current +
          ((risk.forecastedMetrics[0].forecasted - risk.forecastedMetrics[0].current) /
            30) *
            i +
          Math.random() * 5,
        threshold: risk.forecastedMetrics[0].current,
      }))
    : [];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="bg-[#191919] text-white p-6 sticky top-0 z-10">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-2">
                  <code className="text-xl bg-white bg-opacity-20 px-3 py-1 rounded">
                    {risk.id}
                  </code>
                  <span
                    className={`px-4 py-1 rounded-full text-sm border-2 ${getPriorityColor(
                      risk.priority
                    )}`}
                  >
                    {risk.priority}
                  </span>
                </div>
                <h2 className="text-2xl mb-2">{risk.title}</h2>
                <p className="text-gray-300">{risk.impact}</p>
              </div>
              <div className="flex items-center gap-4">
                {/* Risk Score Gauge */}
                <div className="text-center">
                  <div className="relative w-24 h-24">
                    <svg className="transform -rotate-90 w-24 h-24">
                      <circle
                        cx="48"
                        cy="48"
                        r="40"
                        stroke="#374151"
                        strokeWidth="8"
                        fill="none"
                      />
                      <circle
                        cx="48"
                        cy="48"
                        r="40"
                        stroke={getGaugeColor(risk.riskScore)}
                        strokeWidth="8"
                        fill="none"
                        strokeDasharray={`${(risk.riskScore / 100) * 251.2} 251.2`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-2xl">{risk.riskScore}</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-300 mt-1">Risk Score</p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Timeline Countdown */}
            <div className="mt-4 flex items-center gap-2 text-gray-300">
              <Clock className="w-5 h-5" />
              <span>Projected occurrence in: {risk.timeline}</span>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Three Columns */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {/* Risk Profile */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-[#1769FF]" />
                  Risk Profile
                </h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-600">Category</p>
                    <p className="text-[#1769FF]">{risk.category}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Probability</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-[#1769FF]"
                          style={{ width: `${risk.probability}%` }}
                        />
                      </div>
                      <span className="text-sm">{risk.probability}%</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Severity</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-orange-500"
                          style={{ width: `${risk.severity}%` }}
                        />
                      </div>
                      <span className="text-sm">{risk.severity}%</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Affected Entities</p>
                    <div className="space-y-1">
                      {risk.affectedEntities.map((entity) => (
                        <div
                          key={entity}
                          className="text-sm bg-white px-2 py-1 rounded border border-gray-200"
                        >
                          {entity}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Root Causes */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg mb-4">Root Causes</h3>
                <ul className="space-y-2">
                  {risk.rootCauses.map((cause, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <div className="w-2 h-2 bg-[#1769FF] rounded-full mt-1.5 flex-shrink-0" />
                      <span className="text-sm">{cause}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Forecasted Metrics */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg mb-4">Forecasted Metrics</h3>
                <div className="space-y-3">
                  {risk.forecastedMetrics.map((metric, idx) => (
                    <div key={idx} className="bg-white rounded-lg p-3">
                      <p className="text-sm text-gray-600">{metric.metric}</p>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-gray-500 line-through text-sm">
                          {metric.current} {metric.unit}
                        </span>
                        <TrendingUp className="w-4 h-4 text-orange-500" />
                        <span className="text-orange-600">
                          {metric.forecasted} {metric.unit}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Forecast Visualization */}
            {chartData.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h3 className="text-lg mb-4">30-Day Forecast Trend</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#fff',
                        border: '1px solid #e5e7eb',
                      }}
                    />
                    <ReferenceLine
                      y={risk.forecastedMetrics[0]?.current}
                      stroke="#10b981"
                      strokeDasharray="3 3"
                      label="Baseline"
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#1769FF"
                      strokeWidth={3}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Mitigation Strategies */}
            <div>
              <h3 className="text-lg mb-4">Mitigation Strategies</h3>
              <div className="space-y-3">
                {risk.mitigationStrategies.map((strategy) => (
                  <div
                    key={strategy.id}
                    className="border border-gray-200 rounded-lg overflow-hidden"
                  >
                    <button
                      onClick={() =>
                        setExpandedStrategy(
                          expandedStrategy === strategy.id ? null : strategy.id
                        )
                      }
                      className="w-full p-4 bg-white hover:bg-gray-50 transition-colors text-left"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="mb-1">{strategy.name}</h4>
                          <p className="text-sm text-gray-600">{strategy.description}</p>
                        </div>
                        <div className="flex items-center gap-4 ml-4">
                          <div className="text-center">
                            <Clock className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                            <p className="text-xs text-gray-600">
                              {strategy.timelineDays}
                            </p>
                          </div>
                          <div className="text-center">
                            <DollarSign className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                            <p className="text-xs text-gray-600">{strategy.cost}</p>
                          </div>
                          <div className="text-center">
                            <TrendingUp className="w-5 h-5 text-green-600 mx-auto mb-1" />
                            <p className="text-xs text-gray-600">
                              -{strategy.riskReduction}%
                            </p>
                          </div>
                        </div>
                      </div>
                    </button>

                    {expandedStrategy === strategy.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="bg-gray-50 p-4 border-t border-gray-200"
                      >
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <h5 className="text-sm mb-2 flex items-center gap-2 text-green-600">
                              <CheckCircle className="w-4 h-4" />
                              Pros
                            </h5>
                            <ul className="space-y-1">
                              {strategy.pros.map((pro, idx) => (
                                <li key={idx} className="text-sm text-gray-700 flex gap-2">
                                  <span>•</span>
                                  <span>{pro}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <h5 className="text-sm mb-2 flex items-center gap-2 text-orange-600">
                              <AlertCircle className="w-4 h-4" />
                              Cons
                            </h5>
                            <ul className="space-y-1">
                              {strategy.cons.map((con, idx) => (
                                <li key={idx} className="text-sm text-gray-700 flex gap-2">
                                  <span>•</span>
                                  <span>{con}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
