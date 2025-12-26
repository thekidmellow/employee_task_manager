from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.templatetags.static import static as static_url

urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "favicon.ico",
        RedirectView.as_view(
            url=static_url("favicon.ico"),
            permanent=True,
        ),
    ),

    path("", include("apps.core.urls", namespace="core")),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("tasks/", include(("apps.tasks.urls", "tasks"), namespace="tasks")),
    path("", include("django.contrib.auth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

handler404 = "apps.core.views.custom_404"
handler500 = "apps.core.views.custom_500"
