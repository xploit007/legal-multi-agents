"""
Precedent Expert Agent - Finds relevant case law and legal doctrines.
"""
from .base_agent import BaseAgent
from models.schemas import Argument
import config


PRECEDENT_EXPERT_SYSTEM_PROMPT = """You are a legal research expert known as 'The Savant'. You have encyclopedic knowledge of case law.

Analyze the case and provide:
1) 3-5 relevant precedent cases (even if fictional, make them realistic)
2) Key legal doctrines that apply
3) How to distinguish unfavorable precedents
4) Technical legal arguments others might miss

Your research should be thorough and cite specific cases with their holdings."""


class PrecedentExpert(BaseAgent):
    """Precedent Expert agent that finds relevant case law and legal doctrines."""

    def __init__(self):
        super().__init__(
            name=config.AGENT_NAMES["precedent_expert"],
            system_prompt=PRECEDENT_EXPERT_SYSTEM_PROMPT
        )

    def analyze(self, case_data: dict) -> dict:
        """
        Analyze the case and find relevant precedents.
        Writes the argument to MongoDB and returns the result.
        """
        # Build the prompt with case details
        prompt = f"""
LEGAL RESEARCH REQUEST

Title: {case_data.get('title', 'Unknown')}

Facts:
{case_data.get('facts', 'No facts provided')}

Jurisdiction: {case_data.get('jurisdiction', 'Unknown')}

Stakes: {case_data.get('stakes', 'Unknown')}

---

As the Precedent Expert, provide comprehensive legal research for this case:

1. **Relevant Precedent Cases** (3-5 cases):
   For each case provide:
   - Case name and citation
   - Key facts
   - Holding
   - How it applies to our case

2. **Applicable Legal Doctrines**:
   - What doctrines govern this type of dispute?
   - How do they favor our position?

3. **Distinguishing Unfavorable Precedents**:
   - What cases might opposing counsel cite?
   - How do we distinguish them?

4. **Technical Legal Arguments**:
   - What subtle legal points might others miss?
   - Any procedural advantages we can exploit?

Be thorough and precise in your citations.
"""

        # Call LLM to generate precedent research
        response = self.think(prompt)

        # Create argument document
        argument = Argument(
            case_id=case_data["case_id"],
            agent=self.name,
            type="precedent",
            content=response,
            reasoning="Legal precedent research conducted based on jurisdiction and case type analysis."
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
