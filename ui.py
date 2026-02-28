#!/usr/bin/env python3
"""
Streamlit UI for the Self-Healing SRE Agent.

This provides a beautiful, interactive interface to:
1. Start/stop the FastAPI application
2. Trigger crashes
3. Monitor the self-healing workflow in real-time
4. View traces in LangSmith
5. See the final Pull Request

Run with: streamlit run ui.py
"""

import os
import time
from datetime import datetime, timezone

import httpx
import streamlit as st
from dotenv import load_dotenv

# Import our modules
from config import settings
from graph import sre_graph
from state import create_initial_state

# Load environment variables
load_dotenv()


# Page configuration
st.set_page_config(
    page_title="Self-Healing SRE Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)


def check_app_running() -> bool:
    """Check if the FastAPI app is running."""
    try:
        response = httpx.get(f"http://localhost:{settings.app_port}/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def trigger_crash() -> tuple[bool, str]:
    """Trigger the crash in the FastAPI app."""
    try:
        response = httpx.get(
            f"http://localhost:{settings.app_port}/api/data",
            headers={"X-Trigger-Bug": "true"},
            timeout=5.0
        )

        if response.status_code == 500:
            return True, "Crash triggered successfully! Error logged to app_logs.txt"
        else:
            return False, f"Expected 500 error, got {response.status_code}"

    except httpx.ConnectError:
        return False, "FastAPI app is not running. Start it first!"
    except Exception as e:
        return False, f"Error: {str(e)}"


def run_workflow():
    """Execute the self-healing workflow with real-time updates."""

    # Create initial state
    initial_error = f"""
🚨 ALERT: Application Error Detected

Endpoint: /api/data
Status: 500 Internal Server Error
Error Type: KeyError
Timestamp: {datetime.now(timezone.utc).isoformat()}

The monitoring system has detected a crash in the production API.
Please investigate and fix the issue.
"""

    initial_state = create_initial_state(initial_error)

    config = {
        "configurable": {
            "thread_id": f"sre-ui-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
    }

    # Create containers for real-time updates
    status_container = st.container()
    steps_container = st.container()
    result_container = st.container()

    with status_container:
        st.info("🤖 Executing self-healing workflow...")
        progress_bar = st.progress(0)
        status_text = st.empty()

    try:
        # Stream the workflow execution
        step_count = 0
        node_names = []

        for output in sre_graph.stream(initial_state, config):
            step_count += 1
            node_name = list(output.keys())[0]
            node_names.append(node_name)
            state_data = output[node_name]

            # Update progress
            progress_bar.progress(min(step_count * 20, 100))
            status_text.text(f"Step {step_count}: {node_name.title()}...")

            # Display step details
            with steps_container:
                with st.expander(f"Step {step_count}: {node_name.title()}", expanded=True):
                    if node_name == "investigator":
                        st.write("🔍 **Investigator Agent**")
                        st.write(f"- Iteration: {state_data.get('iteration_count', 0)}")
                        st.write(f"- Root cause found: {state_data.get('root_cause_identified', False)}")
                        if state_data.get('root_cause_analysis'):
                            st.code(state_data['root_cause_analysis'][:500] + "...")

                    elif node_name == "mechanic":
                        st.write("🔧 **Mechanic Agent**")
                        st.write("- Generating code fix...")
                        if state_data.get('fix_code'):
                            st.code(state_data['fix_code'][:500] + "...", language="python")

                    elif node_name == "validator":
                        st.write("✅ **Validator Node**")
                        validated = state_data.get('fix_validated', False)
                        if validated:
                            st.success("✅ All tests passed!")
                        else:
                            st.error("❌ Tests failed")
                            errors = state_data.get('validation_errors', [])
                            for error in errors:
                                st.write(f"  - {error}")

                    elif node_name == "pr_creator":
                        st.write("📝 **PR Creator Node**")
                        st.write("- Creating GitHub Pull Request...")

            time.sleep(0.5)  # Small delay for better UX

        # Final results
        progress_bar.progress(100)
        status_text.text("✅ Workflow completed!")

        # Get final state
        final_state = state_data

        with result_container:
            st.markdown("---")
            st.markdown("## 📊 Final Results")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if final_state.get('root_cause_identified'):
                    st.success("✅ Root Cause Found")
                else:
                    st.error("❌ Root Cause Not Found")

            with col2:
                if final_state.get('fix_validated'):
                    st.success("✅ Fix Validated")
                else:
                    st.error("❌ Fix Invalid")

            with col3:
                pr_status = final_state.get('pr_status', 'pending')
                if pr_status == 'created':
                    st.success("✅ PR Created")
                else:
                    st.error(f"❌ PR {pr_status}")

            with col4:
                iterations = final_state.get('iteration_count', 0)
                st.metric("Iterations", iterations)

            # Display PR if created
            if final_state.get('pr_url'):
                st.markdown("### 🎉 Pull Request")
                st.code(final_state['pr_url'], language="text")

            # Display root cause analysis
            if final_state.get('root_cause_analysis'):
                with st.expander("📋 Root Cause Analysis", expanded=False):
                    st.write(final_state['root_cause_analysis'])

            # Display generated fix
            if final_state.get('fix_code'):
                with st.expander("🔧 Generated Fix Code", expanded=False):
                    st.code(final_state['fix_code'], language="python")

            # LangSmith trace link
            if settings.langchain_tracing_v2 and settings.langchain_api_key:
                st.markdown("### 🔗 LangSmith Trace")
                st.info(f"View detailed trace in LangSmith Project: **{settings.langchain_project}**")
                st.markdown("[Open LangSmith Dashboard](https://smith.langchain.com/)")

    except Exception as e:
        st.error(f"❌ Workflow failed: {str(e)}")
        st.exception(e)


def main():
    """Main Streamlit UI."""

    # Header
    st.markdown('<h1 class="main-header">🤖 Self-Healing SRE Agent</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; font-size: 1.2rem; color: #666;">'
        'Autonomous AI agent that detects crashes, analyzes logs, and creates fixes'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Check environment
        st.subheader("Environment Status")

        llm_model = settings.groq_model if settings.llm_provider == "groq" else settings.gemini_model
        if settings.groq_api_key or settings.gemini_api_key:
            st.success(f"✅ LLM: {settings.llm_provider} ({llm_model})")
        else:
            st.error("❌ No LLM API Key")

        if settings.langchain_tracing_v2 and settings.langchain_api_key:
            st.success("✅ LangSmith Tracing")
            st.caption(f"Project: {settings.langchain_project}")
        else:
            st.warning("⚠️ LangSmith Not Configured")

        if settings.github_token and settings.github_repo:
            st.success("✅ GitHub Integration")
        else:
            st.info("ℹ️ Demo Mode (No GitHub)")

        st.markdown("---")

        st.subheader("📖 About")
        st.markdown("""
        This agent demonstrates:
        - 🔍 Log analysis with LLMs
        - 🔧 Automated fix generation
        - ✅ Self-correction loops
        - 📝 GitHub PR automation
        - 📊 LangSmith observability
        """)

        st.markdown("---")
        st.caption("Built with LangGraph & Streamlit")

    # Main content area
    tab1, tab2, tab3 = st.tabs(["🚀 Control Panel", "📊 Workflow", "📚 Help"])

    with tab1:
        st.header("Control Panel")

        # Check API status
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("FastAPI Application")
            app_running = check_app_running()

            if app_running:
                st.success(f"✅ FastAPI app is running on port {settings.app_port}")
            else:
                st.error("❌ FastAPI app is not running")
                st.info("Start it with: `python app.py`")

        with col2:
            st.subheader("Quick Actions")

            if st.button("🔥 Trigger System Crash", type="primary", use_container_width=True):
                if app_running:
                    success, message = trigger_crash()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Start FastAPI app first!")

            st.caption("This sends a request with X-Trigger-Bug: true header")

        st.markdown("---")

        # Workflow execution
        st.header("🤖 Self-Healing Workflow")

        if st.button("🚀 Run Self-Healing Agent", type="primary", use_container_width=True):
            # Check if logs exist
            if not os.path.exists(settings.log_file):
                st.warning("⚠️ No logs found. Trigger a crash first!")
            else:
                run_workflow()

    with tab2:
        st.header("Workflow Architecture")

        st.markdown("""
        ```mermaid
        graph TD
            A[START] --> B[Investigator Agent]
            B -->|Root Cause Found| C[Mechanic Agent]
            B -->|Need More Data| B
            B -->|Max Iterations| Z[END]
            C --> D[Validator Node]
            D -->|Tests Pass| E[PR Creator]
            D -->|Tests Fail| B
            D -->|Max Attempts| Z
            E --> Z
        ```
        """)

        st.markdown("### 🔄 Self-Correction Loop")
        st.info(f"""
        When tests fail, the Validator routes back to the Investigator with error feedback.
        This allows the agent to reconsider its analysis and generate an improved fix.
        Maximum {settings.max_iterations} attempts to prevent infinite loops.
        """)

    with tab3:
        st.header("📚 Help & Documentation")

        with st.expander("🚀 Quick Start"):
            st.markdown("""
            1. **Configure API Keys**: Copy `.env.example` to `.env` and add your keys
            2. **Start FastAPI**: Run `python app.py` in a terminal
            3. **Trigger Crash**: Click "Trigger System Crash" button
            4. **Run Agent**: Click "Run Self-Healing Agent" button
            5. **View Results**: See the agent analyze, fix, and create a PR!
            """)

        with st.expander("🔑 Required API Keys"):
            st.markdown("""
            - **Groq** (free): For LLM reasoning — primary provider
            - **Gemini** (free): Alternative LLM provider
            - **LangSmith**: For tracing and observability (optional)
            - **GitHub**: For actual PR creation (optional, works in demo mode)

            Get keys at:
            - Groq: https://console.groq.com
            - Gemini: https://aistudio.google.com
            - LangSmith: https://smith.langchain.com/
            - GitHub: https://github.com/settings/tokens
            """)

        with st.expander("🎯 The Bug"):
            st.markdown("""
            The FastAPI app has an intentional KeyError bug:

            ```python
            user_config = {
                "user_id": 12345,
                # Missing: "api_key"
            }

            api_key = user_config["api_key"]  # KeyError!
            ```

            The self-healing agent will:
            1. Detect this error in logs
            2. Analyze the stack trace
            3. Generate a fix using `.get()` method
            4. Validate the fix
            5. Create a PR with the solution
            """)

        with st.expander("📊 LangSmith Observability"):
            st.markdown("""
            LangSmith provides:
            - Complete trace of all LLM calls
            - Agent decision-making visualization
            - Tool usage tracking
            - Performance metrics
            - Error debugging

            **This is essential for interviews!** You can show recruiters exactly how
            your agent thinks, loops, and corrects itself.
            """)


if __name__ == "__main__":
    main()
