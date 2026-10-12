from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Project


class StaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return ["site_portfolio:index", "site_portfolio:now", "site_portfolio:contact"]

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.9
    protocol = "https"

    def items(self):
        return Project.objects.all()

    def location(self, obj):
        return reverse("site_portfolio:project_detail", args=[obj.slug])

    def lastmod(self, obj):
        return obj.created_at


SITEMAPS = {
    "static": StaticSitemap,
    "projects": ProjectSitemap,
}
