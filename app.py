from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import streamlit as st
from docx import Document
from pypdf import PdfReader


STOP_WORDS = {
    "about", "after", "again", "against", "also", "and", "any", "are", "because", "been",
    "being", "between", "both", "but", "can", "did", "does", "doing", "for", "from",
    "had", "has", "have", "her", "here", "him", "his", "how", "into", "its", "more",
    "most", "not", "our", "out", "over", "own", "same", "she", "should", "some",
    "such", "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "too", "under", "until", "very", "was", "were", "what",
    "when", "where", "which", "while", "who", "why", "will", "with", "you", "your",
}


SKILL_BANK = {
    "agentic ai": ["agentic ai", "ai agent", "autonomous agent", "multi-agent", "agent orchestration"],
    "python": ["python", "pandas", "numpy", "fastapi", "flask", "streamlit"],
    "llm": ["llm", "large language model", "prompt engineering", "rag", "retrieval augmented generation"],
    "cloud": ["aws", "azure", "gcp", "cloud", "lambda", "s3", "ec2"],
    "data": ["sql", "etl", "data pipeline", "analytics", "tableau", "power bi"],
    "ml": ["machine learning", "scikit-learn", "model", "classification", "regression"],
    "devops": ["docker", "kubernetes", "ci/cd", "github actions", "deployment"],
    "finance": ["risk", "trading", "banking", "jpmc", "compliance", "payments"],
    "engineering": ["api", "microservices", "system design", "testing", "rest"],
    "leadership": ["stakeholder", "agile", "scrum", "mentored", "led", "ownership"],
}


ACTION_VERBS = [
    "Architected",
    "Automated",
    "Built",
    "Delivered",
    "Improved",
    "Integrated",
    "Optimized",
    "Reduced",
    "Scaled",
    "Streamlined",
]


@dataclass
class AgentStep:
    agent: str
    goal: str
    output: str


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def normalize_token(token: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", "", token.lower())


def extract_text_from_upload(uploaded_file) -> str:
    suffix = uploaded_file.name.lower().split(".")[-1]
    raw = uploaded_file.read()

    if suffix == "pdf":
        reader = PdfReader(io.BytesIO(raw))
        return clean_text("\n".join(page.extract_text() or "" for page in reader.pages))

    if suffix == "docx":
        document = Document(io.BytesIO(raw))
        return clean_text("\n".join(paragraph.text for paragraph in document.paragraphs))

    return clean_text(raw.decode("utf-8", errors="ignore"))


def extract_keywords(text: str, top_n: int = 24) -> list[str]:
    tokens = [normalize_token(token) for token in re.findall(r"[A-Za-z][A-Za-z0-9+#.]{1,}", text)]
    filtered = [
        token
        for token in tokens
        if token and token not in STOP_WORDS and len(token) > 2
    ]
    counts: dict[str, int] = {}
    for token in filtered:
        counts[token] = counts.get(token, 0) + 1
    return [word for word, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_n]]


def find_skills(text: str) -> dict[str, list[str]]:
    lowered = text.lower()
    matches: dict[str, list[str]] = {}
    for category, variants in SKILL_BANK.items():
        found = sorted({variant for variant in variants if variant in lowered})
        if found:
            matches[category] = found
    return matches


def flatten_skills(skills: dict[str, list[str]]) -> set[str]:
    return {item for variants in skills.values() for item in variants}


def similarity_score(resume_text: str, jd_text: str) -> float:
    resume_terms = set(extract_keywords(resume_text, top_n=120))
    jd_terms = set(extract_keywords(jd_text, top_n=120))
    if not resume_terms or not jd_terms:
        return 0.0
    overlap = resume_terms.intersection(jd_terms)
    return len(overlap) / len(jd_terms)


def score_fit(resume_text: str, jd_text: str) -> dict[str, object]:
    resume_skills = find_skills(resume_text)
    jd_skills = find_skills(jd_text)
    resume_flat = flatten_skills(resume_skills)
    jd_flat = flatten_skills(jd_skills)
    covered = sorted(resume_flat.intersection(jd_flat))
    missing = sorted(jd_flat.difference(resume_flat))
    skill_coverage = len(covered) / max(len(jd_flat), 1)
    semantic = similarity_score(resume_text, jd_text)
    final_score = round((0.65 * semantic + 0.35 * skill_coverage) * 100)
    return {
        "score": min(100, max(0, final_score)),
        "semantic": round(semantic * 100, 1),
        "skill_coverage": round(skill_coverage * 100, 1),
        "covered": covered,
        "missing": missing,
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
    }


