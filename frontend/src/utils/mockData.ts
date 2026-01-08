import type { Risk, AnalysisConfig, SummaryMetrics, RiskCategory, Priority } from '../types';

export function generateMockRisks(config: AnalysisConfig): Risk[] {
  const risks: Risk[] = [];
  const activeModules = Object.entries(config.modules)
    .filter(([_, active]) => active)
    .map(([module]) => moduleToCategory(module));

  const riskTemplates = [
    {
      category: 'Suppliers' as RiskCategory,
      scenarios: [
        {
          title: 'Supplier Capacity Constraint',
          impact: 'Critical supplier experiencing 40% capacity reduction',
          rootCauses: [
            'Labor shortage at supplier facility',
            'Equipment maintenance downtime',
            'Raw material scarcity',
          ],
          affectedEntities: ['Acme Manufacturing Ltd', 'Global Parts Inc', 'TechSupply Co'],
          forecastedMetrics: [
            { metric: 'Supplier Capacity', current: 100, forecasted: 60, unit: '%' },
            { metric: 'Lead Time', current: 14, forecasted: 28, unit: 'days' },
            { metric: 'Fill Rate', current: 98, forecasted: 72, unit: '%' },
          ],
        },
        {
          title: 'Supplier Financial Instability',
          impact: 'Key supplier showing signs of financial distress',
          rootCauses: [
            'Declining cash flow',
            'High debt-to-equity ratio',
            'Missed payment deadlines',
          ],
          affectedEntities: ['Beta Components', 'Delta Materials'],
          forecastedMetrics: [
            { metric: 'Payment Terms', current: 30, forecasted: 15, unit: 'days' },
            { metric: 'Credit Rating', current: 85, forecasted: 62, unit: 'score' },
          ],
        },
      ],
    },
    {
      category: 'Manufacturing' as RiskCategory,
      scenarios: [
        {
          title: 'Production Line Bottleneck',
          impact: 'Assembly line #3 forecasted to exceed 95% utilization',
          rootCauses: [
            'Increased demand surge',
            'Equipment aging and slower cycle times',
            'Limited staffing during peak shifts',
          ],
          affectedEntities: ['Plant A - Line 3', 'Plant B - Line 1'],
          forecastedMetrics: [
            { metric: 'Capacity Utilization', current: 78, forecasted: 96, unit: '%' },
            { metric: 'Cycle Time', current: 45, forecasted: 62, unit: 'min' },
            { metric: 'Output', current: 1200, forecasted: 980, unit: 'units/day' },
          ],
        },
        {
          title: 'Quality Control Issues',
          impact: 'Predicted increase in defect rate',
          rootCauses: [
            'Supplier material variance',
            'Process parameter drift',
            'Operator training gaps',
          ],
          affectedEntities: ['Quality Line 2', 'Inspection Station 4'],
          forecastedMetrics: [
            { metric: 'Defect Rate', current: 2.1, forecasted: 5.8, unit: '%' },
            { metric: 'Rework Cost', current: 12000, forecasted: 34000, unit: 'USD' },
          ],
        },
      ],
    },
    {
      category: 'Inventory' as RiskCategory,
      scenarios: [
        {
          title: 'Critical Component Stockout Risk',
          impact: 'SKU #A1234 projected to fall below safety stock',
          rootCauses: [
            'Supplier delivery delays',
            'Unexpected demand spike',
            'Inaccurate forecast models',
          ],
          affectedEntities: ['SKU-A1234', 'SKU-B5678', 'SKU-C9012'],
          forecastedMetrics: [
            { metric: 'Stock Level', current: 850, forecasted: 120, unit: 'units' },
            { metric: 'Safety Stock', current: 500, forecasted: 500, unit: 'units' },
            { metric: 'Days of Supply', current: 28, forecasted: 4, unit: 'days' },
          ],
        },
        {
          title: 'Excess Inventory Buildup',
          impact: 'Slow-moving items accumulating beyond optimal levels',
          rootCauses: [
            'Demand forecast overestimation',
            'Product lifecycle changes',
            'Order policy inefficiencies',
          ],
          affectedEntities: ['Warehouse North', 'Warehouse East'],
          forecastedMetrics: [
            { metric: 'Inventory Turns', current: 6.2, forecasted: 2.8, unit: 'turns/year' },
            { metric: 'Carrying Cost', current: 45000, forecasted: 78000, unit: 'USD/month' },
          ],
        },
      ],
    },
    {
      category: 'Demand' as RiskCategory,
      scenarios: [
        {
          title: 'Demand Volatility Spike',
          impact: 'Forecasted 35% increase in demand variance',
          rootCauses: [
            'Market uncertainty',
            'Competitor product launch',
            'Seasonal pattern disruption',
          ],
          affectedEntities: ['Product Line A', 'Product Line C', 'Region East'],
          forecastedMetrics: [
            { metric: 'Demand Mean', current: 5000, forecasted: 6800, unit: 'units' },
            { metric: 'Demand Std Dev', current: 450, forecasted: 1200, unit: 'units' },
            { metric: 'Forecast Accuracy', current: 92, forecasted: 76, unit: '%' },
          ],
        },
        {
          title: 'Market Demand Shift',
          impact: 'Customer preference shifting to alternative products',
          rootCauses: [
            'New technology adoption',
            'Price sensitivity increase',
            'Brand perception changes',
          ],
          affectedEntities: ['Legacy Product Series', 'Mid-Tier Segment'],
          forecastedMetrics: [
            { metric: 'Market Share', current: 24, forecasted: 18, unit: '%' },
            { metric: 'Sales Volume', current: 12000, forecasted: 8500, unit: 'units' },
          ],
        },
      ],
    },
    {
      category: 'Transportation' as RiskCategory,
      scenarios: [
        {
          title: 'Shipping Delay Risk',
          impact: 'Ocean freight routes showing increased transit times',
          rootCauses: [
            'Port congestion',
            'Carrier capacity constraints',
            'Customs processing delays',
          ],
          affectedEntities: ['Route Asia-NA', 'Route EU-NA', 'Carrier XYZ'],
          forecastedMetrics: [
            { metric: 'Transit Time', current: 21, forecasted: 35, unit: 'days' },
            { metric: 'On-Time Delivery', current: 94, forecasted: 78, unit: '%' },
            { metric: 'Freight Cost', current: 2800, forecasted: 4200, unit: 'USD' },
          ],
        },
        {
          title: 'Last-Mile Delivery Disruption',
          impact: 'Regional carrier experiencing service degradation',
          rootCauses: [
            'Driver shortage',
            'Fuel price volatility',
            'Route optimization issues',
          ],
          affectedEntities: ['Region Southwest', 'Carrier ABC'],
          forecastedMetrics: [
            { metric: 'Delivery Time', current: 2.5, forecasted: 4.8, unit: 'days' },
            { metric: 'Cost per Delivery', current: 8.5, forecasted: 12.3, unit: 'USD' },
          ],
        },
      ],
    },
    {
      category: 'External Factors' as RiskCategory,
      scenarios: [
        {
          title: 'Geopolitical Tension Impact',
          impact: 'Trade policy changes affecting tariffs and regulations',
          rootCauses: [
            'International trade disputes',
            'Regulatory changes',
            'Economic sanctions',
          ],
          affectedEntities: ['Region APAC', 'Supplier Country X'],
          forecastedMetrics: [
            { metric: 'Tariff Rate', current: 5, forecasted: 18, unit: '%' },
            { metric: 'Compliance Cost', current: 15000, forecasted: 42000, unit: 'USD/month' },
          ],
        },
        {
          title: 'Severe Weather Forecast',
          impact: 'Hurricane season threatening Gulf Coast operations',
          rootCauses: [
            'Climate pattern changes',
            'Seasonal weather forecasts',
            'Facility location exposure',
          ],
          affectedEntities: ['Plant Gulf Coast', 'Warehouse Houston'],
          forecastedMetrics: [
            { metric: 'Weather Severity', current: 2, forecasted: 7, unit: 'index' },
            { metric: 'Disruption Probability', current: 15, forecasted: 68, unit: '%' },
          ],
        },
      ],
    },
  ];

  // Generate risks based on active modules and threshold
  riskTemplates.forEach((template) => {
    if (activeModules.includes(template.category)) {
      template.scenarios.forEach((scenario, idx) => {
        const riskScore = Math.floor(Math.random() * 40) + 60; // 60-100
        if (riskScore >= config.riskThreshold) {
          const priority = getRiskPriority(riskScore);
          const probability = Math.floor(Math.random() * 30) + 60; // 60-90
          const severity = Math.floor(Math.random() * 30) + 60; // 60-90

          risks.push({
            id: `RISK-${template.category.substring(0, 3).toUpperCase()}-${String(
              risks.length + 1
            ).padStart(4, '0')}`,
            category: template.category,
            title: scenario.title,
            impact: scenario.impact,
            riskScore,
            priority,
            timeline: getTimeline(config.forecastHorizon),
            affectedEntities: scenario.affectedEntities,
            probability,
            severity,
            rootCauses: scenario.rootCauses,
            forecastedMetrics: scenario.forecastedMetrics,
            mitigationStrategies: generateMitigationStrategies(
              `RISK-${template.category.substring(0, 3).toUpperCase()}-${String(
                risks.length + 1
              ).padStart(4, '0')}`,
              template.category
            ),
          });
        }
      });
    }
  });

  return risks;
}

