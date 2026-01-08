export interface AnalysisConfig {
  forecastHorizon: number;
  modules: {
    suppliers: boolean;
    manufacturing: boolean;
    inventory: boolean;
    demand: boolean;
    transportation: boolean;
    externalFactors: boolean;
  };
  riskThreshold: number;
}

export type RiskCategory =
  | 'Suppliers'
  | 'Manufacturing'
  | 'Inventory'
  | 'Demand'
  | 'Transportation'
  | 'External Factors';

export type Priority = 'Critical' | 'High' | 'Medium' | 'Low';

export interface Risk {
  id: string;
  category: RiskCategory;
  title: string;
  impact: string;
  riskScore: number;
  priority: Priority;
  timeline: string;
  affectedEntities: string[];
  probability: number;
  severity: number;
  rootCauses: string[];
  forecastedMetrics: {
    metric: string;
    current: number;
    forecasted: number;
    unit: string;
  }[];
  mitigationStrategies: MitigationStrategy[];
}

export interface MitigationStrategy {
  id: string;
  riskId: string;
  name: string;
  description: string;
  timeline: 'Immediate' | 'Short-term' | 'Long-term';
  timelineDays: string;
  cost: string;
  riskReduction: number;
  pros: string[];
  cons: string[];
}

export interface SummaryMetrics {
  totalRisks: number;
  criticalRisks: number;
  highPriorityRisks: number;
  mediumPriorityRisks: number;
  entitiesAffected: number;
  averageRiskScore: number;
  totalMitigationStrategies: number;
  averageRiskReduction: number;
  priorityActions: number;
}
