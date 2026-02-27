"""FastAPI REST API — programmatic access to WISDOM."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


def get_wisdom() -> Wisdom:
    global _wisdom
    if _wisdom is None:
        _wisdom = Wisdom()
    return _wisdom


# --- Request/Response Models ---

class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    language: str


class ProfileUpdate(BaseModel):
    name: str | None = None
    language: str | None = None
    skill_level: float | None = None
    interests: list[str] | None = None
    goals: list[str] | None = None


class FeedbackRequest(BaseModel):
    user_id: str = ""
    rating: int
    comment: str = ""


# --- Endpoints ---

@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Send a message to WISDOM and get a response."""
    w = get_wisdom()
    response = w.chat(request.message, user_id=request.user_id)
    profile = w.profile_manager.get(request.user_id)
    return ChatResponse(
        response=response,
        language=profile.language if profile else "en",
    )


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


@app.get("/api/v1/progress/{user_id}")
def get_progress(user_id: str):
    """Get user learning progress."""
    w = get_wisdom()
    profile = w.profile_manager.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    from wisdom.soul.learning_path import LearningPath

    path = LearningPath()
    progress = path.get_progress([])  # TODO: load completed lessons from DB
    return {
        "level": profile.skill_level,
        "progress": progress,
    }


@app.get("/api/v1/learning-path/{user_id}")
def get_learning_path(user_id: str):
    """Get personalized learning path."""
    from wisdom.soul.learning_path import LearningPath

    path = LearningPath()
    next_lesson = path.get_next_lesson([])  # TODO: load from DB
    return {
        "modules": path.get_all_modules(),
        "next_lesson": next_lesson,
    }


@app.post("/api/v1/feedback")
def submit_feedback(request: FeedbackRequest):
    """Submit user feedback."""
    from wisdom.heart.feedback_loop import FeedbackLoop

    w = get_wisdom()
    fb = FeedbackLoop(w.config.db_path)
    fb_id = fb.submit(
        rating=request.rating,
        comment=request.comment,
        user_id=request.user_id,
    )
    return {"id": fb_id, "status": "received"}


@app.get("/api/v1/health")
def health_check():
    """Check WISDOM system health."""
    w = get_wisdom()
    return w.health_check()