function moduleToCategory(module: string): RiskCategory {
  const map: Record<string, RiskCategory> = {
    suppliers: 'Suppliers',
    manufacturing: 'Manufacturing',
    inventory: 'Inventory',
    demand: 'Demand',
    transportation: 'Transportation',
    externalFactors: 'External Factors',
  };
  return map[module] || 'Suppliers';
}

function getRiskPriority(score: number): Priority {
  if (score >= 90) return 'Critical';
  if (score >= 70) return 'High';
  if (score >= 50) return 'Medium';
  return 'Low';
}

function getTimeline(horizon: number): string {
  const days = Math.floor(Math.random() * horizon) + 5;
  return `${days} days`;
}

function generateMitigationStrategies(
  riskId: string,
  category: RiskCategory
): any[] {
  const strategies = [
    {
      id: `MIT-${riskId}-001`,
      riskId,
      name: 'Emergency Response Protocol',
      description: 'Activate emergency procurement and alternative sourcing',
      timeline: 'Immediate' as const,
      timelineDays: '<7 days',
      cost: '$50K - $100K',
      riskReduction: 35,
      pros: ['Quick implementation', 'Immediate impact', 'Proven effectiveness'],
      cons: ['Higher costs', 'Temporary solution', 'Resource intensive'],
    },
    {
      id: `MIT-${riskId}-002`,
      riskId,
      name: 'Process Optimization',
      description: 'Implement lean manufacturing and capacity planning improvements',
      timeline: 'Short-term' as const,
      timelineDays: '7-30 days',
      cost: '$100K - $250K',
      riskReduction: 55,
      pros: ['Sustainable solution', 'Improves efficiency', 'Long-term benefits'],
      cons: ['Requires coordination', 'Training needed', 'Medium timeline'],
    },
    {
      id: `MIT-${riskId}-003`,
      riskId,
      name: 'Strategic Partnership Development',
      description: 'Establish backup suppliers and diversify supply base',
      timeline: 'Long-term' as const,
      timelineDays: '>30 days',
      cost: '$250K - $500K',
      riskReduction: 75,
      pros: [
        'Comprehensive risk reduction',
        'Strategic advantage',
        'Network resilience',
      ],
      cons: ['Significant investment', 'Long implementation', 'Complex negotiations'],
    },
  ];

  return strategies;
}

