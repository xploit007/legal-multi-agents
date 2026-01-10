# Legal Strategy Council

A multi-agent legal strategy system built for the MongoDB Hackathon. This application demonstrates **Statement 2: Multi-Agent Collaboration** using MongoDB Atlas as the coordination backbone.

**Agent names inspired by the TV show "Suits"**

## Overview

Legal Strategy Council employs four specialized AI agents that collaborate to analyze legal cases and develop winning strategies:

| Agent | Role | Nickname |
|-------|------|----------|
| **Harvey** | Lead Trial Strategist | "The Closer" |
| **Louis** | Precedent & Research Expert | "The Savant" |
| **Tanner** | Adversarial Counsel | "The Destroyer" |
| **Jessica** | Managing Partner / Moderator | "The Mediator" |

### Key Features

- **Multi-round deliberation**: Harvey and Tanner debate the strategy before Jessica synthesizes
- **Step-level tracing**: Every reasoning step is persisted to MongoDB for auditability
- **Inter-agent messaging**: Agents communicate through MongoDB for coordination
- **Real-time updates**: Watch agents analyze in real-time via SSE

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React with Vite and Tailwind CSS
- **Database**: MongoDB Atlas
- **LLM**: Groq API with Llama 3.3 70B (`llama-3.3-70b-versatile`)
- **Real-time Updates**: Server-Sent Events (SSE)
- **Coordination Layer**: Adapted from LegalServer-main

## Project Structure

```
legal-strategy-council/
├── backend/
│   ├── main.py              # FastAPI application and endpoints
│   ├── config.py            # Configuration settings
│   ├── database.py          # MongoDB connection management
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── agents/
│   │   ├── base_agent.py    # Base agent class
│   │   ├── harvey.py        # Harvey - Lead Trial Strategist
│   │   ├── louis.py         # Louis - Precedent Expert
│   │   ├── tanner.py        # Tanner - Adversarial Counsel
│   │   └── jessica.py       # Jessica - Managing Partner
│   ├── services/
│   │   ├── orchestrator.py      # Multi-round workflow orchestration
│   │   ├── conflict_detector.py # Conflict detection service
│   │   ├── mongo_utils.py       # MongoDB coordination utilities
│   │   └── langgraph_wrapper.py # Step-level tracing
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx          # Main application
│       ├── main.jsx         # Entry point
│       ├── index.css        # Tailwind styles
│       └── components/
│           ├── CaseInput.jsx     # Case input form
│           ├── AgentPanel.jsx    # Individual agent display
│           ├── DebateView.jsx    # Agent grid view
│           ├── ConflictView.jsx  # Conflict display
│           └── FinalStrategy.jsx # Final strategy display
├── .env.example
├── .gitignore
└── README.md
```

## MongoDB Collections

The application uses the following collections in the `legal_war_room` database:

| Collection | Purpose |
|------------|---------|
| `cases` | Stores case facts and metadata |
| `arguments` | Stores Harvey and Louis arguments |
| `counterarguments` | Stores Tanner's attacks |
| `conflicts` | Stores detected disagreements between agents |
| `strategies` | Stores Jessica's final synthesized strategies |
| `agent_runs` | Tracks agent execution for auditability |
| `reasoning_steps` | Stores step-by-step agent thinking |
| `agent_messages` | Stores inter-agent communication |

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- MongoDB Atlas account
- Groq API key

### 1. Clone and Configure

```bash
cd legal-strategy-council

# Copy environment template
cp .env.example .env
```

Edit `.env` with your credentials:

```env
GROQ_API_KEY=your_groq_api_key_here
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=legal_war_room
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cases` | POST | Create a new case and start analysis |
| `/api/cases/{case_id}/stream` | GET | SSE stream for real-time updates |
| `/api/cases/{case_id}` | GET | Get full case with all data |
| `/api/cases/{case_id}/arguments` | GET | Get all arguments for a case |
| `/api/cases/{case_id}/conflicts` | GET | Get all conflicts for a case |
| `/api/cases/{case_id}/strategy` | GET | Get final strategy for a case |

## How It Works

### Multi-Agent Workflow with Deliberation

```
┌─────────────────────────────────────────────────────────────────┐
│                         Case Input                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Harvey develops initial strategy                        │
│  (writes to arguments collection)                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Louis researches precedents                             │
│  (writes to arguments collection)                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Multi-Round Deliberation (2 rounds default)             │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ Tanner attacks  │───▶│ Harvey rebuts   │                     │
│  │ (counterargs)   │    │ (revised args)  │                     │
│  └─────────────────┘    └─────────────────┘                     │
│           │                      │                               │
│           ▼                      ▼                               │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ Tanner attacks  │───▶│ (final attack)  │                     │
│  │ again           │    │                 │                     │
│  └─────────────────┘    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Conflict Detection                                      │
│  (analyzes all arguments, writes to conflicts)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Jessica synthesizes final strategy                      │
│  (reads everything, writes to strategies)                        │
└─────────────────────────────────────────────────────────────────┘
```

### MongoDB as Coordination Backbone

- **Immediate persistence**: Each agent writes to MongoDB immediately upon completion
- **Cross-agent reading**: Agents read from MongoDB to access previous outputs
- **Step-level tracing**: Every reasoning step is persisted to `reasoning_steps`
- **Inter-agent messaging**: Agents communicate through `agent_messages`
- **Audit trail**: Complete history for replay and debugging

### Real-time Updates

The application uses Server-Sent Events (SSE) to push updates to the frontend:

- `agent_started`: When an agent begins analysis
- `agent_completed`: When an agent finishes with output
- `deliberation_round_started`: When a Harvey/Tanner round begins
- `deliberation_round_completed`: When a round finishes
- `conflict_detected`: When conflicts are identified
- `strategy_ready`: When final strategy is available

## Demo Case

The application comes pre-loaded with a demo case:

**NovaTech Solutions vs. Meridian Ventures**

A contract dispute involving a Series A investment agreement where the investor (Meridian) refuses to release the second tranche of funding, claiming the startup (NovaTech) didn't meet the customer milestone requirements.

## Architecture Highlights

- **Multi-round deliberation**: Harvey and Tanner debate before final synthesis
- **Step-level tracing**: Adapted from LegalServer-main for auditability
- **Async Processing**: Agents run asynchronously with thread pooling
- **Error Handling**: Graceful error handling with retry logic for LLM calls
- **Scalability**: MongoDB Atlas provides horizontal scaling
- **Real-time UI**: SSE provides efficient one-way communication

## Credits

- Agent coordination patterns adapted from **LegalServer-main**
- Agent names inspired by the TV show **Suits**
- Built with Groq Llama 3.3 70B and MongoDB Atlas

## License

MIT License - Built for MongoDB Hackathon 2024
