"""Code Playground component — in-browser Python code editor with AI assistance.

Allows users to write, run, and debug Python code with WISDOM's help.
Uses restricted exec for safe execution of simple Python snippets.
"""

from __future__ import annotations

import io
import contextlib
import traceback

import streamlit as st


_STARTER_EXAMPLES = {
    "Hello World": 'print("Hello, World!")',
    "Simple Loop": "for i in range(5):\n    print(f'Number {i}')",
    "List Comprehension": "squares = [x**2 for x in range(10)]\nprint(squares)",
    "Function": "def greet(name):\n    return f'Hello, {name}!'\n\nprint(greet('WISDOM'))",
    "Dictionary": "fruits = {'apple': 3, 'banana': 5, 'cherry': 2}\nfor fruit, count in fruits.items():\n    print(f'{fruit}: {count}')",
}

# Safe built-ins for code execution
_SAFE_BUILTINS = {
    "print": print, "range": range, "len": len, "str": str, "int": int,
    "float": float, "bool": bool, "list": list, "dict": dict, "set": set,
    "tuple": tuple, "type": type, "abs": abs, "max": max, "min": min,
    "sum": sum, "round": round, "sorted": sorted, "enumerate": enumerate,
    "zip": zip, "map": map, "filter": filter, "reversed": reversed,
    "any": any, "all": all, "isinstance": isinstance, "input": lambda *a: "",
    "True": True, "False": False, "None": None,
}


def _safe_exec(code: str, timeout_hint: int = 5) -> tuple[str, str]:
    """Execute Python code in a restricted environment.

    Returns:
        Tuple of (stdout_output, error_output).
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    safe_globals = {"__builtins__": _SAFE_BUILTINS}

    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(code, safe_globals)
    except Exception:
        stderr_capture.write(traceback.format_exc())

    return stdout_capture.getvalue(), stderr_capture.getvalue()


def render_code_playground() -> None:
    """Render the Code Playground page."""
    st.header("💻 Code Playground")
    st.caption("Write and run Python code right in your browser. WISDOM can help you learn!")

    # Starter examples
    col1, col2 = st.columns([3, 1])
    with col2:
        example = st.selectbox(
            "Load Example",
            options=["(empty)"] + list(_STARTER_EXAMPLES.keys()),
        )

    # Code editor
    default_code = _STARTER_EXAMPLES.get(example, "") if example != "(empty)" else ""
    if "playground_code" not in st.session_state:
        st.session_state.playground_code = default_code

    if example != "(empty)" and default_code:
        st.session_state.playground_code = default_code

    code = st.text_area(
        "Python Code",
        value=st.session_state.playground_code,
        height=250,
        key="code_editor",
        help="Write Python code here. Click 'Run' to execute.",
    )
    st.session_state.playground_code = code

    # Action buttons
    col_run, col_explain, col_fix = st.columns(3)

    with col_run:
        run_clicked = st.button("▶️ Run Code", use_container_width=True, type="primary")

    with col_explain:
        explain_clicked = st.button("💡 Explain Code", use_container_width=True)

    with col_fix:
        fix_clicked = st.button("🔧 Fix Errors", use_container_width=True)

    # Run code
    if run_clicked and code.strip():
        st.subheader("Output")
        stdout, stderr = _safe_exec(code)
        if stdout:
            st.code(stdout, language="text")
        if stderr:
            st.error("Error:")
            st.code(stderr, language="text")
        if not stdout and not stderr:
            st.info("Code ran successfully with no output.")

    # AI Explain
    if explain_clicked and code.strip():
        st.subheader("Explanation")
        if hasattr(st.session_state, "chat_engine"):
            try:
                profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)
                message_placeholder = st.empty()
                full_response = ""
                for chunk in st.session_state.chat_engine.generate_stream(
                    user_message=f"Explain this Python code step by step:\n```python\n{code}\n```",
                    profile=profile,
                    history=[],
                    tone_hints={},
                ):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            except Exception as e:
                st.warning(f"AI explanation unavailable: {e}")
        else:
            st.info("Connect an LLM to get AI-powered code explanations.")

    # AI Fix
    if fix_clicked and code.strip():
        stdout, stderr = _safe_exec(code)
        if stderr:
            st.subheader("AI Fix Suggestion")
            if hasattr(st.session_state, "chat_engine"):
                try:
                    profile = st.session_state.profile_manager.get_or_create(st.session_state.user_id)
                    message_placeholder = st.empty()
                    full_response = ""
                    for chunk in st.session_state.chat_engine.generate_stream(
                        user_message=(
                            f"Fix this Python code. Show the corrected code and explain what was wrong:\n"
                            f"```python\n{code}\n```\nError:\n```\n{stderr}\n```"
                        ),
                        profile=profile,
                        history=[],
                        tone_hints={},
                    ):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                except Exception as e:
                    st.warning(f"AI fix unavailable: {e}")
            else:
                st.info("Connect an LLM to get AI-powered error fixing.")
        else:
            st.success("No errors found! The code runs correctly.")
