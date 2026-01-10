"""
Legal Strategy Council API - FastAPI Backend
Multi-agent legal strategy system using MongoDB Atlas and Groq LLM.
"""
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Optional
import json

from models.schemas import CaseCreate, CaseResponse
from services.orchestrator import get_orchestrator
import database

# Initialize FastAPI app
app = FastAPI(
    title="Legal Strategy Council API",
    description="Multi-agent legal strategy system for hackathon",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Store for tracking active analysis tasks
_active_tasks: dict = {}


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    try:
        database.init_collections()
        print("Database collections initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    database.close_connection()


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "Legal Strategy Council API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/cases", response_model=dict)
async def create_case(case_data: CaseCreate, background_tasks: BackgroundTasks):
    """
    Create a new case and trigger the multi-agent analysis.
    Returns the case_id immediately while analysis runs in background.
    """
    orchestrator = get_orchestrator()

    # Create the case in MongoDB
    case = orchestrator.create_case(
        title=case_data.title,
        facts=case_data.facts,
        jurisdiction=case_data.jurisdiction,
        stakes=case_data.stakes
    )

    # Mark case as active for SSE streaming
    _active_tasks[case.case_id] = {
        "status": "pending",
        "events": []
    }

    return {
        "case_id": case.case_id,
        "title": case.title,
        "status": "created",
        "message": "Case created. Connect to /api/cases/{case_id}/stream for real-time updates."
    }


@app.get("/api/cases/{case_id}/stream")
async def stream_case_analysis(case_id: str):
    """
    SSE endpoint that streams agent updates in real-time.
    Events: agent_started, agent_completed, conflict_detected, strategy_ready, error
    """
    orchestrator = get_orchestrator()

    # Check if case exists
    case = orchestrator._get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    async def event_generator():
        """Generate SSE events from the orchestrator."""
        try:
            async for event in orchestrator.run_analysis(case_id):
                yield event
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return EventSourceResponse(event_generator())


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """
    Get full case with all arguments, counterarguments, conflicts, and strategy.
    """
    orchestrator = get_orchestrator()
    result = orchestrator.get_case_with_details(case_id)

    if not result:
        raise HTTPException(status_code=404, detail="Case not found")

    return result


@app.get("/api/cases/{case_id}/arguments")
async def get_case_arguments(case_id: str):
    """Get all arguments for a case."""
    orchestrator = get_orchestrator()

    # Check if case exists
    case = orchestrator._get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    arguments = orchestrator.get_arguments(case_id)
    return {"case_id": case_id, "arguments": arguments}


@app.get("/api/cases/{case_id}/conflicts")
async def get_case_conflicts(case_id: str):
    """Get all conflicts for a case."""
    orchestrator = get_orchestrator()

    # Check if case exists
    case = orchestrator._get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    conflicts = orchestrator.get_conflicts(case_id)
    return {"case_id": case_id, "conflicts": conflicts}


@app.get("/api/cases/{case_id}/strategy")
async def get_case_strategy(case_id: str):
    """Get the final strategy for a case."""
    orchestrator = get_orchestrator()

    # Check if case exists
    case = orchestrator._get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    strategy = orchestrator.get_strategy(case_id)
    if not strategy:
        return {
            "case_id": case_id,
            "strategy": None,
            "message": "Strategy not yet generated. Run analysis first."
        }

    return {"case_id": case_id, "strategy": strategy}


# Additional utility endpoints

@app.get("/api/cases")
async def list_cases():
    """List all cases (for debugging/admin purposes)."""
    cases_collection = database.get_cases_collection()
    cases = list(cases_collection.find().sort("created_at", -1).limit(20))
    for case in cases:
        if "_id" in case:
            del case["_id"]
    return {"cases": cases}


@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: str):
    """Delete a case and all associated data."""
    # Delete from all collections
    database.get_cases_collection().delete_many({"case_id": case_id})
    database.get_arguments_collection().delete_many({"case_id": case_id})
    database.get_counterarguments_collection().delete_many({"case_id": case_id})
    database.get_conflicts_collection().delete_many({"case_id": case_id})
    database.get_strategies_collection().delete_many({"case_id": case_id})

    return {"message": f"Case {case_id} and all associated data deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
