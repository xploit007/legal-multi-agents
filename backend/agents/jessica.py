"""Jessica - Managing Partner / Moderator Agent.

Jessica is "The Mediator" - the managing partner who coordinates Harvey and Tanner
in multi-round deliberation, resolves conflicts, and synthesizes the final strategy.

Named after Jessica Pearson from the TV show "Suits".
"""
from typing import Optional, Dict, Any, List
from .base_agent import BaseAgent
from services.mongo_utils import (
    write_strategy_version, write_agent_message,
    get_arguments, get_counterarguments, get_conflicts
)
from services.langgraph_wrapper import StepTracer
import config


JESSICA_SYSTEM_PROMPT = """You are Jessica Pearson, the Managing Partner of the firm.
You've built this firm from nothing and you know how to make the hard calls.
Your job is to synthesize competing viewpoints and deliver a unified, winning strategy.

Your approach:
- Listen to all perspectives, but make the final call
- Resolve conflicts with clear reasoning
- Balance aggression with practicality
- Always keep the client's interests first
- Be decisive - the team needs direction

You've reviewed all arguments, counterarguments, and conflicts.
Now produce a unified strategy that:
1) Weighs competing strategies fairly
2) Resolves conflicts with clear reasoning
3) Produces a coherent, actionable plan
4) Notes what alternatives you rejected and why

Be decisive. The buck stops here."""


