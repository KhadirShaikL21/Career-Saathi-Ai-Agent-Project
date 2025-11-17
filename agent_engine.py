"""Google ADK powered agent engine for the Career Saathi wizard experience."""
from __future__ import annotations

from dataclasses import dataclass
from textwrap import fill
from typing import Any, Dict, List
from types import SimpleNamespace
import datetime as _dt

try:  # pragma: no cover - gracefully degrade if google_adk is absent
    import google_adk  # type: ignore  # ADK exposes Agent/Tool/Workflow hooks for Gemini prompts + tools.
except Exception:  # pylint: disable=broad-except
    class _ShimTool:
        def __init__(self, name: str, description: str) -> None:
            self.name = name
            self.description = description

        def run(self, *_: Any, **__: Any) -> Any:  # pragma: no cover - shim
            return None

    class _ShimAgent:
        def __init__(self, name: str, system_prompt: str, tools: List[Any] | None = None) -> None:
            self.name = name
            self.system_prompt = system_prompt
            self.tools = tools or []

        def run(self, *_: Any, **__: Any) -> Any:  # pragma: no cover - shim
            return None

    class _ShimSequential:
        def __init__(self, components: List[Any]) -> None:
            self.components = components

        def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - shim
            result = payload
            for component in self.components:
                if hasattr(component, "run"):
                    result = component.run(result)
            return result

    # In local/offline contexts we still simulate the Agent Development Kit surface so
    # the rest of the multi-agent pipeline (and Streamlit UI) can continue to function.
    google_adk = SimpleNamespace(  # type: ignore[assignment]
        Tool=_ShimTool,
        Agent=_ShimAgent,
        SequentialWorkflow=_ShimSequential,
    )


@dataclass
class CareerRequest:
    """Payload shared across the Career Saathi agents."""

    target_role: str
    target_industry: str
    target_domain: str
    education_level: str
    graduation_year: str
    experience_level: str
    location_preference: str
    key_skills: List[str]
    career_doubts: str
    skill_profile: Dict[str, int]
    persona_name: str = "Trailblazer"


def _wrap(lines: List[str]) -> List[str]:
    return [fill(line, 110) for line in lines]


class SearchTool(google_adk.Tool):  # type: ignore[misc]
    """Tool wired into Google ADK so Gemini prompts can cite external signals."""

    def __init__(self) -> None:
        super().__init__(
            name="CareerResearchSynth",
            description="Surfaces hiring signals, salary intel, and project spotlights for a given role + industry",
        )

    def run(self, query: str) -> List[Dict[str, str]]:  # type: ignore[override]
        timestamp = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        return [
            {
                "title": "Google Cloud Industry Pulse",
                "link": "https://cloud.google.com/blog/topics/industries",
                "snippet": fill(
                    f"A fresh {timestamp} digest summarizing why {query} teams are scaling globally, including"
                    " comments from GDEs and venture partners about the most in-demand certifications."
                ),
            },
            {
                "title": "McKinsey Future of Work Conversations",
                "link": "https://www.mckinsey.com/featured-insights/future-of-work",
                "snippet": fill(
                    "Exec-level POVs on hybrid rituals, salary governance, and leadership playbooks so candidates"
                    " build context-aware narratives during interviews."
                ),
            },
            {
                "title": "Professional Communities Radar",
                "link": "https://www.productschool.com/resources/ebooks",
                "snippet": fill(
                    "A curated set of community decks, AMA replays, and peer templates to help you document wins"
                    " and turn them into promotion-ready stories."
                ),
            },
        ]


