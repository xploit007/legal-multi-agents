"""
Legal Strategy Council Agents Module.

Agents inspired by the TV show "Suits":
- Harvey: Lead Trial Strategist (The Closer)
- Louis: Precedent & Research Expert (The Savant)
- Tanner: Adversarial Counsel (The Destroyer)
- Jessica: Managing Partner / Moderator (The Mediator)
"""
from .base_agent import BaseAgent
from .harvey import HarveyAgent
from .louis import LouisAgent
from .tanner import TannerAgent
from .jessica import JessicaAgent

__all__ = [
    "BaseAgent",
    "HarveyAgent",
    "LouisAgent",
    "TannerAgent",
    "JessicaAgent"
]
