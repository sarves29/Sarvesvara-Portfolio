from django.conf import settings


def site_meta(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_URL": settings.SITE_URL,
        "GITHUB_USERNAME": settings.PORTFOLIO_GITHUB_USERNAME,
        "UMAMI_SRC": settings.UMAMI_SRC,
        "UMAMI_WEBSITE_ID": settings.UMAMI_WEBSITE_ID,
        "NAV_LINKS": [
            {"label": "Work", "href": "/#work"},
            {"label": "About", "href": "/#about"},
            {"label": "Now", "href": "/now/"},
            {"label": "Contact", "href": "/contact/"},
        ],
    }
