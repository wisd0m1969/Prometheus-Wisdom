"""FastAPI REST API — programmatic access to WISDOM.

Endpoints: chat, SSE streaming, profiles (CRUD), learning path,
progress, feedback, assessment, health. Includes rate limiting
via in-memory counter.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Generator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from wisdom import Wisdom, __version__

app = FastAPI(
    title="PROMETHEUS WISDOM API",
    description="AI Companion for Humanity — REST API",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared WISDOM instance
_wisdom: Wisdom | None = None

# Simple in-memory rate limiter: {ip: [timestamps]}
_rate_limits: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 100  # requests per minute


def get_wisdom() -> Wisdom:
    global _wisdom
    if _wisdom is None:
        _wisdom = Wisdom()
    return _wisdom


def _check_rate_limit(request: Request) -> None:
    """Check rate limit for the requesting IP."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    # Clean old entries
    _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < 60]
    if len(_rate_limits[ip]) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    _rate_limits[ip].append(now)


# --- Request/Response Models ---

class ChatRequest(BaseModel):
    user_id: str
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    language: str
    mode: str = "free_chat"


class ProfileCreate(BaseModel):
    user_id: str
    name: str = ""
    language: str = "en"


class ProfileUpdate(BaseModel):
    name: str | None = None
    language: str | None = None
    skill_level: float | None = None
    interests: list[str] | None = None
    goals: list[str] | None = None


class FeedbackRequest(BaseModel):
    user_id: str = ""
    rating: int = Field(ge=1, le=5)
    comment: str = ""
    category: str = "general"


class AssessmentAnswer(BaseModel):
    answer: str | int | float


# --- Endpoints ---

@app.post("/api/v1/chat")
def chat(request: ChatRequest, req: Request):
    """Send a message to WISDOM and get a response.

    If stream=true in body, returns Server-Sent Events stream.
    Otherwise returns a full ChatResponse JSON.
    """
    _check_rate_limit(req)
    w = get_wisdom()

    # SSE streaming mode
    if request.stream:
        def event_generator() -> Generator[str, None, None]:
            from wisdom.voice.chat_engine import ChatEngine

            profile = w.profile_manager.get_or_create(request.user_id)
            history = w.memory.get_history(request.user_id)
            tone_hints = w.tone_adapter.get_adaptation(profile, history)

            safe_message = request.message
            if not w.llm_provider.is_local():
                safe_message = w.privacy_manager.sanitize(request.message)

            engine = ChatEngine(w.llm_provider)
            full_response = ""
            for chunk in engine.generate_stream(
                user_message=safe_message,
                profile=profile,
                history=history,
                tone_hints=tone_hints,
            ):
                full_response += chunk
                yield f"data: {chunk}\n\n"

            w.memory.add_message(request.user_id, "user", request.message)
            w.memory.add_message(request.user_id, "wisdom", full_response)
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Synchronous mode
    response = w.chat(request.message, user_id=request.user_id)
    profile = w.profile_manager.get(request.user_id)
    return ChatResponse(
        response=response,
        language=profile.language if profile else "en",
        mode=w.orchestrator._current_mode if hasattr(w.orchestrator, "_current_mode") else "free_chat",
    )


@app.post("/api/v1/chat/stream")
def chat_stream(request: ChatRequest, req: Request):
    """Send a message to WISDOM and get a Server-Sent Events stream."""
    _check_rate_limit(req)
    w = get_wisdom()

    def event_generator() -> Generator[str, None, None]:
        from wisdom.voice.chat_engine import ChatEngine

        profile = w.profile_manager.get_or_create(request.user_id)
        history = w.memory.get_history(request.user_id)
        tone_hints = w.tone_adapter.get_adaptation(profile, history)

        safe_message = request.message
        if not w.llm_provider.is_local():
            safe_message = w.privacy_manager.sanitize(request.message)

        engine = ChatEngine(w.llm_provider)
        full_response = ""
        for chunk in engine.generate_stream(
            user_message=safe_message,
            profile=profile,
            history=history,
            tone_hints=tone_hints,
        ):
            full_response += chunk
            yield f"data: {chunk}\n\n"

        # Update memory after streaming
        w.memory.add_message(request.user_id, "user", request.message)
        w.memory.add_message(request.user_id, "wisdom", full_response)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/v1/profile", status_code=201)
