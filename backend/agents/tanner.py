"""Tanner - Adversarial Counsel Agent.

Tanner is "The Destroyer" - opposing counsel whose only job is to tear apart
your strategy. He identifies weaknesses, proposes counterarguments, and
suggests cross-examination traps.

Named after Travis Tanner from the TV show "Suits".
"""
from typing import Optional, Dict, Any, List
from .base_agent import BaseAgent
from services.mongo_utils import (
    write_counterargument, write_agent_message,
    get_arguments
)
from services.langgraph_wrapper import StepTracer
import config


TANNER_SYSTEM_PROMPT = """You are Travis Tanner, a ruthless opposing counsel known as 'The Destroyer'.
Your reputation is built on tearing apart cases that seemed unwinnable for your opponents.
You find every weakness, exploit every gap, and never show mercy.

Your approach:
- Assume nothing the other side says is true
- Find the three weakest points and attack relentlessly
- Identify evidence that hurts their case
- Plan cross-examination traps
- Think about what discovery will reveal

Your ONLY job is to DESTROY the plaintiff's case. Provide:
1) The 3 weakest points in their strategy
2) Strongest counterarguments
3) Cross-examination traps
4) Evidence that hurts their case
5) Attack vectors (brief phrases for each attack angle)

Be ruthless. Be thorough. Leave nothing standing."""


