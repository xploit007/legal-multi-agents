"""Harvey - Lead Trial Strategist Agent.

Harvey is "The Closer" - a senior trial attorney known for developing bold,
winning legal strategies. He analyzes cases and provides primary strategy
recommendations.

Named after Harvey Specter from the TV show "Suits".
"""
from typing import Optional, Dict, Any, List
from .base_agent import BaseAgent
from services.mongo_utils import write_argument, write_agent_message
from services.langgraph_wrapper import StepTracer
import config


HARVEY_SYSTEM_PROMPT = """You are Harvey Specter, a legendary senior trial attorney known as 'The Closer'.
You have never lost a case that mattered. Your reputation is built on bold, aggressive strategies
that exploit every advantage while maintaining ethical boundaries.

Your analysis style:
- Confident and decisive
- Focus on leverage and winning positions
- Always think three moves ahead
- Identify the jugular - the one thing that wins the case

Analyze the case and provide:
1) Primary legal strategy (trial vs settlement) - be decisive
2) Key leverage points - what gives us power
3) Strategic sequence of moves - the battle plan
4) Critical assumptions - what must be true for this to work
5) Risk assessment - what could go wrong

Be aggressive but realistic. Winners find ways to win."""


class HarveyAgent(BaseAgent):
    """Harvey - Lead Trial Strategist who develops primary legal strategy."""

    def __init__(self):
        super().__init__(
            name=config.AGENT_NAMES["harvey"],
            system_prompt=HARVEY_SYSTEM_PROMPT
        )

    def analyze(self, case_data: Dict[str, Any],
                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the case and develop a primary legal strategy.

        If context contains counterarguments from Tanner, Harvey will
        reconsider and strengthen his strategy.

        Args:
            case_data: The case information
            context: Optional context including counterarguments to address

        Returns:
            Strategy document with trace information
        """
        case_id = case_data["case_id"]

        # Initialize step tracer for auditability
        tracer = StepTracer(
            self.name,
            case_id,
            metadata={"context": context} if context else None
        )

        # Build the prompt based on whether this is initial analysis or reconsideration
        if context and context.get("counterarguments"):
            prompt = self._build_reconsideration_prompt(case_data, context)
            analysis_type = "reconsideration"
        else:
            prompt = self._build_initial_prompt(case_data)
            analysis_type = "initial"

        # Step 1: Generate strategy using LLM
        def generate_strategy():
            return self.think(prompt)

        # Step 2: Extract key components
        def extract_components():
            strategy_text = tracer.steps_executed[-1]["output"] if tracer.steps_executed else ""
            return {
                "full_analysis": strategy_text,
                "analysis_type": analysis_type
            }

        # Run steps with tracing
        results = {}
        results["strategy_generation"] = tracer.run_step("strategy_generation", generate_strategy)
        results["component_extraction"] = tracer.run_step("component_extraction", extract_components)

        # Get the generated strategy
        strategy_content = results["strategy_generation"]["output"]

        # Persist argument to MongoDB
        arg_doc = write_argument(
            case_id=case_id,
            agent=self.name,
            arg_type="primary",
            content=strategy_content,
            reasoning=f"Primary legal strategy developed via {analysis_type} analysis."
        )

        # If this is a reconsideration, send message to Tanner
        if context and context.get("counterarguments"):
            for counter in context["counterarguments"]:
                write_agent_message(
                    case_id=case_id,
                    sender=self.name,
                    recipient="Tanner",
                    message={
                        "event": "rebuttal",
                        "argument_id": arg_doc.get("argument_id"),
                        "responding_to": counter.get("counterargument_id"),
                        "summary": "Strategy strengthened after considering counterarguments"
                    }
                )

        # Finish tracing
        tracer.finish(status="completed", result={"argument_id": arg_doc.get("argument_id")})

        return {
            "agent": self.name,
            "argument_id": arg_doc.get("argument_id"),
            "type": "primary",
            "content": strategy_content,
            "analysis_type": analysis_type,
            "trace": tracer.trace,
            "run_id": tracer.run_id
        }

    def _build_initial_prompt(self, case_data: Dict[str, Any]) -> str:
        """Build prompt for initial case analysis."""
        return f"""
CASE ANALYSIS REQUEST

Title: {case_data.get('title', 'Unknown')}

Facts:
{case_data.get('facts', 'No facts provided')}

Jurisdiction: {case_data.get('jurisdiction', 'Unknown')}

Stakes: {case_data.get('stakes', 'Unknown')}

---

Harvey, analyze this case and deliver your winning strategy. Include:

1. **Primary Strategy Recommendation**: Trial or settlement? Make a call and own it.

2. **Key Leverage Points**: What's our power position? What do we have that they want or fear?

3. **Strategic Sequence**: What are the moves, in order? Think chess, not checkers.

4. **Critical Assumptions**: What has to be true for this strategy to work?

5. **Risk Assessment**: What could blow up? How do we mitigate?

Give me a strategy that wins. That's what we do.
"""

    def _build_reconsideration_prompt(self, case_data: Dict[str, Any],
                                       context: Dict[str, Any]) -> str:
        """Build prompt for reconsidering strategy after Tanner's attacks."""
        counterarguments = context.get("counterarguments", [])
        counter_text = ""
        for counter in counterarguments:
            content = counter.get("content", "")
            if isinstance(content, dict):
                content = str(content)
            counter_text += f"\n--- Attack from {counter.get('agent', 'Opposing Counsel')} ---\n"
            counter_text += f"{content}\n"

        return f"""
STRATEGY RECONSIDERATION REQUEST

Title: {case_data.get('title', 'Unknown')}

Facts:
{case_data.get('facts', 'No facts provided')}

Jurisdiction: {case_data.get('jurisdiction', 'Unknown')}

Stakes: {case_data.get('stakes', 'Unknown')}

---

OPPOSING COUNSEL'S ATTACKS ON YOUR STRATEGY:
{counter_text}

---

Harvey, Tanner has attacked your strategy. You've seen his best shots.
Now strengthen your position. Address the weaknesses. Shore up the gaps.

Provide your REVISED strategy that:

1. **Directly addresses** the strongest counterarguments
2. **Reinforces** your leverage points
3. **Adjusts** your tactical sequence if needed
4. **Maintains** the winning posture

Don't back down - but don't ignore legitimate concerns either.
Make the strategy bulletproof.
"""
