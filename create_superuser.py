import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings")
django.setup()

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

if User.objects.filter(username=username).exists():
    print("⚠️ Superuser already exists — skipping.")
elif not password:
    print("⚠️ DJANGO_SUPERUSER_PASSWORD not set — no admin created (there is deliberately no default).")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print("✅ Superuser created successfully.")