def split_resume_bullets(resume_text: str) -> list[str]:
    normalized = resume_text.replace("\u2022", "\n")
    candidates = re.split(r"[\n]+|(?<=\.)\s+(?=[A-Z])", normalized)
    bullets = [clean_text(item.strip("-* ")) for item in candidates]
    return [item for item in bullets if 35 <= len(item) <= 240][:8]


def rewrite_bullets(bullets: Iterable[str], missing_keywords: list[str]) -> list[dict[str, str]]:
    keyword_hint = ", ".join(missing_keywords[:3]) if missing_keywords else "role-relevant systems"
    rewrites = []
    for index, bullet in enumerate(bullets):
        verb = ACTION_VERBS[index % len(ACTION_VERBS)]
        rewritten = f"{verb} {bullet[0].lower() + bullet[1:]} with emphasis on {keyword_hint}, measurable impact, and cross-functional delivery."
        rewrites.append({"Original": bullet, "Stronger version": rewritten})
    return rewrites


def interview_questions(missing: list[str], jd_keywords: list[str]) -> list[str]:
    focus = missing[:4] or jd_keywords[:4] or ["system design", "stakeholder communication", "delivery tradeoffs"]
    return [
        f"Tell me about a project where you used or quickly learned {skill}. What tradeoffs did you make?"
        for skill in focus
    ] + [
        "Walk me through how you would design an agentic AI workflow for this role.",
        "Describe a time you improved a process, measured the result, and communicated it to stakeholders.",
    ]


def build_report(resume_name: str, job_title: str, result: dict[str, object], keywords: list[str], questions: list[str]) -> str:
    missing = ", ".join(result["missing"]) or "No major tracked gaps"
    covered = ", ".join(result["covered"]) or "No tracked overlap found"
    question_lines = "\n".join(f"- {question}" for question in questions)
    return f"""# Agentic AI Career Copilot Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Resume: {resume_name}
Target role: {job_title or "Not specified"}

## Fit Summary

- Overall fit score: {result["score"]}/100
- Semantic similarity: {result["semantic"]}%
- Skill coverage: {result["skill_coverage"]}%
- Covered signals: {covered}
- Gaps to address: {missing}

## High-Value Job Keywords

{", ".join(keywords)}

## Interview Prep

{question_lines}
"""


def run_agents(resume_text: str, jd_text: str, job_title: str) -> tuple[list[AgentStep], dict[str, object]]:
    steps: list[AgentStep] = []

    steps.append(
        AgentStep(
            "Planner Agent",
            "Create a task plan for resume-to-role analysis.",
            "Plan: parse resume, extract job signals, score fit, identify gaps, coach resume bullets, prepare interview prompts.",
        )
    )

    resume_keywords = extract_keywords(resume_text)
    steps.append(
        AgentStep(
            "Resume Parser Agent",
            "Extract candidate signals from uploaded resume.",
            f"Found {len(resume_keywords)} prominent resume keywords including: {', '.join(resume_keywords[:8])}.",
        )
    )

    jd_keywords = extract_keywords(jd_text)
    steps.append(
        AgentStep(
            "JD Intelligence Agent",
            "Extract role requirements and ranking signals from job description.",
            f"Target role '{job_title or 'unspecified'}' emphasizes: {', '.join(jd_keywords[:10])}.",
        )
    )

    result = score_fit(resume_text, jd_text)
    steps.append(
        AgentStep(
            "Fit Scoring Agent",
            "Calculate resume-role match using semantic similarity and skill coverage.",
            f"Overall fit is {result['score']}/100 with {result['semantic']}% semantic similarity and {result['skill_coverage']}% skill coverage.",
        )
    )

    bullets = split_resume_bullets(resume_text)
    rewrites = rewrite_bullets(bullets, result["missing"])
    steps.append(
        AgentStep(
            "Resume Coach Agent",
            "Rewrite resume bullets to better match the role.",
            f"Generated {len(rewrites)} stronger bullet suggestions using missing role signals where appropriate.",
        )
    )

    questions = interview_questions(result["missing"], jd_keywords)
    steps.append(
        AgentStep(
            "Interview Coach Agent",
            "Generate focused interview preparation prompts.",
            f"Prepared {len(questions)} interview questions based on gaps and role keywords.",
        )
    )

    result["resume_keywords"] = resume_keywords
    result["jd_keywords"] = jd_keywords
    result["rewrites"] = rewrites
    result["questions"] = questions
    return steps, result