class TannerAgent(BaseAgent):
    """Tanner - Adversarial Counsel who attacks the strategy as opposing counsel would."""

    def __init__(self):
        super().__init__(
            name=config.AGENT_NAMES["tanner"],
            system_prompt=TANNER_SYSTEM_PROMPT
        )

    def analyze(self, case_data: Dict[str, Any],
                primary_strategies: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Read previous arguments and generate counterarguments.

        Args:
            case_data: The case information
            primary_strategies: List of strategies from Harvey/Louis to attack

        Returns:
            Counterargument document with attack vectors
        """
        case_id = case_data["case_id"]

        # Initialize step tracer for auditability
        metadata = {}
        if primary_strategies:
            metadata["attacking"] = [s.get("argument_id") for s in primary_strategies if s.get("argument_id")]

        tracer = StepTracer(self.name, case_id, metadata=metadata)

        # If no strategies provided, read from MongoDB
        if not primary_strategies:
            primary_strategies = self._get_strategies_from_db(case_id)

        # Build the prompt
        prompt = self._build_attack_prompt(case_data, primary_strategies)

        # Step 1: Generate attacks using LLM
        def generate_attacks():
            return self.think(prompt)

        # Step 2: Extract attack vectors
        def extract_attack_vectors():
            attack_text = tracer.steps_executed[-1]["output"] if tracer.steps_executed else ""
            vectors = self._extract_attack_vectors(attack_text)
            return vectors

        # Run steps with tracing
        results = {}
        results["attack_generation"] = tracer.run_step("attack_generation", generate_attacks)
        results["vector_extraction"] = tracer.run_step("vector_extraction", extract_attack_vectors)

        # Get results
        attack_content = results["attack_generation"]["output"]
        attack_vectors = results["vector_extraction"]["output"]

        # Determine target argument
        target_id = "general"
        if primary_strategies:
            target_id = primary_strategies[0].get("argument_id", "general")

        # Persist counterargument to MongoDB
        counter_doc = write_counterargument(
            case_id=case_id,
            agent=self.name,
            target_argument_id=target_id,
            content=attack_content,
            attack_vectors=attack_vectors
        )

        # Send message to Harvey about the attack
        write_agent_message(
            case_id=case_id,
            sender=self.name,
            recipient="Harvey",
            message={
                "event": "counter",
                "counterargument_id": counter_doc.get("counterargument_id"),
                "target_argument_id": target_id,
                "attack_vectors": attack_vectors,
                "summary": "Strategy attacked - weaknesses identified"
            }
        )

        # Finish tracing
        tracer.finish(status="completed", result={
            "counterargument_id": counter_doc.get("counterargument_id"),
            "attack_vectors_count": len(attack_vectors)
        })

        return {
            "agent": self.name,
            "counterargument_id": counter_doc.get("counterargument_id"),
            "target_argument_id": target_id,
            "content": attack_content,
            "attack_vectors": attack_vectors,
            "trace": tracer.trace,
            "run_id": tracer.run_id
        }

    def _get_strategies_from_db(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieve all arguments for the case from MongoDB."""
        return get_arguments(case_id)

    def _build_attack_prompt(self, case_data: Dict[str, Any],
                              strategies: List[Dict[str, Any]]) -> str:
        """Build the attack prompt for Tanner."""
        # Format strategies for the prompt
        strategies_text = ""
        for strat in strategies:
            agent = strat.get("agent", "Unknown")
            content = strat.get("content", "")
            if isinstance(content, dict):
                content = str(content)
            strategies_text += f"\n--- {agent}'s Argument ---\n"
            strategies_text += f"{content}\n"

        return f"""
OPPOSING COUNSEL ANALYSIS

CASE OVERVIEW:
Title: {case_data.get('title', 'Unknown')}

Facts:
{case_data.get('facts', 'No facts provided')}

Jurisdiction: {case_data.get('jurisdiction', 'Unknown')}

Stakes: {case_data.get('stakes', 'Unknown')}

---

PLAINTIFF'S ARGUMENTS AND STRATEGY:
{strategies_text}

---

Tanner, tear this apart. I want:

1. **Three Weakest Points**:
   - Identify the most vulnerable aspects of their strategy
   - Explain exactly why each is weak
   - How would you exploit each in court?

2. **Strongest Counterarguments**:
   - What arguments devastate their position?
   - What facts contradict their narrative?
   - What legal principles work against them?

3. **Cross-Examination Traps**:
   - What questions would expose their witnesses?
   - What inconsistencies can you exploit?
   - How do you get them to contradict themselves?

4. **Damaging Evidence**:
   - What evidence hurts their case?
   - What discovery requests would uncover problems?
   - What documents should we subpoena?

5. **Attack Vectors** (list 3-5 brief phrases):
   - Quick summary of each attack angle
   - These should be sharp, focused attacks

Leave nothing standing. That's how we win.
"""

    def _extract_attack_vectors(self, response: str) -> List[str]:
        """Extract attack vectors from the response."""
        vectors = []

        # Default attack vectors
        default_vectors = [
            "Challenge contract interpretation",
            "Question evidence authenticity",
            "Attack witness credibility",
            "Dispute damages calculation",
            "Procedural objections"
        ]

        # Try to find attack vectors section in response
        lines = response.split('\n')
        in_vectors_section = False

        for line in lines:
            line_lower = line.lower()
            if 'attack vector' in line_lower or 'attack angle' in line_lower:
                in_vectors_section = True
                continue

            if in_vectors_section:
                # Stop at next major section
                if line.startswith('##') or (line.startswith('**') and ':' in line and len(vectors) >= 3):
                    break

                # Extract bullet points
                stripped = line.strip()
                if stripped.startswith('-') or stripped.startswith('•') or stripped.startswith('*'):
                    vector = stripped.lstrip('-•* ').strip()
                    if vector and len(vector) > 5:
                        # Clean up markdown
                        vector = vector.replace('**', '').replace('*', '')
                        vectors.append(vector[:100])

                # Also capture numbered items
                if stripped and stripped[0].isdigit() and '.' in stripped[:3]:
                    vector = stripped.split('.', 1)[-1].strip()
                    vector = vector.replace('**', '').replace('*', '')
                    if vector and len(vector) > 5:
                        vectors.append(vector[:100])

                if len(vectors) >= 5:
                    break

        # Use defaults if extraction didn't work well
        if len(vectors) < 3:
            vectors = default_vectors

        return vectors[:5]
