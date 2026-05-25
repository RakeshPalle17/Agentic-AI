# Agentic AI Career Copilot

An interview-ready Streamlit project that demonstrates an agentic AI workflow without paid APIs. The app analyzes a resume against a target job description, runs a multi-agent pipeline, and produces a recruiter-style fit score, skill gaps, resume bullet rewrites, interview prep, and a visible execution trace.

## Why this helps a resume

- Shows practical Agentic AI architecture: planner, parser, skill extractor, fit scorer, resume coach, and interview coach agents.
- Uses tool-driven orchestration instead of a basic chatbot.
- Runs with free/open-source Python packages and can be deployed on Streamlit Community Cloud for free.
- Solves a real candidate workflow: tailoring resumes and interview preparation for specific roles.

## Features

- Upload PDF, DOCX, or TXT resume.
- Paste any job description.
- View agent execution trace and intermediate outputs.
- Compute role-fit score with keyword overlap and skill coverage.
- Detect missing skills and high-value keywords.
- Generate stronger resume bullet rewrites.
- Generate interview questions and STAR story prompts.
- Export an analysis report as Markdown.

## Local setup

Install Python 3.11 or newer for free from https://www.python.org/downloads/ if `python --version` does not work in your terminal. On Windows, check **Add python.exe to PATH** during install. If PowerShell opens the Microsoft Store instead of Python, turn off the App execution aliases for `python.exe` and `python3.exe` in Windows Settings.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Resume bullets you can use

- Built an Agentic AI Career Copilot using Streamlit, Python, keyword retrieval, and modular agent orchestration to analyze resumes against job descriptions and generate actionable interview preparation.
- Implemented a multi-agent workflow with planner, resume parser, skill extractor, fit scorer, resume coach, and interview coach agents, including transparent execution traces for explainability.
- Deployed a free, recruiter-facing AI application on Streamlit Community Cloud using only open-source dependencies and no paid LLM APIs.
