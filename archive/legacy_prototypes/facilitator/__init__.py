"""
AI Facilitator Service - Smart message broker for multi-AI communication.

Handles:
- Message routing between wrapped AI terminals
- Rate limit detection and buffering
- Provider switching (e.g., Gemini Pro → Flash)
- Session management
- Live broadcast streaming
"""

from .service import FacilitatorService
from .session import Session, Participant

__all__ = ["FacilitatorService", "Session", "Participant"]
