from django.db import models
from django.utils.text import slugify


class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    short_summary = models.CharField(max_length=300)
    long_description = models.TextField(blank=True)

    tech_list = models.CharField(max_length=400, help_text="Comma separated")
    github_url = models.URLField(blank=True, null=True)
    demo_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to="projects/", blank=True, null=True)

    year = models.CharField(max_length=40, blank=True, help_text="e.g. 2024 — Present")
    role = models.CharField(max_length=120, blank=True, help_text="Your role on this project")
    company = models.CharField(max_length=120, blank=True)

    problem = models.TextField(blank=True, help_text="What problem did this solve?")
    approach = models.TextField(blank=True, help_text="How did you approach it?")
    outcome = models.TextField(blank=True, help_text="What was the impact?")
    metrics = models.TextField(blank=True, help_text="One metric per line, e.g. '99.9% uptime'")

    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def tech_tags(self):
        return [t.strip() for t in self.tech_list.split(",") if t.strip()]

    def metrics_list(self):
        return [m.strip() for m in self.metrics.splitlines() if m.strip()]

    def __str__(self):
        return self.title


class Resume(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="resumes/")
    extracted_text = models.TextField(blank=True)
    processed = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title


class Profile(models.Model):
    """Single-row bio used as grounding context for the AI chat."""

    name = models.CharField(max_length=120, default="Sarvesvara Ramar")
    title = models.CharField(max_length=160, default="Backend / Product Engineer")
    tagline = models.CharField(max_length=240, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=120, default="Chennai, India")
    email = models.EmailField(default="sarvesvarasar@gmail.com")
    phone = models.CharField(max_length=40, blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    ai_system_prompt = models.TextField(
        blank=True,
        help_text="System instructions for the AI chat. Leave blank to use default.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profile"

    def __str__(self):
        return self.name
