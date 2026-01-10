"""Louis - Precedent & Legal Research Expert Agent.

Louis is "The Savant" - a legal research expert with encyclopedic knowledge
of case law. He finds relevant precedents, identifies applicable legal doctrines,
and provides technical legal arguments that others might miss.

Named after Louis Litt from the TV show "Suits".
"""
from typing import Optional, Dict, Any
from .base_agent import BaseAgent
from services.mongo_utils import write_argument, write_agent_message
from services.langgraph_wrapper import StepTracer
import config


LOUIS_SYSTEM_PROMPT = """You are Louis Litt, a legal research expert known as 'The Savant'.
You have an encyclopedic knowledge of case law and an obsessive attention to detail.
What you lack in courtroom charisma, you make up for in pure legal knowledge.

Your expertise:
- Deep knowledge of precedent cases across jurisdictions
- Master of legal doctrines and their applications
- Ability to find obscure cases that others miss
- Expert at distinguishing unfavorable precedents

Analyze the case and provide:
1) 3-5 relevant precedent cases (make them realistic with holdings)
2) Key legal doctrines that apply
3) How to distinguish unfavorable precedents
4) Technical legal arguments others might miss

Be thorough, precise, and cite specific cases with their holdings.
This is where cases are won - in the details."""


class LouisAgent(BaseAgent):
    """Louis - Precedent Expert who finds relevant case law and legal doctrines."""

    def __init__(self):
        super().__init__(
            name=config.AGENT_NAMES["louis"],
            system_prompt=LOUIS_SYSTEM_PROMPT
        )

    def analyze(self, case_data: Dict[str, Any],
                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the case and find relevant precedents and legal doctrines.

        Args:
            case_data: The case information
            context: Optional context (e.g., Harvey's strategy to support)

        Returns:
            Precedent research document with trace information
        """
        case_id = case_data["case_id"]

        # Initialize step tracer for auditability
        tracer = StepTracer(
            self.name,
            case_id,
            metadata={"context": context} if context else None
        )

        # Build the prompt
        prompt = self._build_research_prompt(case_data, context)

        # Step 1: Generate precedent research using LLM
        def research_precedents():
            return self.think(prompt)

        # Step 2: Categorize findings
        def categorize_findings():
            research_text = tracer.steps_executed[-1]["output"] if tracer.steps_executed else ""
            return {
                "full_research": research_text,
                "research_type": "precedent_analysis"
            }

        # Run steps with tracing
        results = {}
        results["precedent_research"] = tracer.run_step("precedent_research", research_precedents)
        results["categorization"] = tracer.run_step("categorization", categorize_findings)

        # Get the generated research
        research_content = results["precedent_research"]["output"]

        # Persist argument to MongoDB
        arg_doc = write_argument(
            case_id=case_id,
            agent=self.name,
            arg_type="precedent",
            content=research_content,
            reasoning="Legal precedent research conducted to support case strategy."
        )

        # Send message to Harvey about research findings
        write_agent_message(
            case_id=case_id,
            sender=self.name,
            recipient="Harvey",
            message={
                "event": "research_complete",
                "argument_id": arg_doc.get("argument_id"),
                "summary": "Precedent research completed - key cases identified"
            }
        )

        # Finish tracing
        tracer.finish(status="completed", result={"argument_id": arg_doc.get("argument_id")})

        return {
            "agent": self.name,
            "argument_id": arg_doc.get("argument_id"),
            "type": "precedent",
            "content": research_content,
            "trace": tracer.trace,
            "run_id": tracer.run_id
        }

    def _build_research_prompt(self, case_data: Dict[str, Any],
                                context: Optional[Dict[str, Any]] = None) -> str:
        """Build the research prompt for Louis."""
        context_section = ""
        if context and context.get("harvey_strategy"):
            context_section = f"""
HARVEY'S PRIMARY STRATEGY (for reference):
{context.get('harvey_strategy')}

Your research should support and strengthen this strategic approach.
---
"""

        return f"""
LEGAL RESEARCH REQUEST

Title: {case_data.get('title', 'Unknown')}

Facts:
{case_data.get('facts', 'No facts provided')}

Jurisdiction: {case_data.get('jurisdiction', 'Unknown')}

Stakes: {case_data.get('stakes', 'Unknown')}

{context_section}
---

Louis, I need your comprehensive legal research on this case. Provide:

1. **Relevant Precedent Cases** (3-5 cases):
   For each case include:
   - Case name and citation (make them realistic)
   - Key facts that parallel our situation
   - Holding and legal principle established
   - How it supports our position

2. **Applicable Legal Doctrines**:
   - What established legal doctrines govern this dispute?
   - How do they favor our client's position?
   - Any recent developments in the law we should know about?

3. **Distinguishing Unfavorable Precedents**:
   - What cases might opposing counsel cite against us?
   - How do we distinguish them from our facts?
   - What makes our situation different?

4. **Technical Legal Arguments**:
   - What subtle legal points might others miss?
   - Any procedural advantages we can exploit?
   - Jurisdictional considerations?

Be thorough. Be precise. This is where we win.
"""
