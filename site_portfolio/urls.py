from django.urls import path

from . import views

app_name = "site_portfolio"

urlpatterns = [
    path("", views.index, name="index"),
    path("projects/<slug:slug>/", views.project_detail, name="project_detail"),
    path("now/", views.now_page, name="now"),
    path("contact/", views.contact, name="contact"),
    path("resume/download/", views.download_resume, name="download_resume"),
    path("api/ai/ask/", views.ai_ask, name="ai_ask"),
    path("sw.js", views.service_worker, name="service_worker"),
]