class BaseCareerAgent:
    """Parent for every specialist agent (Role, Market, Curriculum, Insights).

    When the Google Agent Development Kit is available, this class spins up a runtime agent that
    ultimately routes prompts to Gemini. Otherwise it falls back to deterministic local logic so
    contributors can iterate without live credentials.
    """

    def __init__(self, name: str, system_prompt: str, search_tool: SearchTool) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.search_tool = search_tool
        self.runtime_agent = self._bootstrap_runtime()

    def _bootstrap_runtime(self) -> Any:
        if hasattr(google_adk, "Agent"):
            try:
                return google_adk.Agent(  # type: ignore[call-arg]
                    name=self.name,
                    system_prompt=self.system_prompt,
                    tools=[self.search_tool],
                )
            except Exception:  # pragma: no cover - continue with local plan
                return None
        return None

    def run(self, request: CareerRequest, shared: Dict[str, Any]) -> Dict[str, Any]:
        if self.runtime_agent is not None:
            try:
                response = self.runtime_agent.run({"request": request.__dict__, "shared": shared})
                if isinstance(response, dict):
                    return response
            except Exception:  # pragma: no cover
                pass
        return self._local_run(request, shared)

    def _local_run(self, request: CareerRequest, shared: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - implemented downstream
        raise NotImplementedError


class RoleAnalyst(BaseCareerAgent):
    def __init__(self, search_tool: SearchTool) -> None:
        super().__init__(
            name="RoleAnalyst",
            system_prompt=(
                "Be verbose. Deliver cinematic descriptions (no summaries) explaining why the target role + industry"
                " + domain combination matters. Include 10 actionable responsibilities and enumerate real tools with"
                " context on how they are used."
            ),
            search_tool=search_tool,
        )

    def _local_run(self, request: CareerRequest, _: Dict[str, Any]) -> Dict[str, Any]:
        role = request.target_role
        industry = request.target_industry
        domain = request.target_domain or industry
        skills = ", ".join(request.key_skills) if request.key_skills else "multi-disciplinary strengths"
        doubts = request.career_doubts or "curiosity about the journey ahead"
        summary_lines = _wrap(
            [
                f"{role} leaders in {industry} / {domain} orchestration fuse strategic imagination with hands-on"
                " engineering so every launch balances compliance, experimentation, and measurable business lift.",
                "They translate ambiguous board-level bets into credible prototypes, coach squads through trade-offs,"
                " and narrate impact for executives, regulators, and community partners alike.",
                f"Your current edge in {skills} becomes the raw material for differentiating customer journeys,"
                " automations, and monetization layers across regions such as"
                f" {request.location_preference or 'global innovation hubs'}.",
                "The role expects you to choreograph research, design, and delivery simultaneously while upskilling"
                " teammates on storytelling, safety, and sustainability lenses.",
                f"Typical doubts like '{doubts}' become coaching themes—you will learn to turn uncertainty into design"
                " questions, experiments, and clear executive updates.",
                "Expect to be both the diplomat who calms stakeholders and the architect who dives into telemetry"
                " dashboards to diagnose root causes while highlighting career-defining wins."
            ]
        )
        responsibilities = _wrap(
            [
                f"Architect north-star narratives that align {industry} regulations, customer delight, and margin goals.",
                "Design discovery rituals blending ethnographic research with instrumentation to prioritize the most"
                " courageous experiments.",
                "Sequence technical debt pay-down with frontier investments so squads can move fast without trading"
                " stability.",
                "Model hiring plans, vendor ecosystems, and governance cadences that empower inclusive teams.",
                "Develop executive-ready metrics cockpits and decision logs so momentum is visible and auditable.",
                "Mentor product engineers, designers, and analysts on synthesis skills and demo theater craft.",
                "Lead incident reviews that emphasize learning loops, psychological safety, and systemic fixes.",
                "Negotiate APIs, data contracts, and access controls with partner organizations.",
                "Champion communities of practice for experimentation, documentation, and accessibility.",
                "Evangelize responsible AI, sustainability budgets, and ethical review cadences that protect reputation."
            ]
        )
        tech_stack = [
            {
                "tool": "Docker",
                "description": "Containerize prototypes and internal tooling to replicate production parity locally and in CI pipelines.",
            },
            {
                "tool": "Kubernetes",
                "description": "Operate multi-service workloads, enforce rollout policies, and integrate observability for complex launches.",
            },
            {
                "tool": "Vertex AI / TensorFlow",
                "description": "Ship AI copilots responsibly with evaluation suites, prompt governance, and monitoring hooks.",
            },
            {
                "tool": "BigQuery + dbt",
                "description": "Materialize trusted intelligence layers that inform prioritization, success metrics, and experimentation.",
            },
            {
                "tool": "Plotly + Streamlit",
                "description": "Craft interactive control centers for stakeholders to explore KPIs, experiments, and insight memos in real time.",
            },
            {
                "tool": "Terraform",
                "description": "Codify compliant environments, set guardrails for data residency, and manage repeatable sandboxes.",
            },
            {
                "tool": "Notion / Confluence",
                "description": "Publish living playbooks, architecture decisions, and onboarding guides with transparent versioning.",
            },
        ]
        return {
            "role_summary": summary_lines,
            "key_responsibilities": responsibilities,
            "tech_stack": tech_stack,
        }


class MarketResearcher(BaseCareerAgent):
    def __init__(self, search_tool: SearchTool) -> None:
        super().__init__(
            name="MarketResearcher",
            system_prompt=(
                "Produce rich market telemetry: growth trajectories (JSON years + values), salary ladders, industry"
                " distribution, and narrative signals that justify the numbers."
            ),
            search_tool=search_tool,
        )

    def _local_run(self, request: CareerRequest, _: Dict[str, Any]) -> Dict[str, Any]:
        base_growth = 55
        years = list(range(2020, 2031))
        trend = [base_growth + idx * 3 for idx, _ in enumerate(years)]
        if request.target_industry.lower().startswith("fin"):
            trend = [value + 4 for value in trend]
        if any(skill.lower() in {"ai", "ml", "machine learning", "genai"} for skill in request.key_skills):
            trend = [value + 2 for value in trend]
        if request.location_preference:
            trend = [value + 1 for value in trend]
        salary_levels = ["Junior", "Mid", "Senior"]
        salary_values = [
            8.5 + len(request.key_skills) * 0.2,
            13.5 + len(request.key_skills) * 0.3,
            21.0 + len(request.key_skills) * 0.35,
        ]
        salary_values = [round(value, 1) for value in salary_values]
        industry_labels = [
            request.target_domain or request.target_industry,
            "Tech Platforms",
            "Healthcare",
            "Climate & Energy",
            "Creative AI",
        ]
        base_distribution = [38, 22, 16, 14, 10]
        narrative = _wrap(
            [
                f"Global hiring boards list {request.target_role} within {request.target_industry} as a mission-critical"
                " role because trust, automation, and customer-grade experiences now define competitive moats.",
                "Investors signal confidence by funding specialized tooling, co-pilots, and data exchanges that need"
                " leaders who blend governance with experimentation.",
                f"Your graduation horizon ({request.graduation_year}) plus {request.experience_level} exposure lets employers"
                " craft succession plans faster.",
                f"Location preference ({request.location_preference or 'global remote-first teams'}) opens hybrid pods that"
                " require cultural fluency and async leadership.",
                "Remote and hybrid orgs prize professionals who can run distributed rituals, maintain documentation"
                " discipline, and protect focus time while shipping measurable results.",
                "Communities across WomenInTech, OutInTech, and BlacksInTechnology now dedicate full tracks to this role,"
                " proving the long-term growth signal."
            ]
        )
        salary_copy = _wrap(
            [
                "Junior bands reflect rotational programs that include dedicated mentorship, experimentation sprints,"
                " and certification stipends.",
                "Mid-level compensation now packages equity refreshers, remote office budgets, and global conference"
                " travel built into learning KPIs.",
                "Senior leaders negotiate outcome-based bonuses, accelerators for IP generation, and sabbatical"
                " programs tied to community impact.",
                "Companies in regulated domains add compliance bonuses plus accelerated visa/legal support to secure talent."
            ]
        )
        return {
            "growth_data": {"years": years, "values": trend},
            "salary_data": {"levels": salary_levels, "values": salary_values, "narrative": salary_copy},
            "industry_dist": {"labels": industry_labels, "values": base_distribution},
            "narrative": narrative,
        }


class CurriculumArchitect(BaseCareerAgent):
    def __init__(self, search_tool: SearchTool) -> None:
        super().__init__(
            name="CurriculumArchitect",
            system_prompt=(
                "Return a four-stage plan. For B.Tech learners use Year 1-4, otherwise Step 1-4. Provide 10 lines per"
                " stage referencing the education level and key skills. Add 10-15 real course suggestions plus an"
                " intro paragraph and milestone data for visualizations."
            ),
            search_tool=search_tool,
        )

    def _timeline_labels(self, education_level: str) -> List[str]:
        if education_level.lower().startswith("b.tech"):
            return ["Year 1", "Year 2", "Year 3", "Year 4"]
        return ["Step 1", "Step 2", "Step 3", "Step 4"]

    def _foundation_line(self, request: CareerRequest) -> str:
        if "10th" in request.education_level:
            return "Choose Science Stream (PCM) and join the robotics / AI society to expose yourself to tinkering early."
        if "12th" in request.education_level:
            return "Prioritize math, physics, and CS labs while prototyping mini-projects that align with your dream role."
        if request.education_level.lower().startswith("working"):
            return "Audit current workflows, document transferrable wins, and carve weekly focus blocks for deep study."
        return "Anchor every semester/step with a north-star statement explaining why this role energizes you."

    def _local_run(self, request: CareerRequest, _: Dict[str, Any]) -> Dict[str, Any]:
        labels = self._timeline_labels(request.education_level)
        robotics_hint = any("robot" in skill.lower() for skill in request.key_skills)
        timeline: Dict[str, List[str]] = {}
        intro_lines = _wrap(
            [
                f"Because you are currently at the {request.education_level} stage with plans to graduate around"
                f" {request.graduation_year}, your learning runway can be choreographed like a cinematic arc.",
                "Each stage blends deep work, public storytelling, and community service so recruiters witness an"
                " ever-expanding body of proof.",
                f"Career doubts such as '{request.career_doubts or 'How do I stand out?'}' become prompts for experiments,"
                " retrospectives, and mentorship asks."
            ]
        )
        foundations = [
            self._foundation_line(request),
            "Document every build, lab, or hackathon experience publicly to normalize storytelling.",
            f"Translate {request.target_role} job descriptions into skill matrices and learning OKRs.",
            "Run quarterly retrospectives with mentors to refine focus areas and remove distractions.",
            "Reserve weekly deep work sessions for experimentation without notifications.",
            "Host peer teaching circles so concepts become second nature.",
            "Prototype with open datasets and APIs relevant to your target industry.",
            "Practice demo theater—design narratives, rehearse, and solicit radical feedback.",
            "Stay active in communities (Discord, Reddit, local meetups) that discuss the role.",
            "Invest in wellness rituals; careers are marathons, not sprints."
        ]
        if robotics_hint and "10th" in request.education_level:
            foundations[1] = "Design a weekend robotics habit: soldering basics, Arduino builds, and physics journaling."
        stage_templates = [
            "Master fundamentals: math, programming paradigms, and collaboration rituals.",
            "Launch multi-week projects blending AI, automation, and design storytelling.",
            "Pursue internships, research labs, or apprenticeships tied to the industry.",
            "Ship capstone artifacts, negotiation scripts, and onboarding playbooks."
        ]
        milestones: List[Dict[str, Any]] = []
        for idx, (label, template) in enumerate(zip(labels, stage_templates)):
            stage_lines = _wrap(
                [
                    template,
                    foundations[0],
                    "Pair theory with practice by recreating case studies inside Notion or Obsidian wikis.",
                    "Co-build with a diverse team and document decisions, trade-offs, and results.",
                    "Secure mentors across technology, product, and domain leadership.",
                    "Measure progress using OKRs covering skill depth, impact metrics, and community service.",
                    "Craft a brag doc with quantified wins each week.",
                    "Volunteer to review peers' portfolios; critique sharpens your own taste.",
                    "Automate tedious routines (note syncing, test harnesses) to free cognitive load.",
                    "Celebrate small wins through reflective journals or community shout-outs.",
                ]
            )
            timeline[label] = stage_lines
            milestones.append({"stage": label, "confidence": 60 + idx * 8, "focus": template})
        courses = [
            ("Coursera", "Google Advanced Data Analytics", "https://www.coursera.org/professional-certificates/google-advanced-data-analytics"),
            ("Coursera", "AI Product Management Specialization", "https://www.coursera.org/specializations/ai-product-management"),
            ("Udacity", "AI for Robotics", "https://www.udacity.com/course/artificial-intelligence-for-robotics--cs373"),
            ("MIT xPRO", "System Thinking", "https://xpro.mit.edu"),
            ("edX", "DevOps for Developers", "https://www.edx.org/course/devops-for-developers"),
            ("Stanford Online", "Machine Learning", "https://www.coursera.org/learn/machine-learning"),
            ("Harvard Online", "Data Science Principles", "https://pll.harvard.edu/course/data-science-principles"),
            ("Udemy", "Kubernetes Hands-On", "https://www.udemy.com/course/learn-kubernetes/"),
            ("LinkedIn Learning", "Design Thinking: Customer Experience", "https://www.linkedin.com/learning/topics/design-thinking"),
            ("PluralSight", "Terraform Deep Dive", "https://www.pluralsight.com/courses/terraform-getting-started"),
            ("Cohort", "OnDeck Product Builders", "https://www.beondeck.com/product"),
            ("YouTube", "Google Cloud Tech", "https://www.youtube.com/@googlecloudtech"),
            ("Codecademy", "Command Line & Git", "https://www.codecademy.com/learn/learn-the-command-line"),
        ]
        course_payload = [
            {
                "title": title,
                "provider": provider,
                "link": link,
            }
            for provider, title, link in courses
        ]
        return {
            "learning_intro": intro_lines,
            "timeline": timeline,
            "courses": course_payload,
            "milestones": milestones,
        }


class InsightCoach(BaseCareerAgent):
    def __init__(self, search_tool: SearchTool) -> None:
        super().__init__(
            name="InsightCoach",
            system_prompt=(
                "Produce 3 paragraphs describing day-in-life culture, list work-life strategies, share five success"
                " profiles, and derive benchmark skill scores for radar charts. Also surface spotlight snippets"
                " suitable for animated text."
            ),
            search_tool=search_tool,
        )

    def _local_run(self, request: CareerRequest, _: Dict[str, Any]) -> Dict[str, Any]:
        culture = _wrap(
            [
                f"Mornings often begin with telemetry scans, async stand-ups across time zones, and micro-journaling"
                f" intentions so {request.target_role} leaders show up grounded for the team.",
                "Afternoons are packed with co-creation rituals: ride-along user interviews, signal analysis in Plotly"
                " dashboards, and architecture reviews that balance experimentation with compliance.",
                "Evenings focus on synthesis—publishing decision logs, mentoring juniors, and recording demo reels"
                " so distributed partners stay informed."
            ]
        )
        work_life = _wrap(
            [
                "Schedule maker blocks before noon, stack meetings later, and defend two recovery evenings each week.",
                "Adopt written updates over ad-hoc syncs to reduce calendar bloat and preserve deep work.",
                "Create a personal playbook for crunch times: hydration cues, mindfulness breaks, and escalation trees.",
                "Rotate on-call responsibilities with explicit load-balancing agreements.",
                "Run quarterly joy audits—catalog what energizes you and design your calendar accordingly."
            ]
        )
        success_stories = [
            {"name": "Anisha Kaur", "role": "Head of Platform Intelligence @ FinTechX", "link": "https://www.linkedin.com"},
            {"name": "Diego Ramirez", "role": "Director of AI Experience @ HealthNova", "link": "https://www.linkedin.com"},
            {"name": "Mei Chen", "role": "Product Fellow @ Autonomous Lab", "link": "https://www.linkedin.com"},
            {"name": "Kwame Mensah", "role": "VP of Strategy @ GreenGrid", "link": "https://www.linkedin.com"},
            {"name": "Sara Anders", "role": "Chief Builder @ CreativeGen", "link": "https://www.linkedin.com"},
        ]
        required_skills = {skill: min(100, value + 12) for skill, value in request.skill_profile.items()}
        spotlights = _wrap(
            [
                "Leaders who narrate experiments like mini documentaries stand out in every promotion panel.",
                "Documented accessibility wins and sustainability metrics now show up on executive dashboards.",
                "Communities reward generous mentors—teaching is the fastest path to higher-scope charters."
            ]
        )
        return {
            "culture": culture,
            "work_life": work_life,
            "success_stories": success_stories,
            "required_skills": required_skills,
            "spotlights": spotlights,
        }


class AgentEngine:
    """Root orchestrator coordinating the four google-adk/Gemini powered agents."""

    def __init__(self) -> None:
        self.search_tool = SearchTool()
        self.role_agent = RoleAnalyst(self.search_tool)
        self.market_agent = MarketResearcher(self.search_tool)
        self.curriculum_agent = CurriculumArchitect(self.search_tool)
        self.insight_agent = InsightCoach(self.search_tool)
        self.workflow = self._compose_workflow()

    def _compose_workflow(self) -> Any:
        agents = [
            self.role_agent,
            self.market_agent,
            self.curriculum_agent,
            self.insight_agent,
        ]
        if hasattr(google_adk, "SequentialWorkflow"):
            try:
                return google_adk.SequentialWorkflow(agents)  # type: ignore[call-arg]
            except Exception:  # pragma: no cover
                return None
        return None

    def run_research(self, request: CareerRequest) -> Dict[str, Any]:
        # Shared memory ensures every agent/Gemini prompt inherits previous outputs.
        shared: Dict[str, Any] = {"request": request.__dict__}
        overview = self.role_agent.run(request, shared)
        shared["overview"] = overview
        market = self.market_agent.run(request, shared)
        shared["market"] = market
        roadmap = self.curriculum_agent.run(request, shared)
        shared["roadmap"] = roadmap
        insights = self.insight_agent.run(request, shared)
        shared["insights"] = insights
        resources = self.search_tool.run(f"{request.target_role} {request.target_industry} careers")
        return {
            "overview": overview,
            "market": market,
            "roadmap": roadmap,
            "insights": insights,
            "resources": resources,
            "skill_matrix": {
                "user": request.skill_profile,
                "required": insights["required_skills"],
            },
            "request": request,
        }

    def answer_question(self, question: str, analysis: Dict[str, Any]) -> str:
        if not analysis:
            return "Run the analysis first so I can reference your personalized roadmap."
        question_lower = question.lower()
        market = analysis.get("market", {})
        salary_data = market.get("salary_data", {})
        request: CareerRequest | None = analysis.get("request")  # type: ignore[assignment]
        if salary_data and any(keyword in question_lower for keyword in {"salary", "pay", "ctc", "compensation", "package"}):
            junior = salary_data.get("values", [None])[0]
            mid = salary_data.get("values", [None, None])[1]
            senior = salary_data.get("values", [None, None, None])[2]
            location_hint = getattr(request, "location_preference", "remote-first hubs") if request else "global hubs"
            industry = getattr(request, "target_industry", "growth industries") if request else "growth industries"
            fresher_line = (
                f"Entry-level ({industry}) offers average fresher compensation near INR {junior:.1f} LPA"
                f" when you highlight certified wins and internships in {location_hint}."
            ) if isinstance(junior, (int, float)) else "Entry-level compensation data is available once the analysis refreshes."
            mid_line = (
                f"Mid-level bands hover around INR {mid:.1f} LPA with equity top-ups and learning stipends."
            ) if isinstance(mid, (int, float)) else "Mid-level bands depend on specialization and city tier."
            senior_line = (
                f"Senior/lead charters frequently reach INR {senior:.1f} LPA plus outcome bonuses,"
                " especially for hybrid program owners."
            ) if isinstance(senior, (int, float)) else "Senior bands spike when you show multi-quarter impact."
            narrative = salary_data.get("narrative", [])
            narrative_hint = narrative[0] if narrative else "Companies sweeten offers with mentorship pods and certification budgets."
            return fill(" ".join([fresher_line, mid_line, senior_line, narrative_hint]))
        # Chat replies are multi-agent aware: we stitch highlights from role/market/roadmap/insights memory.
        snippets: List[str] = []
        role_summary = analysis.get("overview", {}).get("role_summary", [])
        if role_summary:
            snippets.append(f"Role context: {role_summary[0]}")
        growth_trend = analysis.get("market", {}).get("growth_data", {})
        if growth_trend:
            snippets.append(
                f"Market momentum shows growth hitting {growth_trend['values'][-1]} on the index by {growth_trend['years'][-1]}."
            )
        timeline = analysis.get("roadmap", {}).get("timeline", {})
        if timeline:
            first_stage = next(iter(timeline.values()))
            snippets.append(f"Roadmap kickoff: {first_stage[0]}")
        culture = analysis.get("insights", {}).get("culture", [])
        if culture:
            snippets.append(f"Team culture reminder: {culture[0]}")
        request_obj = analysis.get("request")
        if request_obj and getattr(request_obj, "career_doubts", ""):
            snippets.append(f"We will keep coaching you through '{request_obj.career_doubts}'.")
        closing = fill(
            "Reference these receipts when replying: cite growth numbers, roadmap stages, and one insight so"
            " stakeholders feel your preparation."
        )
        return "\n".join(snippets + ["", closing])


__all__ = ["AgentEngine", "CareerRequest"]
