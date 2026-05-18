from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import TemplateView

admin.site.site_header = 'Gestor Biblioteca FACEAC'
admin.site.site_title = 'Gestor Biblioteca'
admin.site.index_title = 'Panel de Administración'

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('importar/', include('apps.importacion.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
