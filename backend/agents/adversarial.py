"""
Adversarial Counsel Agent - Attacks the strategy as opposing counsel would.
"""
from .base_agent import BaseAgent
from models.schemas import Counterargument
import config


ADVERSARIAL_SYSTEM_PROMPT = """You are opposing counsel. Your ONLY job is to destroy the plaintiff's case.

You must:
1) Identify the 3 weakest points in their strategy
2) Propose the strongest counterarguments
3) Suggest cross-examination traps
4) Identify evidence that hurts their case

Be ruthless and thorough. Your job is to find every weakness and exploit it."""


class AdversarialCounsel(BaseAgent):
    """Adversarial Counsel agent that attacks the strategy as opposing counsel would."""

    def __init__(self):
        super().__init__(
            name=config.AGENT_NAMES["adversarial"],
            system_prompt=ADVERSARIAL_SYSTEM_PROMPT
        )

    def analyze(self, case_data: dict) -> dict:
        """
        Read previous arguments from MongoDB and generate counterarguments.
        Writes counterarguments to MongoDB and returns the result.
        """
        case_id = case_data["case_id"]

        # Read previous arguments from MongoDB
        arguments = self.read_from_db(
            config.COLLECTIONS["arguments"],
            {"case_id": case_id}
        )

        # Format arguments for the prompt
        arguments_text = ""
        argument_ids = []
        for arg in arguments:
            arguments_text += f"\n--- {arg['agent']} ({arg['type']}) ---\n"
            arguments_text += f"{arg['content']}\n"
            argument_ids.append(arg.get('argument_id', 'unknown'))

        # Build the prompt
        prompt = f"""
OPPOSING COUNSEL ANALYSIS

CASE OVERVIEW:
Title: {case_data.get('title', 'Unknown')}

Facts:
{case_data.get('facts', 'No facts provided')}

Jurisdiction: {case_data.get('jurisdiction', 'Unknown')}

Stakes: {case_data.get('stakes', 'Unknown')}

---

PLAINTIFF'S ARGUMENTS AND STRATEGY:
{arguments_text}

---

As Opposing Counsel, your mission is to DESTROY this case. Provide:

1. **Three Weakest Points**:
   - Identify the most vulnerable aspects of their strategy
   - Explain exactly why each is weak

2. **Strongest Counterarguments**:
   - What arguments devastate their position?
   - What evidence contradicts their narrative?

3. **Cross-Examination Traps**:
   - What questions would expose their witnesses?
   - What inconsistencies can you exploit?

4. **Damaging Evidence**:
   - What evidence hurts their case?
   - What discovery requests would uncover problems?

5. **Attack Vectors**:
   - List 3-5 specific attack vectors (brief phrases)

Be ruthless. Find every weakness.
"""

        # Call LLM to generate counterarguments
        response = self.think(prompt)

        # Extract attack vectors from response (simplified extraction)
        attack_vectors = self._extract_attack_vectors(response)

        # Create counterargument document
        # Target all previous arguments
        target_id = argument_ids[0] if argument_ids else "general"

        counterargument = Counterargument(
            case_id=case_id,
            agent=self.name,
            target_argument_id=target_id,
            content=response,
            attack_vectors=attack_vectors
        )

        # Write to MongoDB
        self.write_to_db(config.COLLECTIONS["counterarguments"], counterargument.to_dict())

        return {
            "agent": self.name,
            "counterargument_id": counterargument.counterargument_id,
            "target_argument_id": target_id,
            "content": response,
            "attack_vectors": attack_vectors
        }

    def _extract_attack_vectors(self, response: str) -> list:
        """Extract attack vectors from the response."""
        # Look for common patterns in the response
        vectors = []

        # Default attack vectors based on common legal strategies
        default_vectors = [
            "Challenge interpretation of contract terms",
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
            if 'attack vector' in line_lower or 'attack strategies' in line_lower:
                in_vectors_section = True
                continue

            if in_vectors_section:
                # Stop at next major section
                if line.startswith('##') or line.startswith('**') and ':' in line:
                    if len(vectors) >= 3:
                        break

                # Extract bullet points
                stripped = line.strip()
                if stripped.startswith('-') or stripped.startswith('•') or stripped.startswith('*'):
                    vector = stripped.lstrip('-•* ').strip()
                    if vector and len(vector) > 5:
                        vectors.append(vector[:100])  # Limit length

                if len(vectors) >= 5:
                    break

        # Use defaults if extraction didn't work well
        if len(vectors) < 3:
            vectors = default_vectors

        return vectors[:5]
