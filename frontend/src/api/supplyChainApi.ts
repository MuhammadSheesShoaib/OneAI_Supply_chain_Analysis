/**
 * API service for Supply Chain Predictor backend integration.
 * Connects to FastAPI backend running on port 8000.
 */

const API_BASE_URL = '/api';

// ==================== Request Types ====================

export interface AnalysisRequestPayload {
  forecast_horizon: number;
  modules: string[];
  risk_threshold: number;
  include_mitigations: boolean;
}

// ==================== Response Types ====================

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  data_status: Record<string, boolean>;
}

export interface ForecastDataPoint {
  ds: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
  trend?: number;
}

export interface ForecastResult {
  entity_id: string;
  entity_name?: string;
  metric: string;
  historical_avg: number;
  forecasted_avg: number;
  forecast_data: ForecastDataPoint[];
  change_percentage: number;
}

export interface AffectedEntities {
  suppliers: string[];
  plants: string[];
  warehouses: string[];
  skus: string[];
  routes: string[];
  regions: string[];
}

export interface ForecastedMetric {
  metric_name: string;
  forecasted_value: number;
  baseline_value: number;
  change_percentage: number;
  additional_data?: Record<string, unknown>;
}

export interface ApiMitigationStrategy {
  strategy_name: string;
  action_steps: string[];
  timeline_days: number;
  estimated_cost: number;
  risk_reduction: number;
  dependencies: string[];
  pros: string[];
  cons: string[];
}

export interface RiskItem {
  risk_id: string;
  category: string;
  sub_categories: string[];
  impact: string;
  severity: string;
  probability: number;
  risk_score: number;
  priority: string;
  timeline_days: number;
  affected_entities: AffectedEntities;
  forecasted_metrics: ForecastedMetric[];
  root_causes: string[];
  mitigations: ApiMitigationStrategy[];
}

export interface AnalysisSummary {
  total_risks: number;
  critical_risks: number;
  high_risks: number;
  medium_risks: number;
  low_risks: number;
  total_entities_affected: number;
}

export interface ActionRecommendation {
  action: string;
  priority: string;
  related_risks: string[];
}

export interface Recommendations {
  immediate_actions: ActionRecommendation[];
  short_term_actions: ActionRecommendation[];
  long_term_actions: ActionRecommendation[];
}

export interface AnalysisResponse {
  analysis_id: string;
  timestamp: string;
  forecast_horizon: number;
  summary: AnalysisSummary;
  forecasts: Record<string, ForecastResult[]>;
  risks: RiskItem[];
  recommendations: Recommendations;
}

export interface ModuleInfo {
  id: string;
  name: string;
  description: string;
}

export interface ModulesResponse {
  modules: ModuleInfo[];
}

export interface SupplierInfo {
  supplier_id: string;
  supplier_name: string;
  supplier_tier: string;
  supplier_region: string;
  components: string[];
}

export interface PlantInfo {
  plant_id: string;
  plant_name: string;
  plant_region: string;
  skus: string[];
}

export interface WarehouseInfo {
  warehouse_id: string;
  warehouse_name: string;
  warehouse_region: string;
  skus: string[];
}

export interface RouteInfo {
  route_id: string;
  origin: string;
  destination: string;
  carrier_id: string;
  carrier_name: string;
  mode: string;
}

export interface EntitiesResponse {
  suppliers: SupplierInfo[];
  plants: PlantInfo[];
  warehouses: WarehouseInfo[];
  routes: RouteInfo[];
  skus: string[];
  regions: string[];
}

// ==================== API Error ====================

export class ApiError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ==================== API Functions ====================

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.message || errorData.detail || `HTTP error ${response.status}`,
      errorData.details
    );
  }
  return response.json();
}

/**
 * Check API health status
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleResponse<HealthResponse>(response);
}

/**
 * Run supply chain analysis
 */
export async function runAnalysis(
  forecastHorizon: number,
  modules: string[],
  riskThreshold: number,
  includeMitigations: boolean = true
): Promise<AnalysisResponse> {
  const payload: AnalysisRequestPayload = {
    forecast_horizon: forecastHorizon,
    modules: modules,
    risk_threshold: riskThreshold,
    include_mitigations: includeMitigations,
  };

  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  return handleResponse<AnalysisResponse>(response);
}

/**
 * Get available forecast modules
 */
export async function getModules(): Promise<ModulesResponse> {
  const response = await fetch(`${API_BASE_URL}/modules`);
  return handleResponse<ModulesResponse>(response);
}

/**
 * Get available entities
 */
export async function getEntities(): Promise<EntitiesResponse> {
  const response = await fetch(`${API_BASE_URL}/entities`);
  return handleResponse<EntitiesResponse>(response);
}

/**
 * Retrieve a cached analysis by ID
 */
