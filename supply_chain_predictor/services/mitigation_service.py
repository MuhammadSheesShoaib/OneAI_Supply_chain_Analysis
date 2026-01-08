"""
Mitigation Service for generating LLM-powered mitigation recommendations.
Uses Groq API with llama-3.1-8b-instant model.
"""
import logging
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS, GROQ_MAX_RETRIES
from schemas.models import MitigationStrategy, RiskItem

logger = logging.getLogger(__name__)


class MitigationService:
    """
    Service for generating LLM-powered mitigation strategies using Groq API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the MitigationService.
        
        Args:
            api_key: Optional Groq API key (uses env variable if not provided)
        """
        self.api_key = api_key or GROQ_API_KEY
        self.model = GROQ_MODEL
        self.temperature = GROQ_TEMPERATURE
        self.max_tokens = GROQ_MAX_TOKENS
        self.max_retries = GROQ_MAX_RETRIES
        self.client = None
        
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info("MitigationService initialized with Groq client")
            except ImportError:
                logger.warning("Groq package not installed. Mitigations will use fallback.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.warning("No Groq API key provided. Mitigations will use fallback.")
    
    def _build_prompt(self, risk: Dict[str, Any]) -> str:
        """
        Build the prompt for the LLM based on risk details.
        
        Args:
            risk: Risk dictionary with all details
            
        Returns:
            Formatted prompt string
        """
        # Extract risk details
        category = risk.get("category", "Unknown")
        sub_categories = ", ".join(risk.get("sub_categories", []))
        impact = risk.get("impact", "Unknown")
        score = risk.get("risk_score", 0)
        priority = risk.get("priority", "MEDIUM")
        timeline = risk.get("timeline_days", 30)
        
        # Extract affected entities
        entities = risk.get("affected_entities", {})
        entities_str = []
        for entity_type, entity_list in entities.items():
            if entity_list:
                entities_str.append(f"{entity_type}: {', '.join(entity_list)}")
        entities_formatted = "\n".join(entities_str) if entities_str else "Not specified"
        
        # Extract root causes
        root_causes = "\n".join(f"- {c}" for c in risk.get("root_causes", ["Not specified"]))
        
        # Extract metrics
        metrics = risk.get("forecasted_metrics", [])
        if isinstance(metrics, list) and metrics:
            metrics_str = "\n".join(
                f"- {m.get('metric_name', 'Unknown')}: {m.get('forecasted_value', 0)} (baseline: {m.get('baseline_value', 0)})"
                for m in metrics
            )
        else:
            metrics_str = "Not available"
        
        prompt = f"""You are a supply chain expert. Given the following risk:

Risk Category: {category}
Sub-Categories: {sub_categories}
Business Impact: {impact}
Risk Score: {score:.1f} (Priority: {priority})
Timeline: {timeline} days until potential disruption

Context:
- Affected Entities:
{entities_formatted}

- Root Causes:
{root_causes}

- Current State/Metrics:
{metrics_str}

Generate 3-5 prioritized mitigation strategies. For EACH strategy provide:
1. Strategy Name
2. Detailed Action Steps (numbered list)
3. Implementation Timeline (in days)
4. Estimated Cost (USD)
5. Expected Risk Reduction (percentage)
6. Dependencies/Prerequisites
7. Pros and Cons

Format your response as a JSON array with these exact fields for each strategy:
[
  {{
    "strategy_name": "string",
    "action_steps": ["step1", "step2", ...],
    "timeline_days": number,
    "estimated_cost": number,
    "risk_reduction": number,
    "dependencies": ["dep1", "dep2", ...],
    "pros": ["pro1", "pro2", ...],
    "cons": ["con1", "con2", ...]
  }}
]

Respond ONLY with the JSON array, no additional text."""

        return prompt
    
    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse the LLM response to extract mitigation strategies.
        
        Args:
            response_text: Raw LLM response text
            
        Returns:
            List of mitigation strategy dictionaries
        """
        try:
            # Try direct JSON parse first
            strategies = json.loads(response_text)
            if isinstance(strategies, list):
                return self._validate_strategies(strategies)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from response
        try:
            # Look for JSON array pattern
            json_match = re.search(r'\[\s*\{.*?\}\s*\]', response_text, re.DOTALL)
            if json_match:
                strategies = json.loads(json_match.group())
                if isinstance(strategies, list):
                    return self._validate_strategies(strategies)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Try to find individual JSON objects
        try:
            objects = re.findall(r'\{[^{}]+\}', response_text)
            if objects:
                strategies = []
                for obj in objects:
                    try:
                        parsed = json.loads(obj)
                        if "strategy_name" in parsed:
                            strategies.append(parsed)
                    except json.JSONDecodeError:
                        continue
                if strategies:
                    return self._validate_strategies(strategies)
        except Exception:
            pass
        
        logger.warning("Failed to parse LLM response, using fallback")
        return []
    
    def _validate_strategies(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and clean mitigation strategies.
        
        Args:
            strategies: List of raw strategy dictionaries
            
        Returns:
            List of validated strategies
        """
        validated = []
        
        for strategy in strategies:
            try:
                clean_strategy = {
                    "strategy_name": str(strategy.get("strategy_name", "Strategy"))[:100],
                    "action_steps": [str(s)[:500] for s in strategy.get("action_steps", [])[:10]],
                    "timeline_days": max(1, int(strategy.get("timeline_days", 7))),
                    "estimated_cost": max(0, float(strategy.get("estimated_cost", 0))),
                    "risk_reduction": min(100, max(0, float(strategy.get("risk_reduction", 0)))),
                    "dependencies": [str(d)[:200] for d in strategy.get("dependencies", [])[:5]],
                    "pros": [str(p)[:200] for p in strategy.get("pros", [])[:5]],
                    "cons": [str(c)[:200] for c in strategy.get("cons", [])[:5]]
                }
                validated.append(clean_strategy)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to validate strategy: {e}")
                continue
        
        return validated
    
    def _call_groq_api(self, prompt: str, risk: Dict[str, Any]) -> Optional[str]:
        """
        Call the Groq API with retry logic.
        
        Args:
            prompt: The prompt to send
            risk: Risk dictionary for logging context
            
        Returns:
            Response text or None on failure
        """
        if not self.client:
            return None
        
        risk_id = risk.get('risk_id', 'UNKNOWN')
        logger.debug(f"[Mitigation] Calling Groq API for {risk_id} (model={self.model}, max_tokens={self.max_tokens})")
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert supply chain consultant. Provide actionable mitigation strategies in valid JSON format."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                elapsed = time.time() - start_time
                tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 'unknown'
                logger.debug(f"[Mitigation] Groq API call successful for {risk_id} "
                           f"(attempt {attempt+1}/{self.max_retries}, {elapsed:.2f}s, tokens={tokens_used})")
                
                return response.choices[0].message.content
                
            except Exception as e:
                logger.warning(f"[Mitigation] Groq API attempt {attempt + 1}/{self.max_retries} failed for {risk_id}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.debug(f"[Mitigation] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)  # Exponential backoff
        
        logger.warning(f"[Mitigation] All {self.max_retries} Groq API attempts failed for {risk_id}, using fallback")
        return None
    
    def _generate_fallback_mitigations(self, risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate fallback mitigation strategies when LLM is unavailable.
        
        Args:
            risk: Risk dictionary
            
        Returns:
            List of fallback strategies
        """
        category = risk.get("category", "")
        priority = risk.get("priority", "MEDIUM")
        
        # Base cost multiplier by priority
        cost_multiplier = {"CRITICAL": 2.0, "HIGH": 1.5, "MEDIUM": 1.0, "LOW": 0.5}.get(priority, 1.0)
        
        if "Supplier" in category:
            return [
                {
                    "strategy_name": "Activate Backup Supplier",
                    "action_steps": [
                        "Identify and contact qualified backup suppliers",
                        "Request expedited quotes and capacity confirmation",
                        "Negotiate emergency supply agreements",
                        "Place initial trial orders to verify quality",
                        "Establish regular communication channels"
                    ],
                    "timeline_days": 5,
                    "estimated_cost": 45000 * cost_multiplier,
                    "risk_reduction": 60,
                    "dependencies": ["Pre-qualified supplier list", "Budget approval"],
                    "pros": ["Immediate capacity increase", "Supply diversification"],
                    "cons": ["Higher unit costs", "Quality verification needed"]
                },
                {
                    "strategy_name": "Build Safety Stock Buffer",
                    "action_steps": [
                        "Calculate optimal safety stock levels",
                        "Place expedited orders with current supplier",
                        "Arrange additional warehouse capacity",
                        "Implement inventory monitoring system"
                    ],
                    "timeline_days": 14,
                    "estimated_cost": 75000 * cost_multiplier,
                    "risk_reduction": 40,
                    "dependencies": ["Warehouse capacity", "Working capital"],
                    "pros": ["Buffers against future delays", "No supplier change"],
                    "cons": ["Increased inventory costs", "Capital tied up"]
                },
                {
                    "strategy_name": "Negotiate Priority Allocation",
                    "action_steps": [
                        "Schedule meeting with supplier management",
                        "Present volume commitment projections",
                        "Negotiate priority production slots",
                        "Document agreements in contract amendment"
                    ],
                    "timeline_days": 7,
                    "estimated_cost": 15000 * cost_multiplier,
                    "risk_reduction": 30,
                    "dependencies": ["Supplier relationship", "Volume commitment"],
                    "pros": ["Maintains partnership", "Lower cost option"],
                    "cons": ["Dependent on supplier", "May not guarantee delivery"]
                }
            ]
        
        elif "Production" in category:
            return [
                {
                    "strategy_name": "Implement Overtime Production",
                    "action_steps": [
                        "Assess equipment capacity for extended runs",
                        "Schedule additional shifts",
                        "Coordinate with workforce management",
                        "Monitor equipment stress levels"
                    ],
                    "timeline_days": 3,
                    "estimated_cost": 35000 * cost_multiplier,
                    "risk_reduction": 45,
                    "dependencies": ["Labor availability", "Equipment condition"],
                    "pros": ["Quick implementation", "Uses existing assets"],
                    "cons": ["Higher labor costs", "Worker fatigue risk"]
                },
                {
                    "strategy_name": "Outsource to Contract Manufacturer",
                    "action_steps": [
                        "Identify qualified contract manufacturers",
                        "Share product specifications",
                        "Conduct quality audits",
                        "Transfer production batch"
                    ],
                    "timeline_days": 21,
                    "estimated_cost": 120000 * cost_multiplier,
                    "risk_reduction": 55,
                    "dependencies": ["CM availability", "Quality certification"],
                    "pros": ["Adds capacity", "Maintains delivery"],
                    "cons": ["Higher costs", "Quality control challenges"]
                }
            ]
        
        elif "Stock" in category or "Inventory" in category:
            return [
                {
                    "strategy_name": "Expedite Inbound Shipments",
                    "action_steps": [
                        "Identify in-transit inventory",
                        "Upgrade to air freight where possible",
                        "Coordinate with carriers for priority handling",
                        "Track shipments in real-time"
                    ],
                    "timeline_days": 2,
                    "estimated_cost": 25000 * cost_multiplier,
                    "risk_reduction": 35,
                    "dependencies": ["Carrier capacity", "Budget approval"],
                    "pros": ["Fast impact", "Immediate stock boost"],
                    "cons": ["High shipping costs", "Limited volume"]
                },
                {
                    "strategy_name": "Implement Demand Prioritization",
                    "action_steps": [
                        "Segment customers by priority/value",
                        "Allocate available inventory to key accounts",
                        "Communicate proactively with affected customers",
                        "Offer alternatives or future delivery dates"
                    ],
                    "timeline_days": 1,
                    "estimated_cost": 5000 * cost_multiplier,
                    "risk_reduction": 25,
                    "dependencies": ["Customer segmentation data"],
                    "pros": ["Protects key relationships", "Low cost"],
                    "cons": ["Some customers impacted", "Revenue deferral"]
                }
            ]
        
        elif "Transportation" in category:
            return [
                {
                    "strategy_name": "Use Alternative Carriers",
                    "action_steps": [
                        "Contact backup carrier network",
                        "Negotiate spot rates",
                        "Reroute affected shipments",
                        "Monitor delivery performance"
                    ],
                    "timeline_days": 2,
                    "estimated_cost": 20000 * cost_multiplier,
                    "risk_reduction": 50,
                    "dependencies": ["Carrier availability"],
                    "pros": ["Maintains delivery schedule", "Flexible"],
                    "cons": ["Premium rates", "Coordination overhead"]
                },
                {
                    "strategy_name": "Switch Transportation Mode",
                    "action_steps": [
                        "Evaluate air vs. ground vs. rail options",
                        "Calculate cost-benefit of mode switch",
                        "Book alternative transport",
                        "Update tracking systems"
                    ],
                    "timeline_days": 3,
                    "estimated_cost": 40000 * cost_multiplier,
                    "risk_reduction": 45,
                    "dependencies": ["Mode availability", "Cost approval"],
                    "pros": ["Can significantly speed delivery"],
                    "cons": ["Higher costs", "May not suit all products"]
                }
            ]
        
        else:  # External factors or default
            return [
                {
                    "strategy_name": "Activate Contingency Plan",
                    "action_steps": [
                        "Review existing contingency procedures",
                        "Brief relevant teams",
                        "Implement pre-planned mitigation steps",
                        "Monitor situation closely"
                    ],
                    "timeline_days": 1,
                    "estimated_cost": 10000 * cost_multiplier,
                    "risk_reduction": 30,
                    "dependencies": ["Documented contingency plan"],
                    "pros": ["Rapid response", "Pre-approved actions"],
                    "cons": ["May not cover all scenarios"]
                },
                {
                    "strategy_name": "Increase Monitoring and Communication",
                    "action_steps": [
                        "Set up enhanced monitoring for affected areas",
                        "Establish daily status calls with stakeholders",
                        "Create situation dashboard",
                        "Prepare communication templates"
                    ],
                    "timeline_days": 1,
                    "estimated_cost": 5000 * cost_multiplier,
                    "risk_reduction": 20,
                    "dependencies": ["Communication tools"],
                    "pros": ["Early warning of changes", "Stakeholder alignment"],
                    "cons": ["Reactive approach", "Time investment"]
                },
                {
                    "strategy_name": "Hedge Risk Exposure",
                    "action_steps": [
                        "Analyze exposure to specific risk factor",
                        "Explore financial hedging options",
                        "Implement contractual protections",
                        "Diversify where possible"
                    ],
                    "timeline_days": 14,
                    "estimated_cost": 30000 * cost_multiplier,
                    "risk_reduction": 35,
                    "dependencies": ["Financial team involvement", "Market instruments"],
                    "pros": ["Reduces financial impact", "Long-term protection"],
                    "cons": ["Complexity", "Upfront costs"]
                }
            ]
    
    def generate_mitigations(self, risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate mitigation strategies for a risk.
        
        Args:
            risk: Risk dictionary with all details
            
        Returns:
            List of mitigation strategy dictionaries
        """
        # Build prompt
        prompt = self._build_prompt(risk)
        
        # Try LLM first
        risk_id = risk.get('risk_id', 'UNKNOWN')
        if self.client:
            logger.debug(f"[Mitigation] Attempting LLM generation for {risk_id}")
            response = self._call_groq_api(prompt, risk)
            if response:
                strategies = self._parse_llm_response(response)
                if strategies:
                    logger.info(f"[Mitigation] Generated {len(strategies)} strategies via LLM for {risk_id} "
                               f"(category={risk.get('category')}, score={risk.get('risk_score', 0):.1f})")
                    return strategies
                else:
                    logger.warning(f"[Mitigation] LLM response parsing failed for {risk_id}, using fallback")
            else:
                logger.debug(f"[Mitigation] LLM API call failed for {risk_id}, using fallback")
        
        # Fallback to rule-based strategies
        strategies = self._generate_fallback_mitigations(risk)
        risk_id = risk.get('risk_id', 'UNKNOWN')
        logger.info(f"[Mitigation] Generated {len(strategies)} fallback strategies for {risk_id} "
                   f"(LLM unavailable or failed)")
        return strategies
    
    async def generate_mitigations_async(self, risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Async version of generate_mitigations.
        
        Args:
            risk: Risk dictionary with all details
            
        Returns:
            List of mitigation strategy dictionaries
        """
        # For now, just call the sync version
        # Can be enhanced with async Groq client if available
        return self.generate_mitigations(risk)
    
    def generate_bulk_mitigations(
        self,
        risks: List[Dict[str, Any]],
        limit: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate mitigations for multiple risks.
        
        Args:
            risks: List of risk dictionaries
            limit: Optional limit on number of risks to process
            
        Returns:
            Dictionary mapping risk_id to list of mitigations
        """
        results = {}
        
        # Sort by risk score and limit
        sorted_risks = sorted(risks, key=lambda x: x.get("risk_score", 0), reverse=True)
        if limit:
            sorted_risks = sorted_risks[:limit]
        
        for risk in sorted_risks:
            risk_id = risk.get("risk_id", "unknown")
            try:
                mitigations = self.generate_mitigations(risk)
                results[risk_id] = mitigations
            except Exception as e:
                logger.error(f"Failed to generate mitigations for risk {risk_id}: {e}")
                results[risk_id] = self._generate_fallback_mitigations(risk)
        
        return results

