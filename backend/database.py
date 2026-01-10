"""
MongoDB database connection and operations for Legal Strategy Council.

This module manages the MongoDB connection and provides collection accessors.
MongoDB is used as the coordination backbone for multi-agent collaboration,
storing not just data but also agent runs, reasoning steps, and inter-agent messages.
"""
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional
import config

_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_client() -> MongoClient:
    """Get or create MongoDB client."""
    global _client
    if _client is None:
        _client = MongoClient(config.MONGODB_URI)
    return _client


def get_database() -> Database:
    """Get the database instance."""
    global _db
    if _db is None:
        client = get_client()
        _db = client[config.DATABASE_NAME]
    return _db


def get_collection(collection_name: str) -> Collection:
    """Get a specific collection."""
    db = get_database()
    return db[collection_name]


def close_connection():
    """Close the MongoDB connection."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None


# ============================================================================
# Collection Accessors
# ============================================================================

def get_cases_collection() -> Collection:
    """Cases collection - stores case facts and metadata."""
    return get_collection(config.COLLECTIONS["cases"])


def get_arguments_collection() -> Collection:
    """Arguments collection - stores Harvey and Louis arguments."""
    return get_collection(config.COLLECTIONS["arguments"])


def get_counterarguments_collection() -> Collection:
    """Counterarguments collection - stores Tanner's attacks."""
    return get_collection(config.COLLECTIONS["counterarguments"])


def get_conflicts_collection() -> Collection:
    """Conflicts collection - stores detected disagreements."""
    return get_collection(config.COLLECTIONS["conflicts"])


def get_strategies_collection() -> Collection:
    """Strategies collection - stores Jessica's final synthesis."""
    return get_collection(config.COLLECTIONS["strategies"])


def get_agent_runs_collection() -> Collection:
    """Agent runs collection - tracks agent execution for auditability."""
    return get_collection(config.COLLECTIONS["agent_runs"])


def get_reasoning_steps_collection() -> Collection:
    """Reasoning steps collection - stores step-by-step agent thinking."""
    return get_collection(config.COLLECTIONS["reasoning_steps"])


def get_agent_messages_collection() -> Collection:
    """Agent messages collection - stores inter-agent communication."""
    return get_collection(config.COLLECTIONS["agent_messages"])


# ============================================================================
# Initialization
# ============================================================================

def _safe_create_index(collection, index_spec, **kwargs):
    """Create an index, ignoring errors if it already exists or has conflicts."""
    try:
        collection.create_index(index_spec, **kwargs)
    except Exception as e:
        # Index might already exist or have conflicting data - not critical
        print(f"Note: Index {index_spec} on {collection.name}: {e}")


def init_collections():
    """Initialize collections with indexes.

    This creates all required collections and indexes for the legal strategy system.
    Indexes improve query performance and enforce uniqueness where needed.
    """
    db = get_database()

    # Cases collection
    _safe_create_index(db[config.COLLECTIONS["cases"]], "case_id", unique=True)

    # Arguments collection (Harvey, Louis)
    _safe_create_index(db[config.COLLECTIONS["arguments"]], "case_id")
    _safe_create_index(db[config.COLLECTIONS["arguments"]], "argument_id", unique=True)
    _safe_create_index(db[config.COLLECTIONS["arguments"]], "agent")

    # Counterarguments collection (Tanner)
    _safe_create_index(db[config.COLLECTIONS["counterarguments"]], "case_id")
    _safe_create_index(db[config.COLLECTIONS["counterarguments"]], "counterargument_id", unique=True)

    # Conflicts collection
    _safe_create_index(db[config.COLLECTIONS["conflicts"]], "case_id")
    _safe_create_index(db[config.COLLECTIONS["conflicts"]], "conflict_id", unique=True)

    # Strategies collection (Jessica)
    _safe_create_index(db[config.COLLECTIONS["strategies"]], "case_id")
    _safe_create_index(db[config.COLLECTIONS["strategies"]], "strategy_id", unique=True)
    _safe_create_index(db[config.COLLECTIONS["strategies"]], [("case_id", 1), ("version", -1)])

    # Agent runs collection - for tracking agent executions
    _safe_create_index(db[config.COLLECTIONS["agent_runs"]], "run_id", unique=True)
    _safe_create_index(db[config.COLLECTIONS["agent_runs"]], "case_id")
    _safe_create_index(db[config.COLLECTIONS["agent_runs"]], "agent")

    # Reasoning steps collection - step-by-step traces
    _safe_create_index(db[config.COLLECTIONS["reasoning_steps"]], "step_id", unique=True)
    _safe_create_index(db[config.COLLECTIONS["reasoning_steps"]], "run_id")

    # Agent messages collection - inter-agent communication
    _safe_create_index(db[config.COLLECTIONS["agent_messages"]], "message_id", unique=True)
    _safe_create_index(db[config.COLLECTIONS["agent_messages"]], "case_id")
    _safe_create_index(db[config.COLLECTIONS["agent_messages"]], [("sender", 1), ("recipient", 1)])

    print("Collections initialized.")


def ensure_collections():
    """Ensure all collections exist (creates them if needed).

    This is a best-effort function that swallows exceptions for offline/dry runs.
    """
    db = get_database()
    if db is None:
        return

    for collection_name in config.COLLECTIONS.values():
        try:
            db.create_collection(collection_name)
        except Exception:
            # Collection already exists or other error
            pass
