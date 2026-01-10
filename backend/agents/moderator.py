"""
Moderator Agent - Resolves conflicts and synthesizes final strategy.
"""
from .base_agent import BaseAgent
from models.schemas import Strategy
import config


MODERATOR_SYSTEM_PROMPT = """You are the Managing Partner. You've reviewed all arguments, counterarguments, and conflicts.

Your job:
1) Weigh competing strategies
2) Resolve conflicts with clear reasoning
3) Produce a unified, coherent legal strategy
4) Note what alternatives you rejected and why

Be decisive. The team needs clear direction."""


class Moderator(BaseAgent):
    """Moderator agent that resolves conflicts and synthesizes final strategy."""

    def __init__(self):
        super().__init__(
            name=config.AGENT_NAMES["moderator"],
            system_prompt=MODERATOR_SYSTEM_PROMPT
        )

    def analyze(self, case_data: dict) -> dict:
        """
        Read all arguments, counterarguments, and conflicts from MongoDB.
        Synthesize a final strategy.
        Writes the strategy to MongoDB and returns the result.
        """
        case_id = case_data["case_id"]

        # Read all arguments from MongoDB
        arguments = self.read_from_db(
            config.COLLECTIONS["arguments"],
            {"case_id": case_id}
        )

        # Read all counterarguments from MongoDB
        counterarguments = self.read_from_db(
            config.COLLECTIONS["counterarguments"],
            {"case_id": case_id}
        )

        # Read all conflicts from MongoDB
        conflicts = self.read_from_db(
            config.COLLECTIONS["conflicts"],
            {"case_id": case_id}
        )

        # Format arguments for the prompt
        arguments_text = ""
        for arg in arguments:
            arguments_text += f"\n--- {arg['agent']} ({arg['type']}) ---\n"
            arguments_text += f"{arg['content']}\n"

        # Format counterarguments
        counterarguments_text = ""
        for counter in counterarguments:
            counterarguments_text += f"\n--- {counter['agent']} ---\n"
            counterarguments_text += f"{counter['content']}\n"
            counterarguments_text += f"Attack Vectors: {', '.join(counter.get('attack_vectors', []))}\n"

        # Format conflicts
        conflicts_text = ""
        for conflict in conflicts:
            conflicts_text += f"\n--- Conflict: {conflict['issue']} ---\n"
            conflicts_text += f"Agents Involved: {', '.join(conflict['agents_involved'])}\n"
            conflicts_text += f"Description: {conflict['description']}\n"

        # Build the prompt
        prompt = f"""
FINAL STRATEGY SYNTHESIS

CASE OVERVIEW:
Title: {case_data.get('title', 'Unknown')}

Facts:
{case_data.get('facts', 'No facts provided')}

Jurisdiction: {case_data.get('jurisdiction', 'Unknown')}

Stakes: {case_data.get('stakes', 'Unknown')}

---

TEAM ARGUMENTS:
{arguments_text}

---

ADVERSARIAL ANALYSIS (Opposing Counsel Perspective):
{counterarguments_text}

---

IDENTIFIED CONFLICTS:
{conflicts_text if conflicts_text else "No major conflicts detected."}

---

As Managing Partner, synthesize all inputs into a FINAL, UNIFIED STRATEGY:

1. **Executive Summary**:
   - One paragraph summary of the recommended approach

2. **Final Strategy Decision**:
   - Trial or Settlement? Why?
   - Primary legal theory to pursue
   - Key arguments to emphasize

3. **Action Plan**:
   - Immediate next steps (numbered list)
   - Key milestones and deadlines
   - Resource requirements

4. **Risk Mitigation**:
   - How we address the adversarial concerns
   - Contingency plans

5. **Conflict Resolutions**:
   - How each conflict was resolved
   - Rationale for choices made

6. **Rejected Alternatives**:
   - What strategies were considered but rejected?
   - Why were they rejected?

Be decisive and provide clear direction.
"""

        # Call LLM to generate final strategy
        response = self.think(prompt)

        # Extract rejected alternatives (simplified)
        rejected = self._extract_rejected_alternatives(response)

        # Get current strategy version
        existing_strategies = self.read_from_db(
            config.COLLECTIONS["strategies"],
            {"case_id": case_id}
        )
        version = len(existing_strategies) + 1

        # Create strategy document
        strategy = Strategy(
            case_id=case_id,
            version=version,
            final_strategy=response,
            rationale="Synthesized from Lead Strategist primary strategy, Precedent Expert legal research, Adversarial Counsel critique, and conflict analysis.",
            rejected_alternatives=rejected
        )

        # Write to MongoDB
        self.write_to_db(config.COLLECTIONS["strategies"], strategy.to_dict())

        return {
            "agent": self.name,
            "strategy_id": strategy.strategy_id,
            "version": strategy.version,
            "final_strategy": response,
            "rationale": strategy.rationale,
            "rejected_alternatives": rejected
        }

    def _extract_rejected_alternatives(self, response: str) -> list:
        """Extract rejected alternatives from the response."""
        rejected = []

        lines = response.split('\n')
        in_rejected_section = False

        for line in lines:
            line_lower = line.lower()
            if 'rejected alternative' in line_lower or 'rejected strategies' in line_lower:
                in_rejected_section = True
                continue

            if in_rejected_section:
                # Stop at next major section
                if line.startswith('##') or (line.startswith('**') and line.endswith('**')):
                    if len(rejected) >= 2:
                        break

                # Extract bullet points
                stripped = line.strip()
                if stripped.startswith('-') or stripped.startswith('•') or stripped.startswith('*'):
                    alternative = stripped.lstrip('-•* ').strip()
                    if alternative and len(alternative) > 10:
                        rejected.append(alternative[:200])

                # Also capture numbered items
                if stripped and stripped[0].isdigit() and '.' in stripped[:3]:
                    alternative = stripped.split('.', 1)[-1].strip()
                    if alternative and len(alternative) > 10:
                        rejected.append(alternative[:200])

                if len(rejected) >= 5:
                    break

        # Default if extraction didn't work
        if len(rejected) == 0:
            rejected = [
                "Early settlement without discovery - rejected due to insufficient leverage",
                "Aggressive litigation without settlement talks - rejected as too costly"
            ]

        return rejected[:5]
