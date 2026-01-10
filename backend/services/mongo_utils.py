"""Higher-level Mongo utilities for coordination and agent tracing.

This module provides functions that write structured documents for agent runs,
reasoning steps, arguments, and inter-agent messages. MongoDB is treated as
the coordination layer (not only storage): agent runs and step-level traces
are persisted to enable replay, audit trails, and conflict detection.

Adapted from LegalServer-main by teammate.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import sys
sys.path.insert(0, "..")
import database


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


def _generate_id(prefix: str) -> str:
    """Generate a unique ID with given prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ============================================================================
# Agent Run Tracking
# ============================================================================

def start_agent_run(agent_name: str, case_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Start tracking an agent run. Returns the run document."""
    run = {
        "run_id": _generate_id("run"),
        "agent": agent_name,
        "case_id": case_id,
        "metadata": metadata or {},
        "status": "running",
        "started_at": _now_iso(),
    }
    try:
        collection = database.get_collection("agent_runs")
        collection.insert_one(run.copy())
    except Exception as e:
        print(f"Warning: Could not persist agent run: {e}")
    return run


def finish_agent_run(run_id: str, status: str = "completed", result: Optional[Dict[str, Any]] = None):
    """Mark an agent run as finished."""
    update = {"status": status, "finished_at": _now_iso()}
    if result:
        update["result"] = result
    try:
        collection = database.get_collection("agent_runs")
        collection.update_one({"run_id": run_id}, {"$set": update})
    except Exception as e:
        print(f"Warning: Could not update agent run: {e}")


# ============================================================================
# Reasoning Steps (Step-level tracing for auditability)
# ============================================================================

def write_reasoning_step(run_id: str, step_name: str, content: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a single reasoning step within an agent run."""
    doc = {
        "step_id": _generate_id("step"),
        "run_id": run_id,
        "step_name": step_name,
        "content": content,
        "created_at": _now_iso(),
    }
    try:
        collection = database.get_collection("reasoning_steps")
        collection.insert_one(doc.copy())
    except Exception as e:
        print(f"Warning: Could not persist reasoning step: {e}")
    return doc


def get_reasoning_steps(run_id: str) -> List[Dict[str, Any]]:
    """Retrieve all reasoning steps for a given run."""
    try:
        collection = database.get_collection("reasoning_steps")
        steps = list(collection.find({"run_id": run_id}).sort("created_at", 1))
        for step in steps:
            if "_id" in step:
                del step["_id"]
        return steps
    except Exception:
        return []


# ============================================================================
# Arguments (Primary strategies from Harvey and Louis)
# ============================================================================

def write_argument(case_id: str, agent: str, arg_type: str, content: Any, reasoning: str = "") -> Dict[str, Any]:
    """Write an argument document to the arguments collection."""
    doc = {
        "argument_id": _generate_id("arg"),
        "case_id": case_id,
        "agent": agent,
        "type": arg_type,
        "content": content,
        "reasoning": reasoning,
        "created_at": _now_iso(),
    }
    try:
        collection = database.get_collection("arguments")
        collection.insert_one(doc.copy())
    except Exception as e:
        print(f"Warning: Could not persist argument: {e}")
    return doc


def get_arguments(case_id: str) -> List[Dict[str, Any]]:
    """Retrieve all arguments for a case."""
    try:
        collection = database.get_collection("arguments")
        args = list(collection.find({"case_id": case_id}))
        for arg in args:
            if "_id" in arg:
                del arg["_id"]
        return args
    except Exception:
        return []


# ============================================================================
# Counterarguments (Attacks from Tanner)
# ============================================================================

def write_counterargument(case_id: str, agent: str, target_argument_id: str,
                          content: Any, attack_vectors: List[str] = None) -> Dict[str, Any]:
    """Write a counterargument document to the counterarguments collection."""
    doc = {
        "counterargument_id": _generate_id("ctr"),
        "case_id": case_id,
        "agent": agent,
        "target_argument_id": target_argument_id,
        "content": content,
        "attack_vectors": attack_vectors or [],
        "created_at": _now_iso(),
    }
    try:
        collection = database.get_collection("counterarguments")
        collection.insert_one(doc.copy())
    except Exception as e:
        print(f"Warning: Could not persist counterargument: {e}")
    return doc


def get_counterarguments(case_id: str) -> List[Dict[str, Any]]:
    """Retrieve all counterarguments for a case."""
    try:
        collection = database.get_collection("counterarguments")
        counters = list(collection.find({"case_id": case_id}))
        for counter in counters:
            if "_id" in counter:
                del counter["_id"]
        return counters
    except Exception:
        return []


# ============================================================================
# Agent Messages (Inter-agent communication for multi-round deliberation)
# ============================================================================

def write_agent_message(case_id: str, sender: str, recipient: str,
                        message: Dict[str, Any]) -> Dict[str, Any]:
    """Write an agent-to-agent message for coordination.

    This enables channel-based back-and-forth exchanges coordinated through Mongo.
    """
    doc = {
        "message_id": _generate_id("msg"),
        "case_id": case_id,
        "sender": sender,
        "recipient": recipient,
        "message": message,
        "created_at": _now_iso(),
    }
    try:
        collection = database.get_collection("agent_messages")
        collection.insert_one(doc.copy())
    except Exception as e:
        print(f"Warning: Could not persist agent message: {e}")
    return doc


def get_agent_messages(case_id: str, sender: str = None, recipient: str = None) -> List[Dict[str, Any]]:
    """Retrieve agent messages, optionally filtered by sender/recipient."""
    try:
        query = {"case_id": case_id}
        if sender:
            query["sender"] = sender
        if recipient:
            query["recipient"] = recipient
        collection = database.get_collection("agent_messages")
        messages = list(collection.find(query).sort("created_at", 1))
        for msg in messages:
            if "_id" in msg:
                del msg["_id"]
        return messages
    except Exception:
        return []


# ============================================================================
# Strategy Versions (Final synthesized strategies from Jessica)
# ============================================================================

def write_strategy_version(case_id: str, author: str, strategy: Dict[str, Any],
                           rationale: Dict[str, Any] = None,
                           rejected_alternatives: List[str] = None) -> Dict[str, Any]:
    """Persist a versioned strategy for audit and replay."""
    # Get current version number
    try:
        collection = database.get_collection("strategies")
        existing = collection.count_documents({"case_id": case_id})
        version = existing + 1
    except Exception:
        version = 1

    doc = {
        "strategy_id": _generate_id("str"),
        "case_id": case_id,
        "author": author,
        "version": version,
        "final_strategy": strategy,
        "rationale": rationale or {},
        "rejected_alternatives": rejected_alternatives or [],
        "created_at": _now_iso(),
    }
    try:
        collection = database.get_collection("strategies")
        collection.insert_one(doc.copy())
    except Exception as e:
        print(f"Warning: Could not persist strategy version: {e}")
    return doc


def get_latest_strategy(case_id: str) -> Optional[Dict[str, Any]]:
    """Get the latest strategy version for a case."""
    try:
        collection = database.get_collection("strategies")
        strategies = list(collection.find({"case_id": case_id}).sort("version", -1).limit(1))
        if strategies:
            strategy = strategies[0]
            if "_id" in strategy:
                del strategy["_id"]
            return strategy
        return None
    except Exception:
        return None


# ============================================================================
# Conflicts
# ============================================================================

def write_conflict(case_id: str, agents_involved: List[str], issue: str,
                   description: str) -> Dict[str, Any]:
    """Write a conflict document."""
    doc = {
        "conflict_id": _generate_id("conf"),
        "case_id": case_id,
        "agents_involved": agents_involved,
        "issue": issue,
        "description": description,
        "status": "unresolved",
        "created_at": _now_iso(),
    }
    try:
        collection = database.get_collection("conflicts")
        collection.insert_one(doc.copy())
    except Exception as e:
        print(f"Warning: Could not persist conflict: {e}")
    return doc


def get_conflicts(case_id: str) -> List[Dict[str, Any]]:
    """Retrieve all conflicts for a case."""
    try:
        collection = database.get_collection("conflicts")
        conflicts = list(collection.find({"case_id": case_id}))
        for conflict in conflicts:
            if "_id" in conflict:
                del conflict["_id"]
        return conflicts
    except Exception:
        return []


def resolve_conflict(conflict_id: str, resolution: str = None):
    """Mark a conflict as resolved."""
    update = {"status": "resolved", "resolved_at": _now_iso()}
    if resolution:
        update["resolution"] = resolution
    try:
        collection = database.get_collection("conflicts")
        collection.update_one({"conflict_id": conflict_id}, {"$set": update})
    except Exception as e:
        print(f"Warning: Could not update conflict: {e}")
