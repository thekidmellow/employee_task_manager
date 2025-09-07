from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core + Accounts
    path('', include('apps.core.urls', namespace='core')),              # add namespace for consistency
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),

    # Tasks with namespace (IMPORTANT)
    path('tasks/', include(('apps.tasks.urls', 'tasks'), namespace='tasks')),

    # Django auth defaults (login/logout/password reset, etc.) at root
    # If you already provide custom login/logout in apps.accounts, you can omit this line.
    path('', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
