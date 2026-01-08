import { motion } from 'motion/react';
import { Play, CheckSquare, Square } from 'lucide-react';
import type { AnalysisConfig } from '../types';

interface ControlPanelProps {
  config: AnalysisConfig;
  onConfigChange: (config: AnalysisConfig) => void;
  onStartAnalysis: () => void;
  analysisStarted: boolean;
  isLoading?: boolean;
}

export function ControlPanel({
  config,
  onConfigChange,
  onStartAnalysis,
  analysisStarted,
  isLoading = false,
}: ControlPanelProps) {
  const handleModuleToggle = (module: keyof AnalysisConfig['modules']) => {
    onConfigChange({
      ...config,
      modules: {
        ...config.modules,
        [module]: !config.modules[module],
      },
    });
  };

  const allSelected = Object.values(config.modules).every((v) => v);
  const noneSelected = Object.values(config.modules).every((v) => !v);

  const handleSelectAll = () => {
    const newValue = !allSelected;
    onConfigChange({
      ...config,
      modules: {
        suppliers: newValue,
        manufacturing: newValue,
        inventory: newValue,
        demand: newValue,
        transportation: newValue,
        externalFactors: newValue,
      },
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-md p-6"
    >
      <h2 className="text-2xl mb-6">Control Panel</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Forecast Horizon Slider */}
        <div className="space-y-3">
          <label className="block">
            <span className="text-gray-700">Forecast Horizon</span>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-3xl text-[#1769FF]">{config.forecastHorizon}</span>
              <span className="text-gray-500">days</span>
            </div>
          </label>
          <input
            type="range"
            min="30"
            max="60"
            value={config.forecastHorizon}
            onChange={(e) =>
              onConfigChange({ ...config, forecastHorizon: Number(e.target.value) })
            }
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#1769FF]"
          />
          <div className="flex justify-between text-sm text-gray-500">
            <span>30 days</span>
            <span>60 days</span>
          </div>
        </div>

        {/* Module Selection */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Analysis Modules</span>
            <button
              onClick={handleSelectAll}
              className="text-sm text-[#1769FF] hover:underline flex items-center gap-1"
            >
              {allSelected ? (
                <>
                  <CheckSquare className="w-4 h-4" />
                  Deselect All
                </>
              ) : (
                <>
                  <Square className="w-4 h-4" />
                  Select All
                </>
              )}
            </button>
          </div>
          <div className="space-y-2">
            {[
              { key: 'suppliers', label: 'Suppliers' },
              { key: 'manufacturing', label: 'Manufacturing' },
              { key: 'inventory', label: 'Inventory' },
              { key: 'demand', label: 'Demand' },
              { key: 'transportation', label: 'Transportation' },
              { key: 'externalFactors', label: 'External Factors' },
            ].map(({ key, label }) => (
              <label key={key} className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={config.modules[key as keyof typeof config.modules]}
                  onChange={() =>
                    handleModuleToggle(key as keyof typeof config.modules)
                  }
                  className="w-4 h-4 text-[#1769FF] border-gray-300 rounded focus:ring-[#1769FF] cursor-pointer"
                />
                <span className="text-gray-700 group-hover:text-[#1769FF] transition-colors">
                  {label}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Risk Threshold & Start Button */}
        <div className="space-y-4">
          <div className="space-y-3">
            <label className="block">
              <span className="text-gray-700">Risk Threshold</span>
              <select
                value={config.riskThreshold}
                onChange={(e) =>
                  onConfigChange({ ...config, riskThreshold: Number(e.target.value) })
                }
                className="mt-2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1769FF] focus:border-transparent"
              >
                <option value={0}>All Risks (0+)</option>
                <option value={50}>Medium+ (50+)</option>
                <option value={70}>High+ (70+)</option>
                <option value={90}>Critical (90+)</option>
              </select>
            </label>
          </div>

          {/* Start Analysis Button */}
          <motion.button
            onClick={onStartAnalysis}
            disabled={noneSelected || isLoading}
            whileHover={!noneSelected && !isLoading ? { scale: 1.02 } : {}}
            whileTap={!noneSelected && !isLoading ? { scale: 0.98 } : {}}
            animate={
              !noneSelected && !analysisStarted && !isLoading
                ? {
                    boxShadow: [
                      '0 0 0 0 rgba(23, 105, 255, 0.7)',
                      '0 0 0 10px rgba(23, 105, 255, 0)',
                    ],
                  }
                : {}
            }
            transition={{ duration: 2, repeat: Infinity }}
            className={`w-full py-4 rounded-lg text-white flex items-center justify-center gap-2 transition-all ${
              noneSelected || isLoading
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-gradient-to-r from-[#1769FF] to-[#0d4fb8] hover:from-[#0d4fb8] hover:to-[#1769FF] shadow-lg'
            }`}
          >
            <Play className="w-5 h-5" />
            {isLoading ? 'Analyzing...' : analysisStarted ? 'Re-run Analysis' : 'Start Analysis'}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
