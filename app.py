"""Career Saathi Streamlit wizard with cinematic dashboards and always-on chat."""
from __future__ import annotations

from typing import Dict, List

import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_tags import st_tags

from agent_engine import AgentEngine, CareerRequest
from visuals import (
    plot_growth_line,
    plot_industry_pie,
    plot_radar_chart,
    plot_salary_bars,
)

st.set_page_config(page_title="Career Saathi", page_icon="💼", layout="wide")

# Streamlit keeps track of the latest multi-agent dossier so every rerun reuses Gemini outputs
# instead of re-hitting Google ADK unless the user changes their persona inputs.
if "analysis" not in st.session_state:
    st.session_state["analysis"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {
            "role": "assistant",
            "content": (
                "Hey! I'm Saathi. Complete Step 1 to activate my multi-agent brain, then ask me anything—"
                "salary, learning strategy, day-to-day life, interview playbooks."
            ),
        }
    ]

# Single root orchestrator that fans out to RoleAnalyst / MarketResearcher / CurriculumArchitect / InsightCoach.
ENGINE = AgentEngine()

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root {
    --glass-bg: rgba(255, 255, 255, 0.09);
    --glass-border: rgba(255, 255, 255, 0.18);
    --accent: #7f5af0;
    --accent-2: #00c6ff;
    --text-primary: #f5f7ff;
    --text-muted: #a0abc4;
}
html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 15% 20%, #24243e 0%, #0f0c29 30%, #000000 85%);
    color: var(--text-primary);
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] {background: transparent;}
section.main > div:has(.block-container) {
    padding-top: 1.5rem;
}
.block-container {
    padding-top: 1rem;
    max-width: 1500px;
    margin-inline: auto;
}
.section-heading {
    text-align: center;
    font-size: 1.6rem;
    letter-spacing: 0.07em;
    color: var(--text-muted);
    margin-bottom: 1rem;
}
.hero {
    padding: 3rem;
    border-radius: 36px;
    background: linear-gradient(130deg, rgba(0,198,255,0.18), rgba(127,90,240,0.24));
    border: 1px solid rgba(255,255,255,0.2);
    box-shadow: 0 30px 90px rgba(0,0,0,0.55);
}
.hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr);
    gap: 2.5rem;
    align-items: center;
}
.hero h1 {
    font-size: 3.4rem;
    margin-bottom: 1rem;
}
.hero h1 span {
    color: var(--accent-2);
    font-weight: 500;
}
.hero-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 0.5rem;
}
.hero-orbit {
    position: relative;
    height: 220px;
    border-radius: 999px;
    border: 1px dashed rgba(255,255,255,0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    overflow: hidden;
}
.hero-orbit::after,
.hero-orbit::before {
    content: '';
    position: absolute;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: rgba(127,90,240,0.25);
    filter: blur(30px);
    animation: drift 9s ease-in-out infinite;
}
.hero-orbit::before {
    background: rgba(0,198,255,0.3);
    animation-delay: -3s;
}
.hero-badge {
    position: relative;
    z-index: 1;
    text-align: center;
    font-size: 1.05rem;
    line-height: 1.6;
}
.card, .dashboard-card, .timeline-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 28px;
    padding: 2rem;
    box-shadow: 0 25px 80px rgba(0,0,0,0.45);
    backdrop-filter: blur(18px);
    margin-bottom: 1.2rem;
}
.timeline-card {
    border-left: 4px solid var(--accent);
    animation: floatIn 0.8s ease both;
}
.resources-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
}
.resource-card {
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.15);
    padding: 1rem;
    background: rgba(0,0,0,0.3);
    min-height: 150px;
}
.resource-card a {color: var(--accent-2); text-decoration: none; font-weight: 600;}
[data-testid="stSidebar"] > div {
    background: rgba(10,12,16,0.92);
    border-right: 1px solid rgba(255,255,255,0.08);
    padding: 1rem;
}
.chat-bubble {
    border-radius: 18px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.7rem;
    font-size: 0.95rem;
}
.chat-bubble.assistant {
    background: rgba(127,90,240,0.18);
    border: 1px solid rgba(127,90,240,0.4);
}
.chat-bubble.user {
    background: rgba(0,198,255,0.18);
    border: 1px solid rgba(0,198,255,0.4);
}
.timeline-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--accent-2);
    margin-right: 0.6rem;
    animation: pulse 2.5s infinite;
}
.highlight-text {
    display: inline-block;
    background: rgba(255,255,255,0.05);
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.12);
    margin: 0.2rem;
}
.form-shell {
    background: rgba(0,0,0,0.2);
    border-radius: 32px;
    border: 1px solid rgba(255,255,255,0.08);
    padding: 2.5rem;
    margin-bottom: 2.2rem;
    box-shadow: 0 30px 80px rgba(0,0,0,0.55);
}
.form-panel {
    background: rgba(10,11,18,0.65);
    border-radius: 28px;
    border: 1px solid rgba(255,255,255,0.08);
    padding: 1.5rem;
}
.animated-panel {
    position: relative;
    border-radius: 28px;
    border: 1px solid rgba(255,255,255,0.08);
    background: linear-gradient(160deg, rgba(127,90,240,0.3), rgba(0,198,255,0.2));
    min-height: 430px;
    padding: 2rem;
    overflow: hidden;
}
.animated-panel::after,
.animated-panel::before {
    content: '';
    position: absolute;
    width: 180px;
    height: 180px;
    border-radius: 50%;
    background: rgba(255,255,255,0.2);
    filter: blur(35px);
    animation: drift 12s linear infinite;
}
.animated-panel::before {
    width: 120px;
    height: 120px;
    right: 18%;
    top: 14%;
    background: rgba(0,0,0,0.25);
}
.panel-points {
    list-style: none;
    padding-left: 0;
    margin-top: 1.5rem;
}
.panel-points li {
    margin-bottom: 0.9rem;
    padding-left: 1.4rem;
    position: relative;
}
.panel-points li::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0.5rem;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent-2);
    box-shadow: 0 0 12px rgba(0,198,255,0.6);
}
.orb {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    border: 1px solid rgba(255,255,255,0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-primary);
    font-weight: 600;
    animation: pulse 3s ease-in-out infinite;
}
.orb + .orb {margin-top: 1rem;}
.orb.light {background: rgba(255,255,255,0.05);}
.orb.accent {background: rgba(127,90,240,0.2);}
@keyframes pulse {
    0% {transform: scale(0.9); opacity: 0.6;}
    50% {transform: scale(1.1); opacity: 1;}
    100% {transform: scale(0.9); opacity: 0.6;}
}
@keyframes drift {
    0% {transform: translate(-20%, -10%) scale(0.9);}
    50% {transform: translate(12%, 18%) scale(1.05);}
    100% {transform: translate(-20%, -10%) scale(0.9);}
}
@keyframes floatIn {
    0% {transform: translateY(20px); opacity: 0;}
    100% {transform: translateY(0); opacity: 1;}
}
.option-menu .nav-link {
    border-radius: 999px !important;
    margin: 0.3rem 0.4rem !important;
    font-weight: 600 !important;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


def _skill_profile() -> Dict[str, int]:
    col1, col2 = st.columns(2)
    with col1:
        tech = st.slider("Technical Strategy", 0, 100, 78)
        analysis = st.slider("Analytical Sense", 0, 100, 72)
    with col2:
        innovation = st.slider("Innovation Delivery", 0, 100, 68)
        communication = st.slider("Communication Leadership", 0, 100, 82)
    return {
        "Technical Strategy": tech,
        "Analytical Sense": analysis,
        "Innovation Delivery": innovation,
        "Communication Leadership": communication,
    }

def render_chat_tab(analysis: Dict[str, object] | None) -> None:
    # Gemini/ADK infused chat surface now lives in the dashboard so it reads the same context as other tabs.
    st.markdown(
        "<div class='dashboard-card'><h3>🤖 Saathi AI Mentor</h3>"
        "<p>Use natural questions—ask about fresher salary bands, interview playbooks, or upskilling bets.</p></div>",
        unsafe_allow_html=True,
    )
    chat_box = st.container()
    for message in st.session_state["chat_history"]:
        role_class = "assistant" if message["role"] == "assistant" else "user"
        chat_box.markdown(
            f"<div class='chat-bubble {role_class}'>" + message["content"].replace("\n", "<br>") + "</div>",
            unsafe_allow_html=True,
        )
    with st.form("chat_form_dashboard"):
        prompt = st.text_area(
            "Ask role, salary, or strategy questions",
            disabled=analysis is None,
            placeholder="e.g., What's the fresher salary for AI engineers in Bengaluru?",
            height=140,
        )
        submitted = st.form_submit_button(
            "Send",
            use_container_width=True,
            disabled=analysis is None,
        )
    if submitted and prompt:
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        reply = ENGINE.answer_question(prompt, analysis)
        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        st.rerun()


def render_resources(resources: List[Dict[str, str]]) -> None:
    st.markdown("#### Fresh Research Links")
    st.markdown(
        "<div class='resources-grid'>"
        + "".join(
            [
                (
                    "<div class='resource-card'>"
                    f"<a href='{resource['link']}' target='_blank'>{resource['title']}</a>"
                    f"<p>{resource['snippet']}</p>"
                    "</div>"
                )
                for resource in resources
            ]
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def render_overview_tab(overview: Dict[str, List[str]], resources: List[Dict[str, str]]) -> None:
    st.markdown(
        "<div class='dashboard-card'><h3>Role Symphony</h3><p>"
        + "<br><br>".join(overview["role_summary"])
        + "</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown("#### Key Responsibilities (10)")
    st.markdown(
        "<div class='dashboard-card'><ul>"
        + "".join([f"<li>{item}</li>" for item in overview["key_responsibilities"]])
        + "</ul></div>",
        unsafe_allow_html=True,
    )
    st.markdown("#### Tech Stack Spotlight")
    st.markdown(
        "<div class='dashboard-card'><ul>"
        + "".join([f"<li><strong>{tool['tool']}</strong> — {tool['description']}</li>" for tool in overview["tech_stack"]])
        + "</ul></div>",
        unsafe_allow_html=True,
    )
    render_resources(resources)


def render_market_tab(market: Dict[str, Dict[str, List[float]]]) -> None:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(
            plot_growth_line(market["growth_data"]["years"], market["growth_data"]["values"]),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            plot_industry_pie(market["industry_dist"]["labels"], market["industry_dist"]["values"]),
            use_container_width=True,
        )
    st.plotly_chart(
        plot_salary_bars(market["salary_data"]["levels"], market["salary_data"]["values"]),
        use_container_width=True,
    )
    st.markdown(
        "<div class='dashboard-card'><h4>Market Narrative</h4><p>"
        + "<br><br>".join(market["narrative"])
        + "</p><h4>Compensation Notes</h4><p>"
        + "<br><br>".join(market["salary_data"]["narrative"])
        + "</p></div>",
        unsafe_allow_html=True,
    )


def render_learning_tab(roadmap: Dict[str, Dict[str, List[str]]]) -> None:
    st.markdown(
        "<div class='dashboard-card'><h3>Learning Arc</h3><p>"
        + "<br><br>".join(roadmap["learning_intro"])
        + "</p></div>",
        unsafe_allow_html=True,
    )
    for stage, bullets in roadmap["timeline"].items():
        st.markdown(
            f"<div class='timeline-card'><div style='display:flex;align-items:center;margin-bottom:0.6rem;'>"
            "<div class='timeline-dot'></div>"
            f"<h4 style='margin:0;'>{stage}</h4></div><ul>"
            + "".join([f"<li>{line}</li>" for line in bullets])
            + "</ul></div>",
            unsafe_allow_html=True,
        )
    st.markdown("#### Immersive Courses")
    course_cols = st.columns(3)
    for idx, course in enumerate(roadmap["courses"]):
        with course_cols[idx % 3]:
            st.markdown(
                "<div class='card' style='min-height:200px;'>"
                f"<span class='highlight-text'>{course['provider']}</span>"
                f"<h4 style='margin-top:0.6rem;'><a href='{course['link']}' target='_blank'>{course['title']}</a></h4>"
                "<p>Bookmark-worthy module blending projects + mentorship.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
    milestone_cols = st.columns(2)
    for idx, milestone in enumerate(roadmap["milestones"]):
        with milestone_cols[idx % 2]:
            st.markdown(
                "<div class='card' style='min-height:160px;'>"
                f"<h4>{milestone['stage']}</h4>"
                f"<p>{milestone['focus']}</p>"
                f"<span class='highlight-text'>Confidence: {milestone['confidence']}%</span>"
                "</div>",
                unsafe_allow_html=True,
            )


def render_insights_tab(insights: Dict[str, List[str]], skill_matrix: Dict[str, Dict[str, int]]) -> None:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(
            "<div class='dashboard-card'><h4>Culture · Day in the Life</h4><p>"
            + "<br><br>".join(insights["culture"])
            + "</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='dashboard-card'><h4>Work-Life Systems</h4><ul>"
            + "".join([f"<li>{tip}</li>" for tip in insights["work_life"]])
            + "</ul></div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Success Stories")
        st.markdown(
            "<div class='dashboard-card'><ul>"
            + "".join(
                [
                    f"<li><a href='{story['link']}' target='_blank'>{story['name']}</a> — {story['role']}</li>"
                    for story in insights["success_stories"]
                ]
            )
            + "</ul></div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.plotly_chart(
            plot_radar_chart(skill_matrix["user"], skill_matrix["required"]),
            use_container_width=True,
        )
        st.markdown(
            "<div class='dashboard-card'><h4>Spotlights</h4><p>"
            + "<br>".join(insights["spotlights"])
            + "</p></div>",
            unsafe_allow_html=True,
        )


st.markdown(
    "<div class='hero hero-grid'>"
    "<div>"
    "<h1>Career Saathi <span>· 8th Wonder Edition</span></h1>"
    "<div class='hero-meta'>"
    "<span class='highlight-text'>Wizard Workflow</span>"
    "<span class='highlight-text'>Plotly Dashboards</span>"
    "<span class='highlight-text'>Live AI Chat</span>"
    "</div>"
    "</div>"
    "<div class='hero-orbit'>"
    "<div class='hero-badge'>Always-on multi-agent intelligence<br>crafted for cinematic clarity.</div>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

# Step 1 captures every signal required by the agents (role, industry, timeline, skills) before invoking Google ADK.
st.markdown("<div class='section-heading'>STEP 1 · DISCOVER CAREER OPTIONS</div>", unsafe_allow_html=True)
with st.container():
    st.markdown("<div class='form-shell'>", unsafe_allow_html=True)
    with st.form("profile_form"):
        col_form, col_motion = st.columns([3, 2], gap="large")
        with col_form:
            st.markdown("<div class='form-panel'>", unsafe_allow_html=True)
            persona = st.text_input("Persona Name", value="Aditi Sharma")
            target_role = st.text_input("Target Role", value="AI Engineer")
            target_industry = st.text_input("Target Industry", value="FinTech")
            target_domain = st.text_input("Target Domain / Vertical", value="Payments")
            education_level = st.selectbox(
                "Current Education",
                ["10th Grade", "12th Grade", "B.Tech", "Degree", "Working Professional"],
            )
            graduation_year = st.text_input("Graduation / Transition Year", value="2027")
            experience_level = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Professional"], index=1)
            location_preference = st.text_input("Location Preference", value="Bengaluru / Remote")
            career_doubts = st.text_area(
                "Top Career Doubt",
                value="How do I stand out when everyone flaunts AI projects?",
                help="Saathi agents will weave this concern into their plan.",
            )
            key_skills = st_tags(
                label="Key Skills",
                text="Press enter to add",
                value=["Python", "Robotics"],
                suggestions=["AI", "Cloud", "Robotics", "Storytelling", "DevOps", "Leadership"],
            )
            st.markdown("<hr style='opacity:0.2;'>", unsafe_allow_html=True)
            st.caption("Self-audit for the radar")
            skill_profile = _skill_profile()
            st.markdown("</div>", unsafe_allow_html=True)
        with col_motion:
            st.markdown(
                "<div class='animated-panel'>"
                "<span class='highlight-text'>Discover Mode</span>"
                "<h3>Career Pulse Visual</h3>"
                "<p>Saathi syncs your ambitions, location vibes, and doubts to choreograph a two-year runway.</p>"
                "<div class='orb accent'>Plan</div>"
                "<div class='orb light'>Narrate</div>"
                "<div class='orb'>Measure</div>"
                "<ul class='panel-points'>"
                "<li>Real-time prompt routing across Role, Market, and Curriculum agents.</li>"
                "<li>Story-driven insights tuned to your graduation and experience horizon.</li>"
                "<li>Visual trackers fuel radar benchmarks + milestone heatmaps.</li>"
                "</ul>"
                "</div>",
                unsafe_allow_html=True,
            )
        submitted = st.form_submit_button("Launch Analysis", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    clean_skills = [skill.strip() for skill in key_skills if skill.strip()]
    required_fields = [target_role, target_industry, target_domain]
    if any(not field.strip() for field in required_fields):
        st.warning("Please fill target role, industry, and domain to continue.")
    else:
        request = CareerRequest(
            target_role=target_role.strip(),
            target_industry=target_industry.strip(),
            target_domain=target_domain.strip(),
            education_level=education_level,
            graduation_year=graduation_year.strip() or "Soon",
            experience_level=experience_level,
            location_preference=location_preference.strip(),
            key_skills=clean_skills,
            career_doubts=career_doubts.strip(),
            skill_profile=skill_profile,
            persona_name=persona.strip() or "Trailblazer",
        )
        with st.spinner("Orchestrating Role Analyst, Market Researcher, Curriculum Architect, and Insight Coach..."):
            analysis = ENGINE.run_research(request)
        st.session_state["analysis"] = analysis
        st.toast("Saathi dossier refreshed!", icon="✨")

analysis = st.session_state.get("analysis")

# Step 2 renders the multi-agent dossier (Overview, Market, Learning Path, Insights, Chat) using cached Gemini results.
st.markdown("<div class='section-heading'>STEP 2 · ANALYSIS DASHBOARD</div>", unsafe_allow_html=True)
if not analysis:
    st.info("Complete Step 1 to unlock interactive dashboards, salary charts, and insights.")
else:
    selected = option_menu(
        None,
        ["Overview", "Market", "Learning Path", "Insights", "Chat"],
        icons=["compass", "bar-chart", "map", "sun", "chat"],
        orientation="horizontal",
        default_index=0,
        styles={
            "container": {"padding": "0!important"},
            "nav-link": {"font-size": "1rem", "color": "#d7dcf5"},
            "nav-link-selected": {"background-color": "#7f5af0", "color": "#ffffff"},
        },
    )
    if selected == "Overview":
        render_overview_tab(analysis["overview"], analysis["resources"])
    elif selected == "Market":
        render_market_tab(analysis["market"])
    elif selected == "Learning Path":
        render_learning_tab(analysis["roadmap"])
    elif selected == "Insights":
        render_insights_tab(analysis["insights"], analysis["skill_matrix"])
    elif selected == "Chat":
        render_chat_tab(analysis)
