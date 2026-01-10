"""
Configuration settings for the Legal Strategy Council application.

Agent names inspired by the TV show "Suits":
- Harvey: Lead Trial Strategist (The Closer)
- Louis: Precedent & Research Expert (The Savant)
- Tanner: Adversarial Counsel (The Destroyer)
- Jessica: Managing Partner / Moderator (The Mediator)
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"  # Smaller model with higher rate limits
GROQ_TEMPERATURE = 0.7
GROQ_MAX_TOKENS = 1500  # Reduced to stay within rate limits

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "legal_war_room")

# Collection Names
COLLECTIONS = {
    # Core data collections
    "cases": "cases",
    "arguments": "arguments",
    "counterarguments": "counterarguments",
    "conflicts": "conflicts",
    "strategies": "strategies",
    # Coordination collections (from LegalServer-main)
    "agent_runs": "agent_runs",
    "reasoning_steps": "reasoning_steps",
    "agent_messages": "agent_messages",
}

# Agent Names (Suits-inspired)
AGENT_NAMES = {
    "harvey": "Harvey",        # Lead Trial Strategist
    "louis": "Louis",          # Precedent & Research Expert
    "tanner": "Tanner",        # Adversarial Counsel
    "jessica": "Jessica",      # Managing Partner / Moderator
}

# Agent Descriptions (for UI display)
AGENT_DESCRIPTIONS = {
    "Harvey": "Lead Trial Strategist - Develops bold, winning strategies",
    "Louis": "Precedent Expert - Master of case law and legal research",
    "Tanner": "Adversarial Counsel - Ruthlessly attacks your strategy",
    "Jessica": "Managing Partner - Synthesizes and delivers final strategy",
}

# Agent Colors (for UI theming)
AGENT_COLORS = {
    "Harvey": "#3182ce",    # Blue
    "Louis": "#805ad5",     # Purple
    "Tanner": "#e53e3e",    # Red
    "Jessica": "#38a169",   # Green
}

# Multi-round deliberation settings
DELIBERATION_ROUNDS = 2  # Number of Harvey <-> Tanner exchanges before Jessica synthesizes