export function calculateSummaryMetrics(risks: Risk[]): SummaryMetrics {
  const uniqueEntities = new Set<string>();
  risks.forEach((risk) => {
    risk.affectedEntities.forEach((entity) => uniqueEntities.add(entity));
  });

  const averageRiskScore =
    risks.length > 0
      ? Math.round(risks.reduce((sum, risk) => sum + risk.riskScore, 0) / risks.length)
      : 0;

  return {
    totalRisks: risks.length,
    criticalRisks: risks.filter((r) => r.priority === 'Critical').length,
    highPriorityRisks: risks.filter((r) => r.priority === 'High').length,
    mediumPriorityRisks: risks.filter((r) => r.priority === 'Medium').length,
    entitiesAffected: uniqueEntities.size,
    averageRiskScore,
  };
}

// Chart data generators
export function generateSupplierForecast(horizon: number) {
  const data = [];
  for (let i = 0; i <= horizon; i++) {
    const value = 95 - i * 0.6 + Math.random() * 5;
    data.push({
      day: i,
      predicted: Math.max(55, value),
      upperBound: Math.max(60, value + 8),
      lowerBound: Math.max(50, value - 8),
      threshold: 70,
    });
  }
  return data;
}

export function generateManufacturingForecast(horizon: number) {
  const data = [];
  for (let i = 0; i <= horizon; i++) {
    const value = 75 + i * 0.4 + Math.random() * 5;
    data.push({
      day: i,
      utilization: Math.min(98, value),
      criticalThreshold: 90,
    });
  }
  return data;
}

export function generateInventoryForecast(horizon: number) {
  const data = [];
  for (let i = 0; i <= horizon; i++) {
    const stockLevel = Math.max(100, 850 - i * 15 + Math.random() * 50);
    data.push({
      day: i,
      stockLevel,
      safetyStock: 500,
      reorderPoint: 600,
    });
  }
  return data;
}

export function generateDemandForecast(horizon: number) {
  const data = [];
  for (let i = 0; i <= horizon; i++) {
    const historical = i < horizon / 2 ? 5000 + Math.random() * 400 : null;
    const forecasted = i >= horizon / 3 ? 5000 + i * 30 + Math.random() * 600 : null;
    data.push({
      day: i,
      historical,
      forecasted,
      volatilityHigh: i > horizon * 0.6,
    });
  }
  return data;
}

export function generateTransportationForecast(horizon: number) {
  const routes = ['Asia-NA', 'EU-NA', 'SA-NA', 'APAC-EU'];
  return routes.map((route) => ({
    route,
    baseline: 21 + Math.random() * 3,
    forecasted: 28 + Math.random() * 8,
    delayed: Math.random() > 0.5,
  }));
}

export function generateExternalFactorsForecast(horizon: number) {
  return {
    weather: Array.from({ length: 10 }, (_, i) => ({
      week: `W${i + 1}`,
      severity: Math.floor(Math.random() * 8) + 1,
    })),
    tariffs: Array.from({ length: 6 }, (_, i) => ({
      month: `M${i + 1}`,
      rate: 5 + i * 2 + Math.random() * 3,
    })),
    geopolitical: Array.from({ length: 5 }, (_, i) => ({
      region: ['APAC', 'EU', 'NA', 'SA', 'MEA'][i],
      riskIndex: Math.floor(Math.random() * 40) + 40,
    })),
  };
}
