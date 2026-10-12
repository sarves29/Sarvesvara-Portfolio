import html
import json
import logging
import os
import threading
import time

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from . import ai_chat
from .incidents import INCIDENT
from .models import Profile, Project, Resume

logger = logging.getLogger(__name__)

AI_RATE_LIMIT = 8  # requests
AI_RATE_WINDOW = 60  # seconds
CONTACT_RATE_LIMIT = 5  # messages
CONTACT_RATE_WINDOW = 60 * 60  # seconds


def _get_profile():
    return Profile.objects.first()


@ensure_csrf_cookie
def index(request):
    projects = Project.objects.all()
    featured = projects.filter(featured=True)
    return render(
        request,
        "site_portfolio/index.html",
        {
            "profile": _get_profile(),
            "projects": projects,
            "featured": featured,
            "incident": INCIDENT,
        },
    )


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    related = Project.objects.exclude(pk=project.pk)[:2]
    return render(
        request,
        "site_portfolio/project_detail.html",
        {"project": project, "related": related, "profile": _get_profile()},
    )


GITHUB_EVENT_LABELS = {
    "PushEvent": "pushed to",
    "PullRequestEvent": "opened PR in",
    "CreateEvent": "created",
    "WatchEvent": "starred",
    "ForkEvent": "forked",
    "IssuesEvent": "issue in",
    "IssueCommentEvent": "commented on",
    "ReleaseEvent": "released",
    "PublicEvent": "open-sourced",
}


def _fetch_github_events(username: str, limit: int = 6):
    if not username:
        return []
    import json as _json
    import urllib.request

    cache_key = f"gh_events:{username}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"https://api.github.com/users/{username}/events/public?per_page=30"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "sarvesvara-portfolio"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            raw = _json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("github events fetch failed: %s", exc)
        cache.set(cache_key, [], 120)
        return []

    events = []
    for ev in raw:
        label = GITHUB_EVENT_LABELS.get(ev.get("type"), ev.get("type", "activity"))
        repo = (ev.get("repo") or {}).get("name", "")
        if not repo:
            continue
        events.append({
            "label": label,
            "repo": repo,
            "repo_url": f"https://github.com/{repo}",
            "created_at": ev.get("created_at", ""),
            "type": ev.get("type", ""),
        })
        if len(events) >= limit:
            break

    cache.set(cache_key, events, 600)
    return events


def now_page(request):
    events = _fetch_github_events(settings.PORTFOLIO_GITHUB_USERNAME)
    return render(
        request,
        "site_portfolio/now.html",
        {
            "profile": _get_profile(),
            "github_events": events,
            "github_username": settings.PORTFOLIO_GITHUB_USERNAME,
        },
    )


def _send_email_async(message):
    try:
        api_key = settings.SENDGRID_API_KEY
        if not api_key:
            logger.warning("SendGrid API key missing — skipping send")
            return
        SendGridAPIClient(api_key).send(message)
    except Exception:
        logger.exception("SendGrid error")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()

        if _rate_limited(f"contact:{_client_ip(request)}", CONTACT_RATE_LIMIT, CONTACT_RATE_WINDOW):
            messages.error(request, "Too many messages — please try again later.")
            return redirect("site_portfolio:contact")

        if not name or not email or not message:
            messages.error(request, "Please fill out all fields.")
            return redirect("site_portfolio:contact")
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("site_portfolio:contact")
        if len(name) > 100 or len(message) > 5000:
            messages.error(request, "That message is too long.")
            return redirect("site_portfolio:contact")

        # Everything the visitor typed is escaped before it goes into an HTML email.
        html_content = (
            f"<h2>New message from portfolio</h2>"
            f"<p><strong>From:</strong> {html.escape(name)} &lt;{html.escape(email)}&gt;</p>"
            f"<p><strong>Message:</strong></p><p>{html.escape(message).replace(chr(10), '<br>')}</p>"
        )
        mail = Mail(
            from_email=settings.PORTFOLIO_CONTACT_FROM,
            to_emails=settings.PORTFOLIO_CONTACT_TO,
            subject=f"Portfolio contact — {name[:80]}",
            html_content=html_content,
        )
        threading.Thread(target=_send_email_async, args=(mail,), daemon=True).start()
        messages.success(request, "Message sent. I'll get back to you within a day.")
        return redirect("site_portfolio:contact")

    return render(request, "site_portfolio/contact.html", {"profile": _get_profile()})


def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, "site_portfolio", "static", "site_portfolio", "sw.js")
    with open(sw_path, "rb") as fh:
        body = fh.read()
    resp = HttpResponse(body, content_type="application/javascript")
    resp["Service-Worker-Allowed"] = "/"
    resp["Cache-Control"] = "no-cache"
    return resp


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /api/",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def download_resume(request):
    latest = Resume.objects.first()
    if latest and latest.file and latest.file.storage.exists(latest.file.name):
        filename = os.path.basename(latest.file.name)
        return FileResponse(latest.file.open("rb"), as_attachment=True, filename=filename)

    fallback = os.path.join(settings.MEDIA_ROOT, "resumes", "Sarvesvara_Resume.pdf")
    if os.path.exists(fallback):
        return FileResponse(open(fallback, "rb"), as_attachment=True, filename="Sarvesvara_Ramar_Resume.pdf")

    raise Http404("Resume not found.")


def _client_ip(request):
    # nginx sets X-Real-IP from the TCP peer. X-Forwarded-For's first entry is
    # whatever the client sent, so trusting it let anyone dodge the rate limits.
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR", "unknown")


def _rate_limited(key: str, limit: int, window: int) -> bool:
    hits = cache.get(key, 0)
    if hits >= limit:
        return True
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
    return False


@require_POST
def ai_ask(request):
    """AI chat endpoint — Gemini-grounded Q&A on Sarvesvara's profile + projects."""
    if not ai_chat.is_available():
        return JsonResponse({"error": "AI chat is not configured."}, status=503)

    if _rate_limited(f"ai_ask:{_client_ip(request)}", AI_RATE_LIMIT, AI_RATE_WINDOW):
        return JsonResponse(
            {"error": "Too many questions. Give me a moment, then try again."},
            status=429,
        )

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    question = (payload.get("question") or "").strip()
    if not question:
        return JsonResponse({"error": "Ask a question first."}, status=400)
    if len(question) > ai_chat.MAX_QUESTION_CHARS:
        return JsonResponse({"error": "Question is too long — keep it under 500 characters."}, status=400)

    start = time.monotonic()
    try:
        text = ai_chat.answer(question)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ai_ask failed: %s", exc)
        return JsonResponse({"error": "Something broke on my end. Try again in a minute."}, status=502)

    return JsonResponse(
        {"answer": text, "elapsed_ms": int((time.monotonic() - start) * 1000)},
        status=200,
    )
