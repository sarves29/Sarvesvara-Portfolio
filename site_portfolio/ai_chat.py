"""Gemini-backed chat grounded on Profile + Projects + Resume text."""
from __future__ import annotations

import logging
from functools import lru_cache

from django.conf import settings

from .models import Profile, Project, Resume

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"
MAX_QUESTION_CHARS = 500
MAX_RESUME_CHARS = 8000

SYSTEM_INSTRUCTION = """You are the AI assistant embedded in Sarvesvara Ramar's portfolio site.
You answer questions about Sarvesvara's experience, projects, tech stack, and fit for roles,
using ONLY the grounding context provided below. Speak about him in the third person
("Sarvesvara built…", "he owns…"), in a calm, confident, plain voice — no hype, no emojis.

Rules:
- Stay inside 2–4 short paragraphs, or a tight bulleted list when listing tech/projects.
- If the grounding doesn't cover something, say so briefly and suggest what it does cover.
- Never invent employers, dates, metrics, or credentials.
- Politely decline questions unrelated to his professional background.
- When citing a project, refer to it by its title so the reader can find it on the site."""


def _profile_block(profile: Profile | None) -> str:
    if not profile:
        return ""
    lines = [
        f"Name: {profile.name}",
        f"Title: {profile.title}",
        f"Location: {profile.location}",
    ]
    if profile.tagline:
        lines.append(f"Tagline: {profile.tagline}")
    if profile.bio:
        lines.append(f"Bio:\n{profile.bio.strip()}")
    if profile.github_url:
        lines.append(f"GitHub: {profile.github_url}")
    if profile.linkedin_url:
        lines.append(f"LinkedIn: {profile.linkedin_url}")
    return "## Profile\n" + "\n".join(lines)


def _project_block(projects) -> str:
    if not projects:
        return ""
    parts = ["## Projects"]
    for p in projects:
        chunk = [f"### {p.title}"]
        meta = []
        if p.role:
            meta.append(f"role: {p.role}")
        if p.company:
            meta.append(f"company: {p.company}")
        if p.year:
            meta.append(f"year: {p.year}")
        if meta:
            chunk.append(" · ".join(meta))
        if p.short_summary:
            chunk.append(f"Summary: {p.short_summary}")
        if p.tech_list:
            chunk.append(f"Stack: {p.tech_list}")
        if p.problem:
            chunk.append(f"Problem: {p.problem.strip()}")
        if p.approach:
            chunk.append(f"Approach: {p.approach.strip()}")
        if p.outcome:
            chunk.append(f"Outcome: {p.outcome.strip()}")
        if p.metrics:
            chunk.append("Metrics:\n" + p.metrics.strip())
        parts.append("\n".join(chunk))
    return "\n\n".join(parts)


def _resume_block(resume: Resume | None) -> str:
    if not resume or not resume.extracted_text:
        return ""
    text = resume.extracted_text.strip()[:MAX_RESUME_CHARS]
    return f"## Resume (extracted text)\n{text}"


def build_context() -> str:
    profile = Profile.objects.first()
    projects = list(Project.objects.all())
    resume = Resume.objects.first()
    blocks = [_profile_block(profile), _project_block(projects), _resume_block(resume)]
    return "\n\n".join(b for b in blocks if b)


@lru_cache(maxsize=1)
def _get_client():
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return None
    try:
        from google import genai
    except ImportError:
        logger.warning("google-genai not installed")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:  # noqa: BLE001
        logger.exception("failed to init gemini client: %s", exc)
        return None


def is_available() -> bool:
    return _get_client() is not None


def answer(question: str) -> str:
    question = (question or "").strip()
    if not question:
        raise ValueError("empty question")
    if len(question) > MAX_QUESTION_CHARS:
        raise ValueError("question too long")

    client = _get_client()
    if client is None:
        raise RuntimeError("AI chat is not configured")

    profile = Profile.objects.first()
    system = profile.ai_system_prompt.strip() if profile and profile.ai_system_prompt else SYSTEM_INSTRUCTION
    context = build_context()

    prompt = (
        f"{system}\n\n"
        f"--- GROUNDING CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
        f"Visitor's question: {question}\n\n"
        "Answer using only the grounding context."
    )

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    text = (getattr(response, "text", "") or "").strip()
    if not text:
        raise RuntimeError("empty response from model")
    return text