def create_profile(request: ProfileCreate):
    """Create a new user profile."""
    w = get_wisdom()
    existing = w.profile_manager.get(request.user_id)
    if existing:
        raise HTTPException(status_code=409, detail="Profile already exists")
    profile = w.profile_manager.create(request.user_id, name=request.name, language=request.language)
    return profile.to_dict()


@app.get("/api/v1/profile/{user_id}")
def get_profile(user_id: str):
    """Get user profile."""
    w = get_wisdom()
    profile = w.profile_manager.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile.to_dict()


@app.put("/api/v1/profile/{user_id}")
def update_profile(user_id: str, update: ProfileUpdate):
    """Update user profile."""
    w = get_wisdom()
    profile = w.profile_manager.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    if update.name is not None:
        profile.name = update.name
    if update.language is not None:
        profile.language = update.language
    if update.skill_level is not None:
        profile.skill_level = update.skill_level
    if update.interests is not None:
        profile.interests = update.interests
    if update.goals is not None:
        profile.goals = update.goals

    w.profile_manager.update(profile)
    return profile.to_dict()


@app.delete("/api/v1/profile/{user_id}")
def delete_profile(user_id: str):
    """Delete user profile and all associated data."""
    w = get_wisdom()
    profile = w.profile_manager.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    w.profile_manager.delete(user_id)
    w.memory.clear_session(user_id)
    return {"status": "deleted", "user_id": user_id}


@app.get("/api/v1/progress/{user_id}")
def get_progress(user_id: str):
    """Get user learning progress."""
    w = get_wisdom()
    profile = w.profile_manager.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    from wisdom.soul.learning_path import LearningPath

    path = LearningPath()
    progress = path.get_progress([])
    return {
        "level": profile.skill_level,
        "progress": progress,
    }


@app.get("/api/v1/learning-path/{user_id}")
def get_learning_path(user_id: str):
    """Get personalized learning path."""
    from wisdom.soul.learning_path import LearningPath

    w = get_wisdom()
    profile = w.profile_manager.get(user_id)

    path = LearningPath()
    if profile:
        personalized = path.generate_personalized_path(
            starting_level=max(1, int(profile.skill_level / 2) + 1),
            interests=profile.interests,
        )
        return {
            "modules": personalized,
            "next_lesson": path.get_next_lesson([]),
        }

    return {
        "modules": path.get_all_modules(),
        "next_lesson": path.get_next_lesson([]),
    }


@app.post("/api/v1/assessment/start")
def start_assessment():
    """Start a new skill assessment."""
    from wisdom.soul.skill_assessor import SkillAssessor

    assessor = SkillAssessor()
    question = assessor.start_assessment()
    return {"question": question, "status": "started"}


@app.post("/api/v1/feedback")
def submit_feedback(request: FeedbackRequest, req: Request):
    """Submit user feedback."""
    _check_rate_limit(req)
    from wisdom.heart.feedback_loop import FeedbackLoop

    w = get_wisdom()
    fb = FeedbackLoop(w.config.db_path)
    fb_id = fb.submit(
        rating=request.rating,
        comment=request.comment,
        user_id=request.user_id,
        category=request.category,
    )
    return {"id": fb_id, "status": "received"}


@app.get("/api/v1/feedback/stats")
def feedback_stats():
    """Get feedback statistics."""
    from wisdom.heart.feedback_loop import FeedbackLoop

    w = get_wisdom()
    fb = FeedbackLoop(w.config.db_path)
    return fb.get_stats()


@app.get("/api/v1/profile/{user_id}/export")
def export_user_data(user_id: str):
    """Export all user data as JSON (GDPR compliance)."""
    w = get_wisdom()
    data = w.export_user_data(user_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@app.get("/api/v1/analytics")
def get_analytics(days: int = 30):
    """Get analytics summary (DAU, retention, completion rates)."""
    from wisdom.core.analytics import Analytics

    w = get_wisdom()
    analytics = Analytics(w.config.db_path)
    return analytics.get_summary(days)


@app.get("/api/v1/health")
def health_check():
    """Check WISDOM system health."""
    w = get_wisdom()
    return w.health_check()
