"""
app.py – Streamlit entry-point for TestIQ.

Provides a multi-page dashboard covering:
    1. Dashboard     – KPI metrics and charts
    2. Requirements  – Enter and analyse requirements
    3. Test Cases    – Generate, view, edit, and export test cases
    4. Test Execution– Run tests and view results
    5. Defect Analysis – View, classify, and manage defects
    6. Reports       – Download CSV / text reports
    7. About         – Project information
"""

import logging

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import database as db
from ai_engine import ai_analyze_requirement, get_engine_status
from bug_analyzer import create_defect
from config import APP_NAME, APP_SUBTITLE, APP_VERSION, DEFECT_STATUSES
from report_generator import (
    generate_defects_csv,
    generate_full_report_csv,
    generate_summary_text,
    generate_test_cases_csv,
    generate_test_results_csv,
)
from test_executor import execute_all, execute_test_case
from test_generator import generate_test_cases
from utils import (
    SAMPLE_REQUIREMENT,
    format_datetime,
    get_priority_colour,
    get_severity_colour,
    get_status_colour,
    quality_label,
    truncate,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.WARNING)

# ---------------------------------------------------------------------------
# Page config – must be the first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Database bootstrap
# ---------------------------------------------------------------------------
db.init_db()

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ── Global body ── */
    html, body, [data-testid="stAppViewContainer"] {
        background: #0d0d1a !important;
        color: #e2e8f0;
        font-family: 'Segoe UI', system-ui, sans-serif;
    }

    /* ── Hide default Streamlit top-bar chrome ── */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important;
        border-right: 1px solid rgba(139,92,246,0.3);
    }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stRadio > label {
        font-size: 0.95rem;
        font-weight: 500;
        padding: 6px 0;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #a5b4fc !important;
    }

    /* ── Main content area ── */
    .block-container {
        padding-top: 1.5rem !important;
        max-width: 1400px;
    }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border: 1px solid rgba(139,92,246,0.4);
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 4px 20px rgba(139,92,246,0.15);
        transition: transform 0.2s;
    }
    [data-testid="metric-container"]:hover { transform: translateY(-2px); }
    [data-testid="metric-container"] label { color: #a5b4fc !important; font-size: 0.8rem; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        font-weight: 700;
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 1.05rem;
        font-weight: 700;
        color: #c4b5fd;
        border-left: 4px solid #8b5cf6;
        padding-left: 10px;
        margin: 1.2rem 0 0.6rem 0;
        letter-spacing: 0.02em;
    }

    /* ── Hero banner ── */
    .hero-banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #4c1d95 40%, #6d28d9 70%, #7c3aed 100%);
        border-radius: 18px;
        padding: 36px 40px;
        margin-bottom: 28px;
        border: 1px solid rgba(139,92,246,0.5);
        box-shadow: 0 8px 32px rgba(109,40,217,0.35);
    }
    .hero-banner h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0 0 6px 0;
        letter-spacing: -0.02em;
    }
    .hero-banner p {
        color: #c4b5fd;
        font-size: 1.05rem;
        margin: 0;
    }

    /* ── Info card ── */
    .info-card {
        background: linear-gradient(135deg, #1e1b4b, #2d2459);
        border: 1px solid rgba(139,92,246,0.4);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        color: #c4b5fd;
    }

    /* ── Chart containers ── */
    [data-testid="stPlotlyChart"] {
        background: #13111f;
        border-radius: 14px;
        padding: 8px;
        border: 1px solid rgba(139,92,246,0.2);
    }

    /* ── DataFrames ── */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        border: 1px solid rgba(139,92,246,0.25);
        overflow: hidden;
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        background: #13111f;
        border: 1px solid rgba(139,92,246,0.25) !important;
        border-radius: 10px !important;
        margin-bottom: 6px;
    }
    [data-testid="stExpander"] summary { color: #c4b5fd !important; }

    /* ── Buttons ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
        border: none !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
        box-shadow: 0 4px 14px rgba(109,40,217,0.4) !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(139,92,246,0.5) !important;
    }
    .stButton > button:not([kind="primary"]) {
        background: rgba(139,92,246,0.12) !important;
        border: 1px solid rgba(139,92,246,0.4) !important;
        color: #c4b5fd !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: rgba(139,92,246,0.25) !important;
    }

    /* ── Select boxes and inputs ── */
    [data-testid="stSelectbox"], [data-testid="stTextInput"],
    [data-testid="stTextArea"] {
        border-radius: 10px;
    }
    .stSelectbox > div > div, .stTextInput > div > div > input,
    .stTextArea > div > textarea {
        background: #1e1b4b !important;
        border: 1px solid rgba(139,92,246,0.4) !important;
        color: #e2e8f0 !important;
        border-radius: 10px !important;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] [role="tab"] {
        color: #a5b4fc !important;
        font-weight: 500;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #c4b5fd !important;
        border-bottom: 2px solid #8b5cf6 !important;
    }

    /* ── Divider ── */
    hr { border-color: rgba(139,92,246,0.25) !important; }

    /* ── Headings inside pages ── */
    h1, h2, h3, h4 { color: #e2e8f0 !important; }
    p, li, label { color: #cbd5e1; }

    /* ── Download buttons ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1e3a5f, #1e40af) !important;
        border: 1px solid rgba(59,130,246,0.5) !important;
        color: #bfdbfe !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #1e40af, #2563eb) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Spinner ── */
    [data-testid="stSpinner"] { color: #8b5cf6 !important; }

    /* ── Info / warning / success boxes ── */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        border-left: 4px solid #8b5cf6 !important;
    }

    /* ── Tag badge ── */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 1px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ===========================================================================
# Sidebar navigation
# ===========================================================================

with st.sidebar:
    st.markdown(
        f"""
        <div style="padding:16px 8px 8px 8px; text-align:center;">
            <div style="font-size:2rem;">🧪</div>
            <div style="font-size:1.3rem;font-weight:800;color:#e2e8f0;margin:4px 0 2px 0;">{APP_NAME}</div>
            <div style="font-size:0.78rem;color:#a5b4fc;">{APP_SUBTITLE}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "📋 Requirement Analysis",
            "🧪 Test Case Generator",
            "▶️ Test Execution",
            "🐛 Defect Analysis",
            "📄 Reports",
            "ℹ️ About",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    engine_status = get_engine_status()
    mode_icon = "🤖" if engine_status["ai_enabled"] else "⚙️"
    st.markdown(
        f"""
        <div style="padding:8px;background:rgba(139,92,246,0.15);border-radius:8px;
                    border:1px solid rgba(139,92,246,0.3);text-align:center;margin-bottom:6px;">
            <span style="color:#c4b5fd;font-size:0.85rem;">{mode_icon} <b>Engine:</b> {engine_status['mode']}</span>
        </div>
        <div style="text-align:center;color:#6b7280;font-size:0.75rem;">v{APP_VERSION}</div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# Helper: draw a coloured pill
# ===========================================================================

def pill(label: str, colour: str) -> str:
    return (
        f'<span style="background:{colour};color:#fff;padding:2px 10px;'
        f'border-radius:12px;font-size:0.75rem;font-weight:600;">'
        f"{label}</span>"
    )


# ===========================================================================
# PAGE 1 – Dashboard
# ===========================================================================

def page_dashboard():
    st.markdown(
        f"""
        <div class="hero-banner">
            <h1>🧪 {APP_NAME}</h1>
            <p>{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = db.get_dashboard_metrics()

    # Row 1 – requirement / test-case counts
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📋 Requirements",  metrics["total_requirements"])
    c2.metric("🧪 Test Cases",    metrics["total_test_cases"])
    c3.metric("✅ Passed",        metrics["passed"])
    c4.metric("❌ Failed",        metrics["failed"])
    c5.metric("⏸️ Blocked",       metrics["blocked"])

    # Row 2 – quality / defect counts
    c6, c7, c8, c9, c10 = st.columns(5)
    c6.metric("📈 Pass Rate",      f"{metrics['pass_rate']}%")
    c7.metric("🐛 Total Defects",  metrics["total_defects"])
    c8.metric("🔴 Critical",       metrics["critical_defects"])
    c9.metric("🟠 Major",          metrics["major_defects"])
    c10.metric("🟡 Minor",         metrics["minor_defects"])

    st.markdown("---")

    # Charts row
    results   = db.get_all_test_results()
    test_cases= db.get_all_test_cases()
    defects   = db.get_all_defects()

    col_l, col_m, col_r = st.columns(3)

    with col_l:
        st.markdown('<p class="section-header">Test Execution Status</p>',
                    unsafe_allow_html=True)
        if results:
            df_r = pd.DataFrame(results)
            counts = df_r["status"].value_counts().reset_index()
            counts.columns = ["Status", "Count"]
            colour_map = {
                "PASS":    "#16a34a",
                "FAIL":    "#dc2626",
                "BLOCKED": "#ca8a04",
            }
            fig = px.pie(
                counts, values="Count", names="Status",
                color="Status", color_discrete_map=colour_map,
                hole=0.45,
            )
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), height=280,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#c4b5fd"),
                legend=dict(font=dict(color="#c4b5fd")),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No test executions yet.")

    with col_m:
        st.markdown('<p class="section-header">Test Type Distribution</p>',
                    unsafe_allow_html=True)
        if test_cases:
            df_tc = pd.DataFrame(test_cases)
            counts = df_tc["test_type"].value_counts().reset_index()
            counts.columns = ["Type", "Count"]
            fig = px.bar(
                counts, x="Type", y="Count",
                color="Type",
                color_discrete_sequence=["#8b5cf6","#6d28d9","#a78bfa","#c4b5fd"],
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=280,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#c4b5fd"),
                xaxis=dict(gridcolor="rgba(139,92,246,0.15)", tickfont=dict(color="#a5b4fc")),
                yaxis=dict(gridcolor="rgba(139,92,246,0.15)", tickfont=dict(color="#a5b4fc")),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No test cases yet.")

    with col_r:
        st.markdown('<p class="section-header">Defect Severity</p>',
                    unsafe_allow_html=True)
        if defects:
            df_d = pd.DataFrame(defects)
            counts = df_d["severity"].value_counts().reset_index()
            counts.columns = ["Severity", "Count"]
            colour_map = {
                "Critical": "#dc2626",
                "Major":    "#ea580c",
                "Minor":    "#ca8a04",
                "Trivial":  "#16a34a",
            }
            fig = px.bar(
                counts, x="Severity", y="Count",
                color="Severity", color_discrete_map=colour_map,
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=280,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#c4b5fd"),
                xaxis=dict(gridcolor="rgba(139,92,246,0.15)", tickfont=dict(color="#a5b4fc")),
                yaxis=dict(gridcolor="rgba(139,92,246,0.15)", tickfont=dict(color="#a5b4fc")),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No defects found yet.")

    # Priority distribution
    if test_cases:
        st.markdown('<p class="section-header">Test Priority Distribution</p>',
                    unsafe_allow_html=True)
        df_tc = pd.DataFrame(test_cases)
        pri_counts = df_tc["priority"].value_counts().reset_index()
        pri_counts.columns = ["Priority", "Count"]
        colour_map = {
            "Critical": "#7c3aed",
            "High":     "#dc2626",
            "Medium":   "#ca8a04",
            "Low":      "#16a34a",
        }
        fig = px.bar(
            pri_counts, x="Priority", y="Count",
            color="Priority", color_discrete_map=colour_map,
            orientation="v",
        )
        fig.update_layout(
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=250,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c4b5fd"),
            xaxis=dict(gridcolor="rgba(139,92,246,0.15)", tickfont=dict(color="#a5b4fc")),
            yaxis=dict(gridcolor="rgba(139,92,246,0.15)", tickfont=dict(color="#a5b4fc")),
        )
        st.plotly_chart(fig, use_container_width=True)


# ===========================================================================
# PAGE 2 – Requirement Analysis
# ===========================================================================

def page_requirement_analysis():
    st.title("📋 Requirement Analysis")
    st.markdown(
        "Enter a software requirement and TestIQ will identify inputs, "
        "validation rules, edge cases, and boundary conditions."
    )
    st.markdown("---")

    # Quick-fill with sample
    if st.button("📥 Load Sample Requirement"):
        st.session_state["req_title"]    = SAMPLE_REQUIREMENT["title"]
        st.session_state["req_desc"]     = SAMPLE_REQUIREMENT["description"]
        st.session_state["req_module"]   = SAMPLE_REQUIREMENT["module"]
        st.session_state["req_acc"]      = SAMPLE_REQUIREMENT["acceptance"]

    col_l, col_r = st.columns([2, 1])

    with col_l:
        title = st.text_input(
            "Requirement Title *",
            key="req_title",
            placeholder="e.g. User Registration",
        )
        description = st.text_area(
            "Requirement Description *",
            key="req_desc",
            height=130,
            placeholder=(
                "e.g. The application should allow users to register "
                "using name, email and password."
            ),
        )

    with col_r:
        module = st.text_input(
            "Module Name",
            key="req_module",
            placeholder="e.g. Authentication",
        )
        acceptance = st.text_area(
            "Acceptance Criteria (optional)",
            key="req_acc",
            height=130,
            placeholder=(
                "- Email must be valid\n"
                "- Password at least 8 characters\n"
                "- Name cannot be empty"
            ),
        )

    st.markdown("")
    analyze_btn = st.button("🔍 Analyse Requirement", type="primary")

    if analyze_btn:
        if not title.strip() or not description.strip():
            st.error("⚠️ Requirement Title and Description are required.")
            return

        with st.spinner("Analysing requirement…"):
            analysis = ai_analyze_requirement(title, description, module, acceptance)

        # Save to DB
        req_id = db.insert_requirement(title, description, module, acceptance)
        st.session_state["last_analysis"]   = analysis
        st.session_state["last_req_id"]     = req_id
        st.session_state["last_req_title"]  = title

        st.success(f"✅ Requirement saved (ID: {req_id})")

    # Display analysis results
    if "last_analysis" in st.session_state:
        analysis = st.session_state["last_analysis"]
        _display_analysis(analysis)

    # Existing requirements table
    st.markdown("---")
    st.markdown('<p class="section-header">Saved Requirements</p>',
                unsafe_allow_html=True)
    reqs = db.get_all_requirements()
    if reqs:
        df = pd.DataFrame(reqs)[["id", "title", "module", "status", "created_at"]]
        df.columns = ["ID", "Title", "Module", "Status", "Created"]
        df["Created"] = df["Created"].apply(format_datetime)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No requirements saved yet. Analyse a requirement above.")


def _display_analysis(analysis: dict):
    st.markdown("---")
    st.markdown("### 🔎 Analysis Results")

    engine = analysis.get("engine", "rule-based")
    risk   = analysis.get("risk_level", "Low")
    risk_colour = {"High": "#dc2626", "Medium": "#ca8a04", "Low": "#16a34a"}.get(risk, "#6b7280")

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"**Module:** {analysis.get('module', 'N/A')}")
    col2.markdown(
        f"**Risk Level:** "
        + pill(risk, risk_colour),
        unsafe_allow_html=True,
    )
    col3.markdown(f"**Engine:** `{engine}`")

    # Detected fields
    fields = analysis.get("detected_fields", [])
    st.markdown(
        "**Detected Input Fields:** "
        + " ".join(
            pill(f, "#3b82f6") for f in fields
        ),
        unsafe_allow_html=True,
    )

    col_l, col_r = st.columns(2)

    with col_l:
        with st.expander("📐 Validation Rules", expanded=True):
            rules = analysis.get("validation_rules", {})
            for field, rule_list in rules.items():
                st.markdown(f"**{field}:** " + ", ".join(f"`{r}`" for r in rule_list))

        with st.expander("✅ Expected Behaviours"):
            for b in analysis.get("expected_behaviours", []):
                st.markdown(f"- {b}")

        with st.expander("🎯 Test Scope"):
            for s in analysis.get("test_scope", []):
                st.markdown(f"- {s}")

    with col_r:
        with st.expander("⚠️ Edge Cases", expanded=True):
            for ec in analysis.get("edge_cases", []):
                st.markdown(f"- {ec}")

        with st.expander("📏 Boundary Conditions"):
            for bc in analysis.get("boundary_conditions", []):
                st.markdown(f"- {bc}")

        with st.expander("🐛 Potential Defect Areas"):
            for pd_item in analysis.get("potential_defects", []):
                st.markdown(f"- {pd_item}")


# ===========================================================================
# PAGE 3 – Test Case Generator
# ===========================================================================

def page_test_generator():
    st.title("🧪 Test Case Generator")
    st.markdown(
        "Generate structured test cases from a saved requirement. "
        "Cases cover Positive, Negative, Boundary, and Validation scenarios."
    )
    st.markdown("---")

    reqs = db.get_all_requirements()
    if not reqs:
        st.warning("No requirements found. Please analyse a requirement first.")
        return

    req_options = {f"[{r['id']}] {r['title']}": r["id"] for r in reqs}
    selected_label = st.selectbox("Select Requirement", list(req_options.keys()))
    req_id = req_options[selected_label]

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("⚡ Generate Test Cases", type="primary"):
            req = db.get_requirement_by_id(req_id)
            if req:
                with st.spinner("Generating test cases…"):
                    analysis = ai_analyze_requirement(
                        req["title"], req["description"],
                        req["module"], req["acceptance"],
                    )
                    test_cases = generate_test_cases(analysis, req_id)

                # Save to DB (skip duplicates by test_id)
                existing_ids = {
                    tc["test_id"]
                    for tc in db.get_test_cases_by_requirement(req_id)
                }
                new_count = 0
                for tc in test_cases:
                    if tc["test_id"] not in existing_ids:
                        db.insert_test_case(tc)
                        new_count += 1

                st.success(
                    f"✅ Generated {len(test_cases)} test cases "
                    f"({new_count} new saved to database)."
                )

    with col2:
        # Export button (shown whenever test cases exist for this req)
        tcs = db.get_test_cases_by_requirement(req_id)
        if tcs:
            csv_bytes = generate_test_cases_csv(tcs)
            st.download_button(
                "📥 Export Test Cases (CSV)",
                data=csv_bytes,
                file_name=f"test_cases_req{req_id}.csv",
                mime="text/csv",
            )

    # Display existing test cases for selected requirement
    tcs = db.get_test_cases_by_requirement(req_id)
    if not tcs:
        st.info("No test cases yet for this requirement. Click 'Generate Test Cases'.")
        return

    st.markdown(f"**{len(tcs)} test cases** for requirement #{req_id}")

    # Type tabs
    types = ["All"] + sorted({tc["test_type"] for tc in tcs})
    tab_labels = types
    tabs = st.tabs(tab_labels)

    for tab, t in zip(tabs, tab_labels):
        with tab:
            subset = tcs if t == "All" else [tc for tc in tcs if tc["test_type"] == t]
            _render_test_case_table(subset, req_id)


def _render_test_case_table(test_cases: list, req_id: int):
    """Render test cases with expand/delete actions."""
    if not test_cases:
        st.info("No test cases in this category.")
        return

    for tc in test_cases:
        with st.expander(
            f"**{tc['test_id']}** – {truncate(tc['scenario'], 90)}", expanded=False
        ):
            c1, c2, c3 = st.columns(3)
            c1.markdown(
                f"**Type:** "
                + pill(
                    tc["test_type"],
                    {"Positive": "#16a34a", "Negative": "#dc2626",
                     "Boundary": "#7c3aed", "Validation": "#2563eb"}.get(
                        tc["test_type"], "#6b7280"
                    ),
                ),
                unsafe_allow_html=True,
            )
            c2.markdown(
                f"**Priority:** " + pill(tc["priority"], get_priority_colour(tc["priority"])),
                unsafe_allow_html=True,
            )
            c3.markdown(
                f"**Status:** " + pill(tc["status"], get_status_colour(tc["status"])),
                unsafe_allow_html=True,
            )

            st.markdown(f"**Scenario:** {tc['scenario']}")
            st.markdown(f"**Preconditions:** {tc.get('preconditions', 'None')}")
            st.markdown(f"**Test Data:** `{tc.get('test_data', 'N/A')}`")
            st.markdown(f"**Expected Result:** {tc['expected_result']}")

            if st.button(f"🗑️ Delete {tc['test_id']}", key=f"del_{tc['test_id']}"):
                db.delete_test_case(tc["test_id"])
                st.rerun()


# ===========================================================================
# PAGE 4 – Test Execution
# ===========================================================================

def page_test_execution():
    st.title("▶️ Test Execution Engine")
    st.markdown(
        "Execute test cases against the validation engine. "
        "PASS / FAIL is determined by real validation logic — not hard-coded."
    )
    st.markdown("---")

    all_tcs = db.get_all_test_cases()
    if not all_tcs:
        st.warning("No test cases found. Generate test cases first.")
        return

    # Summary before run
    reqs = db.get_all_requirements()
    req_options = {"All Requirements": None}
    req_options.update({f"[{r['id']}] {r['title']}": r["id"] for r in reqs})
    selected_label = st.selectbox("Filter by Requirement", list(req_options.keys()))
    filter_req_id = req_options[selected_label]

    if filter_req_id:
        run_tcs = db.get_test_cases_by_requirement(filter_req_id)
    else:
        run_tcs = all_tcs

    st.markdown(f"**{len(run_tcs)} test cases** selected for execution.")

    col1, col2 = st.columns([1, 3])

    with col1:
        run_all = st.button("🚀 Run All Tests", type="primary")

    # Individual test selection
    tc_options = {f"{tc['test_id']} – {truncate(tc['scenario'], 60)}": tc for tc in run_tcs}
    selected_tc_label = st.selectbox("Or select a single test to run:", list(tc_options.keys()))

    with col2:
        run_one = st.button("▶️ Run Selected Test")

    results_to_show = []

    if run_all:
        with st.spinner(f"Executing {len(run_tcs)} test cases…"):
            results = execute_all(run_tcs)
            _persist_results(results, run_tcs)
            results_to_show = results
        st.success(f"Execution complete. {len(results)} results saved.")

    elif run_one and selected_tc_label:
        tc = tc_options[selected_tc_label]
        with st.spinner(f"Executing {tc['test_id']}…"):
            result = execute_test_case(tc)
            _persist_results([result], [tc])
            results_to_show = [result]
        status = result["status"]
        colour = get_status_colour(status)
        st.markdown(
            f"Result: " + pill(status, colour) + f"  —  {result['actual_result']}",
            unsafe_allow_html=True,
        )

    # Always show recent results
    st.markdown("---")
    st.markdown('<p class="section-header">Execution Results</p>',
                unsafe_allow_html=True)

    all_results = db.get_all_test_results()
    if filter_req_id:
        req_tc_ids = {tc["test_id"] for tc in run_tcs}
        all_results = [r for r in all_results if r["test_id"] in req_tc_ids]

    if all_results:
        _render_results_table(all_results)
    else:
        st.info("No execution results yet. Run the tests above.")


def _persist_results(results: list, test_cases: list):
    """Save execution results to DB and create defects for failures."""
    tc_map = {tc["test_id"]: tc for tc in test_cases}
    for result in results:
        db.insert_test_result(result)
        db.update_test_case_status(result["test_id"], result["status"])
        if result["status"] in ("FAIL", "BLOCKED"):
            tc = tc_map.get(result["test_id"])
            defect = create_defect(result, tc)
            if defect:
                try:
                    db.insert_defect(defect)
                except Exception:
                    pass  # duplicate defect_id – already logged


def _render_results_table(results: list):
    rows = []
    for r in results:
        rows.append({
            "Test ID":        r["test_id"],
            "Status":         r["status"],
            "Expected":       truncate(r["expected_result"], 60),
            "Actual":         truncate(r["actual_result"], 60),
            "Exec Time (s)":  f"{r.get('execution_time', 0):.4f}",
            "Executed At":    format_datetime(r.get("executed_at", "")),
        })
    df = pd.DataFrame(rows)

    # Colour the Status column with styler
    def colour_status(val):
        c = get_status_colour(val)
        return f"color: {c}; font-weight: bold;"

    styled = df.style.applymap(colour_status, subset=["Status"])
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ===========================================================================
# PAGE 5 – Defect Analysis
# ===========================================================================

def page_defect_analysis():
    st.title("🐛 Defect Analysis")
    st.markdown(
        "Defects are automatically created when a test fails. "
        "Severity and priority are classified by rule-based logic."
    )
    st.markdown("---")

    defects = db.get_all_defects()
    if not defects:
        st.info("No defects found. Run test cases to generate defects automatically.")
        return

    # Summary metrics
    total    = len(defects)
    critical = sum(1 for d in defects if d["severity"] == "Critical")
    major    = sum(1 for d in defects if d["severity"] == "Major")
    minor    = sum(1 for d in defects if d["severity"] == "Minor")
    trivial  = sum(1 for d in defects if d["severity"] == "Trivial")
    open_d   = sum(1 for d in defects if d["status"] == "Open")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total",    total)
    c2.metric("🔴 Critical", critical)
    c3.metric("🟠 Major",    major)
    c4.metric("🟡 Minor",    minor)
    c5.metric("⚪ Trivial",   trivial)
    c6.metric("🔓 Open",    open_d)

    st.markdown("---")

    # Severity filter
    sev_filter = st.selectbox(
        "Filter by Severity",
        ["All", "Critical", "Major", "Minor", "Trivial"],
    )
    filtered = defects if sev_filter == "All" else [
        d for d in defects if d["severity"] == sev_filter
    ]

    for defect in filtered:
        sev_colour = get_severity_colour(defect["severity"])
        status_colour = get_status_colour(defect["status"])
        with st.expander(
            f"**{defect['defect_id']}** – {truncate(defect['title'], 80)}",
            expanded=False,
        ):
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(
                f"**Severity:** " + pill(defect["severity"], sev_colour),
                unsafe_allow_html=True,
            )
            col2.markdown(
                f"**Priority:** " + pill(defect["priority"], get_priority_colour(defect["priority"])),
                unsafe_allow_html=True,
            )
            col3.markdown(
                f"**Status:** " + pill(defect["status"], status_colour),
                unsafe_allow_html=True,
            )
            col4.markdown(f"**Test ID:** `{defect['test_id']}`")

            st.markdown(f"**Description:** {defect['description']}")
            st.markdown(f"**Expected:** {defect['expected_result']}")
            st.markdown(f"**Actual:** {defect['actual_result']}")
            st.markdown(f"**Created:** {format_datetime(defect.get('created_at', ''))}")

            # Status update
            new_status = st.selectbox(
                "Update Status",
                DEFECT_STATUSES,
                index=DEFECT_STATUSES.index(defect["status"]),
                key=f"status_{defect['defect_id']}",
            )
            if st.button("💾 Save Status", key=f"save_{defect['defect_id']}"):
                db.update_defect_status(defect["defect_id"], new_status)
                st.success("Status updated.")
                st.rerun()


# ===========================================================================
# PAGE 6 – Reports
# ===========================================================================

def page_reports():
    st.title("📄 Reports")
    st.markdown("Download test data, results, and defects as CSV or text reports.")
    st.markdown("---")

    metrics    = db.get_dashboard_metrics()
    test_cases = db.get_all_test_cases()
    results    = db.get_all_test_results()
    defects    = db.get_all_defects()
    reqs       = db.get_all_requirements()

    # Summary card
    pass_rate = metrics["pass_rate"]
    st.markdown(
        f"""
        <div class="info-card">
        <b>Project:</b> {APP_NAME} &nbsp;|&nbsp;
        <b>Requirements:</b> {metrics['total_requirements']} &nbsp;|&nbsp;
        <b>Test Cases:</b> {metrics['total_test_cases']} &nbsp;|&nbsp;
        <b>Pass Rate:</b> {pass_rate}% &nbsp;|&nbsp;
        <b>Total Defects:</b> {metrics['total_defects']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📦 Individual Reports")

        if test_cases:
            st.download_button(
                "📥 Download Test Cases CSV",
                data=generate_test_cases_csv(test_cases),
                file_name="testiq_test_cases.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button("📥 Download Test Cases CSV", disabled=True, use_container_width=True)

        if results:
            st.download_button(
                "📥 Download Test Results CSV",
                data=generate_test_results_csv(results),
                file_name="testiq_test_results.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button("📥 Download Test Results CSV", disabled=True, use_container_width=True)

        if defects:
            st.download_button(
                "📥 Download Defects CSV",
                data=generate_defects_csv(defects),
                file_name="testiq_defects.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button("📥 Download Defects CSV", disabled=True, use_container_width=True)

    with col2:
        st.markdown("#### 📋 Complete Reports")

        summary_bytes = generate_summary_text(metrics)
        st.download_button(
            "📥 Download Testing Summary (TXT)",
            data=summary_bytes,
            file_name="testiq_summary.txt",
            mime="text/plain",
            use_container_width=True,
        )

        if test_cases or results or defects:
            full_csv = generate_full_report_csv(reqs, test_cases, results, defects, metrics)
            st.download_button(
                "📥 Download Full Report (CSV)",
                data=full_csv,
                file_name="testiq_full_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # Data preview
    st.markdown("---")
    st.markdown('<p class="section-header">Data Preview</p>', unsafe_allow_html=True)
    preview_tabs = st.tabs(["Requirements", "Test Cases", "Results", "Defects"])

    with preview_tabs[0]:
        if reqs:
            st.dataframe(pd.DataFrame(reqs), use_container_width=True, hide_index=True)
        else:
            st.info("No requirements.")

    with preview_tabs[1]:
        if test_cases:
            st.dataframe(pd.DataFrame(test_cases), use_container_width=True, hide_index=True)
        else:
            st.info("No test cases.")

    with preview_tabs[2]:
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        else:
            st.info("No test results.")

    with preview_tabs[3]:
        if defects:
            st.dataframe(pd.DataFrame(defects), use_container_width=True, hide_index=True)
        else:
            st.info("No defects.")


# ===========================================================================
# PAGE 7 – About
# ===========================================================================

def page_about():
    st.title(f"ℹ️ About {APP_NAME}")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            f"""
### {APP_NAME} – {APP_SUBTITLE}

**TestIQ** is a portfolio project that demonstrates core skills required for an
**Associate Software Test Engineer / Intelligent Automation** role.

#### What TestIQ Does

Given a natural-language software requirement, TestIQ automatically:

1. **Analyses** the requirement to extract fields, rules, and risks
2. **Generates** structured test cases (Positive / Negative / Boundary / Validation)
3. **Executes** tests using a real Python validation engine
4. **Classifies** failures as defects with severity and priority
5. **Visualises** results on an interactive dashboard
6. **Exports** reports as CSV or text files

#### Why This Demonstrates QA Skills

| Skill | How Demonstrated |
|---|---|
| Test-case design | Structured positive/negative/boundary/validation generation |
| Boundary Value Analysis | Automated boundary test generation |
| Defect analysis | Rule-based defect classification engine |
| Automation | Python-driven test execution without manual steps |
| Validation logic | Real validators (email, password, name, range) |
| Database | SQLite with CRUD operations and parameterised queries |
| Reporting | CSV export and text summary reports |
| AI-Assisted Testing | Optional LLM enhancement via OpenAI/Gemini |

#### System Architecture

```
User → Streamlit UI → Requirement Analyzer → AI / Rule-Based Engine
                     ↓
               Test Case Generator
                     ↓
             Test Execution Engine
                     ↓
             Validation Engine (validators.py)
                     ↓
               Defect Analyzer
                     ↓
               SQLite Database
                     ↓
         Dashboard & Report Generator
```

#### AI Integration

TestIQ works **fully offline** using its deterministic rule-based engine.
Set `OPENAI_API_KEY` or `GEMINI_API_KEY` in a `.env` file to enable
AI-enhanced analysis.
            """
        )

    with col2:
        st.markdown("#### Technology Stack")
        stack = {
            "Python": "3.12+",
            "Streamlit": "UI Framework",
            "SQLite": "Database",
            "Pandas": "Data Handling",
            "Plotly": "Charts",
            "python-dotenv": "Config",
        }
        for tech, role in stack.items():
            st.markdown(f"- **{tech}** – {role}")

        st.markdown("---")
        st.markdown("#### Version")
        st.code(f"TestIQ v{APP_VERSION}")

        st.markdown("#### Running Tests")
        st.code("pytest tests/ -v", language="bash")


# ===========================================================================
# Router
# ===========================================================================

page_map = {
    "📊 Dashboard":           page_dashboard,
    "📋 Requirement Analysis": page_requirement_analysis,
    "🧪 Test Case Generator":  page_test_generator,
    "▶️ Test Execution":       page_test_execution,
    "🐛 Defect Analysis":      page_defect_analysis,
    "📄 Reports":              page_reports,
    "ℹ️ About":                page_about,
}

page_map[page]()