export async function getAnalysis(analysisId: string): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis/${analysisId}`);
  return handleResponse<AnalysisResponse>(response);
}

// ==================== Data Transformers ====================

import type { Risk, MitigationStrategy, Priority, RiskCategory, SummaryMetrics } from '../types';

/**
 * Map backend module IDs to frontend category names
 */
function mapCategoryName(category: string): RiskCategory {
  const categoryMap: Record<string, RiskCategory> = {
    'Supplier Delays': 'Suppliers',
    'Production Delays': 'Manufacturing',
    'Stock Shortages': 'Inventory',
    'Demand Volatility': 'Demand',
    'Transportation Issues': 'Transportation',
    'External Factors': 'External Factors',
    // Direct mappings if backend uses different names
    'suppliers': 'Suppliers',
    'manufacturing': 'Manufacturing',
    'inventory': 'Inventory',
    'demand': 'Demand',
    'transportation': 'Transportation',
    'external': 'External Factors',
  };
  return categoryMap[category] || 'Suppliers';
}

/**
 * Map backend priority to frontend priority
 */
function mapPriority(priority: string): Priority {
  const priorityMap: Record<string, Priority> = {
    'CRITICAL': 'Critical',
    'HIGH': 'High',
    'MEDIUM': 'Medium',
    'LOW': 'Low',
  };
  return priorityMap[priority.toUpperCase()] || 'Medium';
}

/**
 * Format timeline for display
 */
function formatTimeline(timelineDays: number): 'Immediate' | 'Short-term' | 'Long-term' {
  if (timelineDays <= 7) return 'Immediate';
  if (timelineDays <= 30) return 'Short-term';
  return 'Long-term';
}

/**
 * Format cost for display
 */
function formatCost(cost: number): string {
  if (cost < 1000) return `$${cost}`;
  if (cost < 1000000) return `$${(cost / 1000).toFixed(0)}K`;
  return `$${(cost / 1000000).toFixed(1)}M`;
}

/**
 * Transform API mitigation to frontend format
 */
function transformMitigation(
  apiMitigation: ApiMitigationStrategy,
  riskId: string,
  index: number
): MitigationStrategy {
  return {
    id: `MIT-${riskId}-${String(index + 1).padStart(3, '0')}`,
    riskId,
    name: apiMitigation.strategy_name,
    description: apiMitigation.action_steps.join(' '),
    timeline: formatTimeline(apiMitigation.timeline_days),
    timelineDays: apiMitigation.timeline_days <= 7 
      ? '<7 days' 
      : apiMitigation.timeline_days <= 30 
        ? '7-30 days' 
        : '>30 days',
    cost: formatCost(apiMitigation.estimated_cost),
    riskReduction: apiMitigation.risk_reduction,
    pros: apiMitigation.pros,
    cons: apiMitigation.cons,
  };
}

/**
 * Get all affected entities as a flat array of strings
 */
function flattenAffectedEntities(entities: AffectedEntities): string[] {
  return [
    ...entities.suppliers,
    ...entities.plants,
    ...entities.warehouses,
    ...entities.skus,
    ...entities.routes,
    ...entities.regions,
  ];
}

/**
 * Transform API risk to frontend format
 */
export function transformRisk(apiRisk: RiskItem): Risk {
  const affectedEntities = flattenAffectedEntities(apiRisk.affected_entities);
  
  return {
    id: apiRisk.risk_id,
    category: mapCategoryName(apiRisk.category),
    title: apiRisk.sub_categories.length > 0 
      ? apiRisk.sub_categories[0] 
      : apiRisk.category,
    impact: apiRisk.impact,
    riskScore: Math.round(apiRisk.risk_score),
    priority: mapPriority(apiRisk.priority),
    timeline: `${apiRisk.timeline_days} days`,
    affectedEntities,
    probability: Math.round(apiRisk.probability * 100),
    severity: apiRisk.severity === 'CRITICAL' ? 90 
      : apiRisk.severity === 'HIGH' ? 75 
      : apiRisk.severity === 'MEDIUM' ? 50 
      : 30,
    rootCauses: apiRisk.root_causes,
    forecastedMetrics: apiRisk.forecasted_metrics.map(m => ({
      metric: m.metric_name,
      current: m.baseline_value,
      forecasted: m.forecasted_value,
      unit: '',  // Backend doesn't provide units, could be added
    })),
    mitigationStrategies: apiRisk.mitigations.map((m, i) => 
      transformMitigation(m, apiRisk.risk_id, i)
    ),
  };
}

/**
 * Transform API analysis response to frontend risks array
 */
export function transformAnalysisToRisks(analysis: AnalysisResponse): Risk[] {
  return analysis.risks.map(transformRisk);
}

/**
 * Transform API summary to frontend summary metrics
 */
export function transformSummary(
  summary: AnalysisSummary, 
  risks: Risk[]
): SummaryMetrics {
  const averageRiskScore = risks.length > 0
    ? Math.round(risks.reduce((sum, r) => sum + r.riskScore, 0) / risks.length)
    : 0;

  // Calculate total mitigation strategies
  const totalMitigationStrategies = risks.reduce(
    (sum, risk) => sum + risk.mitigationStrategies.length,
    0
  );

  // Calculate average risk reduction
  const allStrategies = risks.flatMap((risk) => risk.mitigationStrategies);
  const averageRiskReduction = allStrategies.length > 0
    ? Math.round(
        allStrategies.reduce((sum, strategy) => sum + strategy.riskReduction, 0) /
        allStrategies.length
      )
    : 0;

  // Calculate priority actions (Immediate + Short-term)
  const priorityActions = allStrategies.filter(
    (strategy) => strategy.timeline === 'Immediate' || strategy.timeline === 'Short-term'
  ).length;

  return {
    totalRisks: summary.total_risks,
    criticalRisks: summary.critical_risks,
    highPriorityRisks: summary.high_risks,
    mediumPriorityRisks: summary.medium_risks,
    entitiesAffected: summary.total_entities_affected,
    averageRiskScore,
    totalMitigationStrategies,
    averageRiskReduction,
    priorityActions,
  };
}

