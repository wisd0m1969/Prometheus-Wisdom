"""Community Q&A component — browse and contribute shared knowledge.

Users can search community Q&A, submit their own, vote, and report.
All content is PII-sanitized before storage.
"""

from __future__ import annotations

import streamlit as st


def render_community() -> None:
    """Render the Community Q&A page."""
    st.header("🌍 Community Knowledge")
    st.caption("Learn from the community. Share your knowledge anonymously.")

    community = st.session_state.community
    profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)
    lang = profile.language or "en"

    tab_browse, tab_submit = st.tabs(["Browse Q&A", "Share Knowledge"])

    with tab_browse:
        # Search
        query = st.text_input("Search community knowledge", placeholder="e.g., What is machine learning?")

        if query:
            results = community.search(query, language=lang, limit=10)
        else:
            results = community.get_top(language=lang, limit=10)

        if not results:
            st.info("No community Q&A found yet. Be the first to share!")
        else:
            for qa in results:
                with st.container():
                    st.markdown(f"**Q:** {qa['question']}")
                    st.markdown(f"**A:** {qa['answer']}")
                    col_up, col_down, col_report, col_score = st.columns([1, 1, 1, 2])
                    with col_up:
                        if st.button("👍", key=f"up_{qa['id']}"):
                            community.vote(qa["id"], upvote=True)
                            st.rerun()
                    with col_down:
                        if st.button("👎", key=f"down_{qa['id']}"):
                            community.vote(qa["id"], upvote=False)
                            st.rerun()
                    with col_report:
                        if st.button("🚩", key=f"report_{qa['id']}", help="Report inappropriate content"):
                            community.report(qa["id"], reason="user_report")
                            st.toast("Reported. Thank you for keeping the community safe.")
                    with col_score:
                        score = qa.get("upvotes", 0) - qa.get("downvotes", 0)
                        st.caption(f"Score: {score}")
                    st.divider()

    with tab_submit:
        st.subheader("Share a Q&A Pair")
        st.write("Help others learn! Your submission will be anonymized and PII-sanitized.")

        with st.form("submit_qa"):
            question = st.text_input("Question", placeholder="What question did you have?")
            answer = st.text_area("Answer", placeholder="What was the helpful answer?", height=150)
            category = st.selectbox(
                "Category",
                options=["general", "ai_basics", "coding", "prompt_engineering", "ethics", "tools"],
                format_func=lambda x: x.replace("_", " ").title(),
            )
            submitted = st.form_submit_button("Submit", type="primary")

            if submitted:
                if question.strip() and answer.strip():
                    qa_id = community.submit(question, answer, language=lang, category=category)
                    st.success(f"Thank you! Your Q&A has been shared (#{qa_id}).")
                else:
                    st.warning("Please fill in both the question and answer.")
