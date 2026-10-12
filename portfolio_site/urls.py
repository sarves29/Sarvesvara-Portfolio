from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('site_portfolio.urls', namespace='site_portfolio')),
]

# Uploaded media (project images, resumes). A portfolio's traffic is small enough
# that Django can serve these itself instead of needing a separate file host.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
