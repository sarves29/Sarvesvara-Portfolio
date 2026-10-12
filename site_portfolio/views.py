from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, Http404
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.contrib import messages
import html
import logging
import os
import threading
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect
from .forms import ContactForm
from .models import Project, Resume

logger = logging.getLogger(__name__)

def index(request):
    projects = Project.objects.order_by('order')
    return render(request, 'site_portfolio/index.html', {'projects': projects})

def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    return render(request, 'site_portfolio/project_detail.html', {'project': project})

def send_email_async(message):
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        logger.info("Contact email sent: %s", response.status_code)
    except Exception:
        logger.exception("Error sending contact email")


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    # The proxy appends the real client address last; earlier entries are client-supplied.
    return forwarded.split(",")[-1].strip() or request.META.get("REMOTE_ADDR", "")


def rate_limited(request):
    key = f"contact-rate:{client_ip(request)}"
    count = cache.get(key, 0)
    if count >= settings.CONTACT_RATE_LIMIT:
        return True
    cache.set(key, count + 1, timeout=3600)
    return False

def contact(request):
    if request.method == "POST":
        if rate_limited(request):
            messages.error(request, "⚠️ Too many messages — please try again later.")
            return redirect("site_portfolio:contact")

        form = ContactForm(request.POST)
        if not form.is_valid():
            messages.error(request, "⚠️ Please fill out all fields with a valid email.")
            return redirect("site_portfolio:contact")

        # Escape everything the visitor typed before it goes into an HTML email.
        name = html.escape(form.cleaned_data["name"])
        email = html.escape(form.cleaned_data["email"])
        message = html.escape(form.cleaned_data["message"]).replace("\n", "<br>")

        subject = f"Portfolio Contact: {form.cleaned_data['name'][:80]}"
        html_content = f"""
            <h2>New Message from Portfolio</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Message:</strong><br>{message}</p>
        """

        mail = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=settings.CONTACT_TO_EMAIL,
            subject=subject,
            html_content=html_content,
        )
        threading.Thread(target=send_email_async, args=(mail,), daemon=True).start()
        messages.success(request, "✅ Your message has been sent successfully!")

        return redirect("site_portfolio:contact")

    return render(request, "site_portfolio/contact.html")
    
def download_resume(request):
    latest_resume = Resume.objects.order_by('-uploaded_at').first()
    if not latest_resume:
        raise Http404("Resume not found.")
    return FileResponse(latest_resume.file.open('rb'), as_attachment=True, filename=latest_resume.file.name.split('/')[-1])
