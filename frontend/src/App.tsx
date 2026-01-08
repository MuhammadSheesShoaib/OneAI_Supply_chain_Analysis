import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { AlertCircle, RefreshCw, Loader2, Play } from 'lucide-react';
import { ControlPanel } from './components/ControlPanel';
import { SummaryCards } from './components/SummaryCards';
import { ForecastCharts } from './components/ForecastCharts';
import { RiskTable } from './components/RiskTable';
import { RiskDetailModal } from './components/RiskDetailModal';
import { MitigationPanel } from './components/MitigationPanel';
import { DemoPage } from './pages/DemoPage';
// Removed mock data - only using backend data
import {
  runAnalysis,
  checkHealth,
  transformAnalysisToRisks,
  transformSummary,
  ApiError,
  type AnalysisResponse,
} from './api/supplyChainApi';
import type { Risk, AnalysisConfig, SummaryMetrics } from './types';

// Module key to API module mapping
const MODULE_API_MAP: Record<string, string> = {
  suppliers: 'suppliers',
  manufacturing: 'manufacturing',
  inventory: 'inventory',
  demand: 'demand',
  transportation: 'transportation',
  externalFactors: 'external',
};

export default function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'demo'>('dashboard');
  
  const [config, setConfig] = useState<AnalysisConfig>({
    forecastHorizon: 45,
    modules: {
      suppliers: true,
      manufacturing: true,
      inventory: true,
      demand: true,
      transportation: true,
      externalFactors: true,
    },
    riskThreshold: 50,
  });

  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [selectedRisk, setSelectedRisk] = useState<Risk | null>(null);
  const [summaryMetrics, setSummaryMetrics] = useState<SummaryMetrics | null>(null);
  const [analysisResponse, setAnalysisResponse] = useState<AnalysisResponse | null>(null);
  const [useMockData, setUseMockData] = useState(false);

  const handleStartAnalysis = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    // Get active modules as API module names
    const activeModules = Object.entries(config.modules)
      .filter(([_, active]) => active)
      .map(([key]) => MODULE_API_MAP[key]);

    try {
      // First check if backend is available
      await checkHealth();

      // Run the analysis
      const response = await runAnalysis(
        config.forecastHorizon,
        activeModules,
        config.riskThreshold,
        true // include mitigations
      );

      setAnalysisResponse(response);

      // Transform API response to frontend format
      const transformedRisks = transformAnalysisToRisks(response);
      setRisks(transformedRisks);

      // Transform summary
      const summary = transformSummary(response.summary, transformedRisks);
      setSummaryMetrics(summary);

      setAnalysisStarted(true);
      setUseMockData(false);
    } catch (err) {
      console.error('API Error:', err);
      
      // Show error - no mock data fallback
      if (err instanceof ApiError) {
        if (err.statusCode === 503) {
          setError('Backend service unavailable. Please ensure the backend is running on port 8000.');
        } else {
          setError(`Backend error (${err.statusCode}): ${err.message}`);
        }
      } else if (err instanceof TypeError && err.message.includes('fetch')) {
        setError('Cannot connect to backend server. Please ensure the backend is running on http://localhost:8000');
      } else {
        setError(err instanceof Error ? err.message : 'Analysis failed. Please check backend logs.');
      }

      // Don't set analysisStarted or use mock data
      setAnalysisStarted(false);
      setRisks([]);
      setSummaryMetrics(null);
      setAnalysisResponse(null);
      setUseMockData(false);
    } finally {
      setIsLoading(false);
    }
  }, [config]);

  const handleRetry = useCallback(() => {
    setError(null);
    handleStartAnalysis();
  }, [handleStartAnalysis]);

  // Show Demo page if selected (after all hooks are declared)
  if (currentPage === 'demo') {
    return <DemoPage onBack={() => setCurrentPage('dashboard')} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-[#191919] text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl">Supply Chain Risk Analysis Dashboard</h1>
              <p className="text-gray-400 mt-1">
                Real-time risk forecasting and mitigation strategies
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setCurrentPage('demo')}
                className="flex items-center gap-2 px-4 py-2 bg-[#1769FF] hover:bg-[#0d4fb8] rounded-lg transition-colors"
              >
                <Play className="w-4 h-4" />
                Watch Demo
              </button>
              {analysisStarted && analysisResponse && (
                <>
                  <span className="bg-green-500/20 text-green-300 px-3 py-1 rounded-full text-sm">
                    Analysis ID: {analysisResponse.analysis_id.slice(0, 8)}...
                  </span>
                  <span className="bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full text-sm">
                    {new Date(analysisResponse.timestamp).toLocaleString()}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Error Banner */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-orange-50 border border-orange-300 rounded-lg p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-orange-500" />
                <span className="text-orange-800">{error}</span>
              </div>
              <button
                onClick={handleRetry}
                className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Retry
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Control Panel */}
        <ControlPanel
          config={config}
          onConfigChange={setConfig}
          onStartAnalysis={handleStartAnalysis}
          analysisStarted={analysisStarted}
          isLoading={isLoading}
        />

        {/* Loading State */}
        <AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="bg-white rounded-lg shadow-md p-12 flex flex-col items-center justify-center gap-4"
            >
              <Loader2 className="w-12 h-12 text-[#1769FF] animate-spin" />
              <div className="text-center">
                <p className="text-xl text-gray-700">Running Analysis...</p>
                <p className="text-gray-500 mt-1">
                  Processing forecasts and identifying risks
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results Section - Only show after analysis started and not loading */}
        {analysisStarted && !isLoading && summaryMetrics && (
          <>
            {/* Summary Cards */}
            <SummaryCards metrics={summaryMetrics} risks={risks} />

            {/* Forecast Charts */}
            <ForecastCharts 
              config={config} 
              risks={risks} 
              forecastData={analysisResponse?.forecasts}
            />

            {/* Risk Table */}
            <RiskTable risks={risks} onViewDetails={setSelectedRisk} />

            {/* Mitigation Panel */}
            <MitigationPanel risks={risks} />
          </>
        )}
      </main>

      {/* Risk Detail Modal */}
      {selectedRisk && (
        <RiskDetailModal risk={selectedRisk} onClose={() => setSelectedRisk(null)} />
      )}
    </div>
  );
}
