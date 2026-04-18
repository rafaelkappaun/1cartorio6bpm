from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rotas do App (Templates e Lógica Principal)
    path('', include('gestao.urls')),

    # Admin Django
    path('admin/', admin.site.urls),
]

# Servir arquivos de mídia
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)