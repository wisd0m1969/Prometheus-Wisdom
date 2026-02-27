"""Progress dashboard — progress bars, skill radar chart, badges, stats.

Shows skill profile radar, learning progress per level,
earned achievements, and usage statistics including days active.
"""

from __future__ import annotations

import streamlit as st

from wisdom.core.constants import SKILL_CATEGORIES, BADGES, SKILL_LEVELS
from wisdom.soul.learning_path import LearningPath
from wisdom.soul.goal_tracker import GoalTracker


def render_dashboard() -> None:
    """Render the progress dashboard."""
    st.header("📊 Your Learning Dashboard")

    profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)

    # --- Skill Radar Chart ---
    st.subheader("🎯 Skill Profile")

    try:
        import plotly.graph_objects as go

        categories = list(SKILL_CATEGORIES.keys())
        labels = [SKILL_CATEGORIES[c]["label"] for c in categories]

        # Simulated scores based on skill level
        scores = [min(10, profile.skill_level + (i * 0.5)) for i, _ in enumerate(categories)]
        scores.append(scores[0])  # close the polygon
        labels.append(labels[0])

        fig = go.Figure(data=go.Scatterpolar(
            r=scores,
            theta=labels,
            fill="toself",
            fillcolor="rgba(76, 175, 80, 0.3)",
            line=dict(color="#4CAF50"),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            height=350,
            margin=dict(l=40, r=40, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.info("Install plotly for skill radar chart: pip install plotly")

    # --- Skill Level Description ---
    level_int = int(profile.skill_level)
    level_desc = SKILL_LEVELS.get(level_int, "")
    if level_desc:
        st.caption(f"Level {level_int}: {level_desc}")

    # --- Learning Progress ---
    st.subheader("📚 Learning Progress")

    path = LearningPath()
    progress = path.get_progress([])

    for level in sorted(path.modules.keys()):
        info = progress[level]
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(
                info["percentage"] / 100,
                text=f"Level {level}: {info['name']}",
            )
        with col2:
            st.write(f"{info['completed']}/{info['total']}")

    overall = progress["overall"]
    st.metric("Overall Progress", f"{overall['percentage']}%", f"{overall['completed']}/{overall['total']} lessons")

    # --- Achievements ---
    st.subheader("🏆 Achievements")

    goal_tracker = GoalTracker(st.session_state.config.db_path)
    earned = goal_tracker.get_badges(st.session_state.user_id)

    if earned:
        cols = st.columns(min(5, len(earned)))
        for i, badge in enumerate(earned):
            badge_info = BADGES.get(badge["badge_id"], {})
            with cols[i % 5]:
                st.metric(
                    badge["name"],
                    badge_info.get("icon", "✅"),
                )
    else:
        st.info("Start learning to earn your first badge! 🎖️")

    # All available badges
    with st.expander("🎖️ All Badges"):
        for badge_id, badge_info in BADGES.items():
            earned_ids = [b["badge_id"] for b in earned]
            status = "✅" if badge_id in earned_ids else "🔒"
            st.write(f"{badge_info.get('icon', '')} **{badge_info['name']}** {status} — {badge_info['trigger']}")

    # --- Statistics ---
    st.subheader("📈 Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        msg_count = len(st.session_state.memory.get_history(st.session_state.user_id))
        st.metric("Messages", msg_count)
    with col2:
        st.metric("Skill Level", f"{profile.skill_level:.1f}/10")
    with col3:
        st.metric("Badges Earned", len(earned))
    with col4:
        # Days active calculation
        goals = goal_tracker.get_goals(st.session_state.user_id)
        days_active = len(set(g.get("created_at", "")[:10] for g in goals if g.get("created_at")))
        st.metric("Days Active", max(1, days_active))

    # --- Goals Summary ---
    if profile.goals:
        st.subheader("🎯 Current Goals")
        for goal in profile.goals:
            st.write(f"- {goal}")