st.set_page_config(
    page_title="Agentic AI Career Copilot",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; max-width: 1180px;}
    div[data-testid="stMetric"] {background: #f7f7f8; border: 1px solid #e4e4e7; padding: 0.85rem; border-radius: 8px;}
    .agent-step {border: 1px solid #e4e4e7; border-radius: 8px; padding: 0.8rem 0.95rem; margin-bottom: 0.65rem; background: #ffffff;}
    .agent-name {font-weight: 700; color: #111827;}
    .agent-goal {font-size: 0.86rem; color: #52525b; margin: 0.15rem 0 0.35rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Agentic AI Career Copilot")
st.caption("A free, multi-agent resume and interview preparation system. Analyzes your resume and gets you interview-ready.")

with st.sidebar:
    st.header("Inputs")
    job_title = st.text_input("Target role", placeholder="Agentic AI Engineer")
    uploaded_resume = st.file_uploader("Resume", type=["pdf", "docx", "txt"])
    sample_mode = st.toggle("Use sample resume", value=uploaded_resume is None)

    st.divider()
    st.subheader("Agent Controls")
    show_trace = st.toggle("Show agent trace", value=True)
    show_rewrites = st.toggle("Show resume rewrites", value=True)


sample_resume = """
Software Engineer with 5 years of experience building Python applications, REST APIs, data pipelines, and automation workflows for financial services.
Built Streamlit dashboards and SQL analytics for operations teams, reducing manual reporting effort by 40 percent.
Developed Python ETL jobs with pandas and cloud storage integrations for risk and compliance reporting.
Partnered with stakeholders in agile teams to deliver production features, testing improvements, and system documentation.
"""

default_jd = """
We are hiring an Agentic AI Engineer to design multi-agent workflows, build RAG applications, integrate LLM tools, deploy Python services, and collaborate with product stakeholders.
The role requires Python, Streamlit or FastAPI, prompt engineering, retrieval augmented generation, cloud deployment, API design, testing, and strong communication.
Experience in banking, compliance, or risk analytics is a plus.
"""

job_description = st.text_area("Job description", value=default_jd, height=220)

resume_text = ""
resume_name = "sample_resume.txt"
if uploaded_resume is not None:
    resume_name = uploaded_resume.name
    resume_text = extract_text_from_upload(uploaded_resume)
elif sample_mode:
    resume_text = clean_text(sample_resume)

analyze = st.button("Run agentic analysis", type="primary", use_container_width=True)

if not resume_text:
    st.info("Upload a resume or enable the sample resume to run the agent workflow.")
elif not clean_text(job_description):
    st.warning("Paste a job description to analyze role fit.")
elif analyze or sample_mode:
    steps, result = run_agents(resume_text, clean_text(job_description), job_title)

    score_col, sem_col, cov_col = st.columns(3)
    score_col.metric("Overall fit", f"{result['score']}/100")
    sem_col.metric("Semantic match", f"{result['semantic']}%")
    cov_col.metric("Skill coverage", f"{result['skill_coverage']}%")

    st.subheader("Score breakdown")
    for label, value in [
        ("Semantic match", result["semantic"]),
        ("Skill coverage", result["skill_coverage"]),
        ("Overall fit", result["score"]),
    ]:
        st.write(f"{label}: {value}%")
        st.progress(int(value) / 100)

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Covered role signals")
        if result["covered"]:
            st.write(", ".join(result["covered"]))
        else:
            st.write("No tracked role signals found in both documents.")

        st.subheader("Missing role signals")
        if result["missing"]:
            st.write(", ".join(result["missing"]))
        else:
            st.write("No major tracked gaps found.")

    with right:
        st.subheader("High-value JD keywords")
        st.write(", ".join(result["jd_keywords"][:18]))

        st.subheader("Resume keyword signals")
        st.write(", ".join(result["resume_keywords"][:18]))

    if show_trace:
        st.subheader("Agent execution trace")
        for step in steps:
            st.markdown(
                f"""
                <div class="agent-step">
                  <div class="agent-name">{step.agent}</div>
                  <div class="agent-goal">{step.goal}</div>
                  <div>{step.output}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if show_rewrites:
        st.subheader("Resume bullet rewrites")
        rewrites = result["rewrites"]
        if rewrites:
            st.table(rewrites)
        else:
            st.write("Add more detailed resume bullets to generate rewrite suggestions.")

    st.subheader("Interview prep")
    for question in result["questions"]:
        st.write(f"- {question}")

    report = build_report(resume_name, job_title, result, result["jd_keywords"], result["questions"])
    st.download_button(
        "Download Markdown report",
        data=report,
        file_name="agentic_ai_career_report.md",
        mime="text/markdown",
        use_container_width=True,
    )
else:
    st.info("Click **Run agentic analysis** to start the workflow.")
