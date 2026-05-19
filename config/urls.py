from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from apps.reportes.views import dashboard

admin.site.site_header = 'Gestor Biblioteca FACEAC'
admin.site.site_title = 'Gestor Biblioteca'
admin.site.index_title = 'Panel de Administración'

urlpatterns = [
    path('', dashboard, name='home'),
    path('importar/', include('apps.importacion.urls')),
    path('prestamos/', include('apps.prestamos.urls')),
    path('catalogo/', include('apps.catalogo.urls')),
    path('personas/', include('apps.usuarios.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path('alertas/', include('apps.alertas.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
