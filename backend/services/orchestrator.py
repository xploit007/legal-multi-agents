"""
Orchestrator Service - Controls the multi-agent workflow.

Manages the sequential and multi-round execution of agents:
1. Harvey (Lead Strategist) develops initial strategy
2. Louis (Precedent Expert) provides case law research
3. Multi-round deliberation: Tanner attacks -> Harvey rebuts (configurable rounds)
4. Conflict Detection identifies disagreements
5. Jessica (Moderator) synthesizes final strategy

Emits SSE events for real-time frontend updates.
"""
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime

from agents.harvey import HarveyAgent
from agents.louis import LouisAgent
from agents.tanner import TannerAgent
from agents.jessica import JessicaAgent
from services.conflict_detector import ConflictDetector
from services.mongo_utils import write_agent_message, get_arguments, get_counterarguments
from models.schemas import Case
import database
import config


class Orchestrator:
    """
    Orchestrates the multi-agent legal strategy workflow with multi-round deliberation.

    Flow:
    1. Harvey -> Initial Strategy
    2. Louis -> Precedent Research
    3. [Deliberation Loop] Tanner attacks -> Harvey rebuts (N rounds)
    4. Conflict Detection
    5. Jessica -> Final Synthesis
    """

    def __init__(self):
        self.harvey = HarveyAgent()
        self.louis = LouisAgent()
        self.tanner = TannerAgent()
        self.jessica = JessicaAgent()
        self.conflict_detector = ConflictDetector()

        # Store for tracking case progress
        self._case_progress: Dict[str, Dict] = {}

    def create_case(self, title: str, facts: str, jurisdiction: str, stakes: str) -> Case:
        """Create a new case and save to MongoDB."""
        case = Case(
            title=title,
            facts=facts,
            jurisdiction=jurisdiction,
            stakes=stakes
        )

        # Save to MongoDB
        cases_collection = database.get_cases_collection()
        cases_collection.insert_one(case.to_dict())

        # Initialize progress tracking
        self._case_progress[case.case_id] = {
            "status": "created",
            "agents_completed": [],
            "current_agent": None,
            "deliberation_round": 0,
            "conflicts": [],
            "strategy": None
        }

        return case

    async def run_analysis(self, case_id: str) -> AsyncGenerator[str, None]:
        """
        Run the full multi-agent analysis workflow with multi-round deliberation.
        Yields SSE events as agents complete their work.
        """
        print(f"[Orchestrator] Starting analysis for case: {case_id}")

        # Get case from MongoDB
        case_data = self._get_case(case_id)
        if not case_data:
            print(f"[Orchestrator] Case not found: {case_id}")
            yield self._format_sse_event("error", {"message": "Case not found"})
            return

        print(f"[Orchestrator] Case data loaded: {case_data.get('title', 'Unknown')}")
        deliberation_history = {"rounds": []}

        try:
            # ================================================================
            # Step 1: Harvey - Initial Strategy
            # ================================================================
            print(f"[Orchestrator] Starting Harvey analysis...")
            yield self._format_sse_event("agent_started", {
                "agent": config.AGENT_NAMES["harvey"],
                "case_id": case_id,
                "phase": "initial_strategy"
            })

            try:
                harvey_result = await asyncio.to_thread(
                    self.harvey.analyze, case_data
                )
                print(f"[Orchestrator] Harvey completed successfully")
            except Exception as e:
                print(f"[Orchestrator] Harvey ERROR: {e}")
                raise

            yield self._format_sse_event("agent_completed", {
                "agent": config.AGENT_NAMES["harvey"],
                "case_id": case_id,
                "content": harvey_result["content"],
                "type": "primary",
                "run_id": harvey_result.get("run_id")
            })

            # ================================================================
            # Step 2: Louis - Precedent Research
            # ================================================================
            yield self._format_sse_event("agent_started", {
                "agent": config.AGENT_NAMES["louis"],
                "case_id": case_id,
                "phase": "precedent_research"
            })

            louis_result = await asyncio.to_thread(
                self.louis.analyze, case_data,
                {"harvey_strategy": harvey_result["content"]}
            )

            yield self._format_sse_event("agent_completed", {
                "agent": config.AGENT_NAMES["louis"],
                "case_id": case_id,
                "content": louis_result["content"],
                "type": "precedent",
                "run_id": louis_result.get("run_id")
            })

            # ================================================================
            # Step 3: Multi-Round Deliberation (Tanner <-> Harvey)
            # ================================================================
            rounds = config.DELIBERATION_ROUNDS
            current_strategy = harvey_result

            for round_num in range(1, rounds + 1):
                yield self._format_sse_event("deliberation_round_started", {
                    "case_id": case_id,
                    "round": round_num,
                    "total_rounds": rounds
                })

                # Tanner attacks
                yield self._format_sse_event("agent_started", {
                    "agent": config.AGENT_NAMES["tanner"],
                    "case_id": case_id,
                    "phase": f"attack_round_{round_num}"
                })

                tanner_result = await asyncio.to_thread(
                    self.tanner.analyze, case_data,
                    [current_strategy, louis_result]
                )

                yield self._format_sse_event("agent_completed", {
                    "agent": config.AGENT_NAMES["tanner"],
                    "case_id": case_id,
                    "content": tanner_result["content"],
                    "attack_vectors": tanner_result.get("attack_vectors", []),
                    "round": round_num,
                    "run_id": tanner_result.get("run_id")
                })

                # Record deliberation round
                round_data = {
                    "round": round_num,
                    "tanner": tanner_result["content"][:500],
                    "tanner_vectors": tanner_result.get("attack_vectors", [])
                }

                # Harvey rebuts (if not last round, or if we want final rebuttal)
                if round_num < rounds:
                    yield self._format_sse_event("agent_started", {
                        "agent": config.AGENT_NAMES["harvey"],
                        "case_id": case_id,
                        "phase": f"rebuttal_round_{round_num}"
                    })

                    # Harvey reconsiders with Tanner's counterarguments
                    harvey_rebuttal = await asyncio.to_thread(
                        self.harvey.analyze, case_data,
                        {"counterarguments": [tanner_result]}
                    )

                    yield self._format_sse_event("agent_completed", {
                        "agent": config.AGENT_NAMES["harvey"],
                        "case_id": case_id,
                        "content": harvey_rebuttal["content"],
                        "type": "rebuttal",
                        "round": round_num,
                        "run_id": harvey_rebuttal.get("run_id")
                    })

                    current_strategy = harvey_rebuttal
                    round_data["harvey"] = harvey_rebuttal["content"][:500]

                deliberation_history["rounds"].append(round_data)

                yield self._format_sse_event("deliberation_round_completed", {
                    "case_id": case_id,
                    "round": round_num,
                    "total_rounds": rounds
                })

            # ================================================================
            # Step 4: Conflict Detection
            # ================================================================
            print(f"[Orchestrator] Starting conflict detection...")
            yield self._format_sse_event("detecting_conflicts", {
                "case_id": case_id
            })

            try:
                conflicts = await asyncio.to_thread(
                    self.conflict_detector.detect_conflicts, case_id
                )
                print(f"[Orchestrator] Conflict detection completed, found {len(conflicts)} conflicts")
            except Exception as e:
                print(f"[Orchestrator] Conflict detection ERROR: {e}")
                raise

            yield self._format_sse_event("conflict_detected", {
                "case_id": case_id,
                "conflicts": conflicts,
                "count": len(conflicts)
            })

            # ================================================================
            # Step 5: Jessica - Final Synthesis
            # ================================================================
            print(f"[Orchestrator] Starting Jessica synthesis...")
            yield self._format_sse_event("agent_started", {
                "agent": config.AGENT_NAMES["jessica"],
                "case_id": case_id,
                "phase": "final_synthesis"
            })

            # Gather all arguments and counterarguments
            all_arguments = get_arguments(case_id)
            all_counterarguments = get_counterarguments(case_id)

            try:
                jessica_result = await asyncio.to_thread(
                    self.jessica.analyze, case_data,
                    all_arguments,
                    all_counterarguments,
                    conflicts,
                    deliberation_history
                )
                print(f"[Orchestrator] Jessica completed successfully")
            except Exception as e:
                print(f"[Orchestrator] Jessica ERROR: {e}")
                raise

            yield self._format_sse_event("agent_completed", {
                "agent": config.AGENT_NAMES["jessica"],
                "case_id": case_id,
                "content": jessica_result["final_strategy"],
                "rejected_alternatives": jessica_result.get("rejected_alternatives", []),
                "run_id": jessica_result.get("run_id")
            })

            # ================================================================
            # Final Event
            # ================================================================
            yield self._format_sse_event("strategy_ready", {
                "case_id": case_id,
                "strategy": {
                    "strategy_id": jessica_result["strategy_id"],
                    "version": jessica_result["version"],
                    "final_strategy": jessica_result["final_strategy"],
                    "rationale": jessica_result["rationale"],
                    "rejected_alternatives": jessica_result.get("rejected_alternatives", [])
                },
                "deliberation_rounds": len(deliberation_history["rounds"])
            })

            # Update progress
            self._case_progress[case_id] = {
                "status": "completed",
                "agents_completed": [
                    config.AGENT_NAMES["harvey"],
                    config.AGENT_NAMES["louis"],
                    config.AGENT_NAMES["tanner"],
                    config.AGENT_NAMES["jessica"]
                ],
                "current_agent": None,
                "deliberation_rounds": len(deliberation_history["rounds"]),
                "conflicts": conflicts,
                "strategy": jessica_result
            }

        except Exception as e:
            yield self._format_sse_event("error", {
                "case_id": case_id,
                "message": str(e)
            })

    def _get_case(self, case_id: str) -> Optional[Dict]:
        """Retrieve case from MongoDB."""
        cases_collection = database.get_cases_collection()
        case = cases_collection.find_one({"case_id": case_id})
        if case:
            if "_id" in case:
                del case["_id"]
        return case

    def get_case_with_details(self, case_id: str) -> Optional[Dict]:
        """Get full case with all arguments, counterarguments, conflicts, and strategy."""
        case = self._get_case(case_id)
        if not case:
            return None

        # Get arguments
        arguments_collection = database.get_arguments_collection()
        arguments = list(arguments_collection.find({"case_id": case_id}))
        for arg in arguments:
            if "_id" in arg:
                del arg["_id"]

        # Get counterarguments
        counterarguments_collection = database.get_counterarguments_collection()
        counterarguments = list(counterarguments_collection.find({"case_id": case_id}))
        for counter in counterarguments:
            if "_id" in counter:
                del counter["_id"]

        # Get conflicts
        conflicts_collection = database.get_conflicts_collection()
        conflicts = list(conflicts_collection.find({"case_id": case_id}))
        for conflict in conflicts:
            if "_id" in conflict:
                del conflict["_id"]

        # Get strategy (latest version)
        strategies_collection = database.get_strategies_collection()
        strategies = list(strategies_collection.find({"case_id": case_id}).sort("version", -1).limit(1))
        strategy = None
        if strategies:
            strategy = strategies[0]
            if "_id" in strategy:
                del strategy["_id"]

        # Get agent messages for audit trail
        messages_collection = database.get_agent_messages_collection()
        messages = list(messages_collection.find({"case_id": case_id}).sort("created_at", 1))
        for msg in messages:
            if "_id" in msg:
                del msg["_id"]

        return {
            "case": case,
            "arguments": arguments,
            "counterarguments": counterarguments,
            "conflicts": conflicts,
            "strategy": strategy,
            "agent_messages": messages
        }

    def get_arguments(self, case_id: str) -> list:
        """Get all arguments for a case."""
        return get_arguments(case_id)

    def get_conflicts(self, case_id: str) -> list:
        """Get all conflicts for a case."""
        conflicts_collection = database.get_conflicts_collection()
        conflicts = list(conflicts_collection.find({"case_id": case_id}))
        for conflict in conflicts:
            if "_id" in conflict:
                del conflict["_id"]
        return conflicts

    def get_strategy(self, case_id: str) -> Optional[Dict]:
        """Get the final strategy for a case."""
        strategies_collection = database.get_strategies_collection()
        strategies = list(strategies_collection.find({"case_id": case_id}).sort("version", -1).limit(1))
        if strategies:
            strategy = strategies[0]
            if "_id" in strategy:
                del strategy["_id"]
            return strategy
        return None

    def _format_sse_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as an SSE event string."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


# Singleton orchestrator instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get or create the orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