class JessicaAgent(BaseAgent):
    """Jessica - Managing Partner who synthesizes the final strategy."""

    def __init__(self):
        super().__init__(
            name=config.AGENT_NAMES["jessica"],
            system_prompt=JESSICA_SYSTEM_PROMPT
        )

    def analyze(self, case_data: Dict[str, Any],
                arguments: Optional[List[Dict[str, Any]]] = None,
                counterarguments: Optional[List[Dict[str, Any]]] = None,
                conflicts: Optional[List[Dict[str, Any]]] = None,
                deliberation_history: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Synthesize all inputs into a final, unified strategy.

        Args:
            case_data: The case information
            arguments: List of arguments from Harvey and Louis
            counterarguments: List of counterarguments from Tanner
            conflicts: List of detected conflicts
            deliberation_history: History of multi-round Harvey <-> Tanner exchanges

        Returns:
            Final strategy document
        """
        case_id = case_data["case_id"]

        # Initialize step tracer
        tracer = StepTracer(
            self.name,
            case_id,
            metadata={"deliberation_rounds": len(deliberation_history.get("rounds", [])) if deliberation_history else 0}
        )

        # If not provided, read from MongoDB
        if arguments is None:
            arguments = get_arguments(case_id)
        if counterarguments is None:
            counterarguments = get_counterarguments(case_id)
        if conflicts is None:
            conflicts = get_conflicts(case_id)

        # Build the synthesis prompt
        prompt = self._build_synthesis_prompt(
            case_data, arguments, counterarguments, conflicts, deliberation_history
        )

        # Step 1: Generate final strategy using LLM
        def generate_synthesis():
            return self.think(prompt)

        # Step 2: Extract rejected alternatives
        def extract_rejected():
            synthesis = tracer.steps_executed[-1]["output"] if tracer.steps_executed else ""
            return self._extract_rejected_alternatives(synthesis)

        # Step 3: Build rationale
        def build_rationale():
            return {
                "method": "Multi-round deliberation with conflict resolution",
                "inputs_considered": {
                    "arguments": len(arguments),
                    "counterarguments": len(counterarguments),
                    "conflicts_resolved": len(conflicts)
                },
                "deliberation_rounds": len(deliberation_history.get("rounds", [])) if deliberation_history else 0
            }

        # Run steps with tracing
        results = {}
        results["synthesis"] = tracer.run_step("synthesis", generate_synthesis)
        results["rejected_extraction"] = tracer.run_step("rejected_extraction", extract_rejected)
        results["rationale"] = tracer.run_step("rationale", build_rationale)

        # Get results
        final_strategy = results["synthesis"]["output"]
        rejected_alternatives = results["rejected_extraction"]["output"]
        rationale = results["rationale"]["output"]

        # Persist strategy version to MongoDB
        strategy_doc = write_strategy_version(
            case_id=case_id,
            author=self.name,
            strategy={"content": final_strategy},
            rationale=rationale,
            rejected_alternatives=rejected_alternatives
        )

        # Send message to the team
        write_agent_message(
            case_id=case_id,
            sender=self.name,
            recipient="Team",
            message={
                "event": "strategy_finalized",
                "strategy_id": strategy_doc.get("strategy_id"),
                "version": strategy_doc.get("version"),
                "summary": "Final strategy synthesized and approved"
            }
        )

        # Finish tracing
        tracer.finish(status="completed", result={
            "strategy_id": strategy_doc.get("strategy_id"),
            "version": strategy_doc.get("version")
        })

        return {
            "agent": self.name,
            "strategy_id": strategy_doc.get("strategy_id"),
            "version": strategy_doc.get("version"),
            "final_strategy": final_strategy,
            "rationale": rationale,
            "rejected_alternatives": rejected_alternatives,
            "trace": tracer.trace,
            "run_id": tracer.run_id
        }

    def _build_synthesis_prompt(self, case_data: Dict[str, Any],
                                 arguments: List[Dict[str, Any]],
                                 counterarguments: List[Dict[str, Any]],
                                 conflicts: List[Dict[str, Any]],
                                 deliberation_history: Optional[Dict[str, Any]]) -> str:
        """Build the synthesis prompt for Jessica."""

        # Format arguments (truncate to save tokens)
        arguments_text = ""
        for arg in arguments[:3]:  # Limit to 3 most recent
            agent = arg.get("agent", "Unknown")
            arg_type = arg.get("type", "unknown")
            content = arg.get("content", "")
            if isinstance(content, dict):
                content = content.get("content", str(content))
            content = content[:800] + "..." if len(content) > 800 else content  # Truncate
            arguments_text += f"\n--- {agent} ({arg_type}) ---\n"
            arguments_text += f"{content}\n"

        # Format counterarguments (truncate to save tokens)
        counterarguments_text = ""
        for counter in counterarguments[:2]:  # Limit to 2 most recent
            agent = counter.get("agent", "Unknown")
            content = counter.get("content", "")
            if isinstance(content, dict):
                content = str(content)
            content = content[:600] + "..." if len(content) > 600 else content  # Truncate
            counterarguments_text += f"\n--- {agent}'s Attack ---\n"
            counterarguments_text += f"{content}\n"

        # Format conflicts (truncate to save tokens)
        conflicts_text = ""
        for conflict in conflicts[:3]:  # Limit to 3 conflicts
            issue = conflict.get("issue", "Unknown")
            agents = conflict.get("agents_involved", [])
            description = conflict.get("description", "")[:200]  # Truncate description
            conflicts_text += f"\n--- Conflict: {issue} ---\n"
            conflicts_text += f"Agents: {', '.join(agents[:2])}\n"
            conflicts_text += f"{description}\n"

        # Format deliberation history
        deliberation_text = ""
        if deliberation_history and deliberation_history.get("rounds"):
            deliberation_text = "\n--- DELIBERATION HISTORY ---\n"
            for i, round_data in enumerate(deliberation_history["rounds"], 1):
                deliberation_text += f"\nRound {i}:\n"
                if round_data.get("harvey"):
                    deliberation_text += f"  Harvey's Position: {round_data['harvey'][:200]}...\n"
                if round_data.get("tanner"):
                    deliberation_text += f"  Tanner's Attack: {round_data['tanner'][:200]}...\n"

        # Truncate facts to save tokens
        facts = case_data.get('facts', 'No facts provided')
        facts = facts[:600] + "..." if len(facts) > 600 else facts

        return f"""FINAL STRATEGY SYNTHESIS

CASE: {case_data.get('title', 'Unknown')}
Jurisdiction: {case_data.get('jurisdiction', 'Unknown')} | Stakes: {case_data.get('stakes', 'Unknown')}

Facts: {facts}

TEAM ARGUMENTS:
{arguments_text if arguments_text else "None."}

ADVERSARIAL ATTACKS:
{counterarguments_text if counterarguments_text else "None."}

CONFLICTS:
{conflicts_text if conflicts_text else "None."}
{deliberation_text}

Jessica, synthesize a FINAL STRATEGY with:
1. Executive Summary (1 paragraph)
2. Decision: Trial or Settlement + key arguments
3. Action Plan (3-5 steps)
4. Risk Mitigation
5. Rejected Alternatives (brief)
"""

    def _extract_rejected_alternatives(self, response: str) -> List[str]:
        """Extract rejected alternatives from the response."""
        rejected = []

        lines = response.split('\n')
        in_rejected_section = False

        for line in lines:
            line_lower = line.lower()
            if 'rejected alternative' in line_lower or 'rejected strateg' in line_lower:
                in_rejected_section = True
                continue

            if in_rejected_section:
                # Stop at next major section
                if line.startswith('##') or (line.startswith('**') and line.endswith('**') and ':' not in line):
                    if len(rejected) >= 2:
                        break

                # Extract bullet points
                stripped = line.strip()
                if stripped.startswith('-') or stripped.startswith('•') or stripped.startswith('*'):
                    alternative = stripped.lstrip('-•* ').strip()
                    alternative = alternative.replace('**', '')
                    if alternative and len(alternative) > 10:
                        rejected.append(alternative[:200])

                # Also capture numbered items
                if stripped and stripped[0].isdigit() and '.' in stripped[:3]:
                    alternative = stripped.split('.', 1)[-1].strip()
                    alternative = alternative.replace('**', '')
                    if alternative and len(alternative) > 10:
                        rejected.append(alternative[:200])

                if len(rejected) >= 5:
                    break

        # Default if extraction didn't work
        if len(rejected) == 0:
            rejected = [
                "Early settlement without discovery - insufficient leverage at this stage",
                "Aggressive litigation without settlement talks - unnecessarily costly and risky"
            ]

        return rejected[:5]
