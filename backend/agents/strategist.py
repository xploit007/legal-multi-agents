"""
Lead Strategist Agent - Develops primary legal strategy.
"""
from .base_agent import BaseAgent
from models.schemas import Argument
import config


STRATEGIST_SYSTEM_PROMPT = """You are a senior trial attorney known as 'The Closer'. You develop bold, winning legal strategies.

Analyze the case and provide:
1) Primary legal strategy (trial vs settlement)
2) Key leverage points
3) Strategic sequence of moves
4) Critical assumptions

Be aggressive but realistic. Your output should be structured and actionable."""


class LeadStrategist(BaseAgent):
    """Lead Strategist agent that develops primary legal strategy."""

    def __init__(self):
        super().__init__(
            name=config.AGENT_NAMES["strategist"],
            system_prompt=STRATEGIST_SYSTEM_PROMPT
        )

    def analyze(self, case_data: dict) -> dict:
        """
        Analyze the case and develop a primary legal strategy.
        Writes the argument to MongoDB and returns the result.
        """
        # Build the prompt with case details
        prompt = f"""
CASE ANALYSIS REQUEST

Title: {case_data.get('title', 'Unknown')}

Facts:
{case_data.get('facts', 'No facts provided')}

Jurisdiction: {case_data.get('jurisdiction', 'Unknown')}

Stakes: {case_data.get('stakes', 'Unknown')}

---

As the Lead Strategist, analyze this case and provide your comprehensive legal strategy. Include:

1. **Primary Strategy Recommendation**: Should we pursue trial or settlement? Why?

2. **Key Leverage Points**: What are our strongest positions and how do we exploit them?

3. **Strategic Sequence of Moves**: What are the tactical steps in order?

4. **Critical Assumptions**: What must be true for this strategy to succeed?

5. **Risk Assessment**: What could go wrong and how do we mitigate?

Be bold but grounded in legal reality.
"""

        # Call LLM to generate strategy
        response = self.think(prompt)

        # Create argument document
        argument = Argument(
            case_id=case_data["case_id"],
            agent=self.name,
            type="primary",
            content=response,
            reasoning="Primary legal strategy developed based on case facts, jurisdiction, and stakes analysis."
        )

        # Write to MongoDB
        self.write_to_db(config.COLLECTIONS["arguments"], argument.to_dict())

        return {
            "agent": self.name,
            "argument_id": argument.argument_id,
            "type": argument.type,
            "content": response,
            "reasoning": argument.reasoning
        }
