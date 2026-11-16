from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path



def saude(request):
    """Endpoint leve para monitoramento de disponibilidade (uptime)."""
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("saude/", saude, name="saude"),
    path("admin/", admin.site.urls),
    path("", include("agenda.urls")),
]
