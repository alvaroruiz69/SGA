"""
Configuración de rutas para la aplicación SGA.
"""

from django.contrib.auth.views import LogoutView
from django.urls import path

from core import views

from .views import editar_usuario, gestion_permisos

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    # path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('registro-visitantes/', views.registro_visitantes,
         name='registro_visitantes'),
    path('registro-vehiculos/', views.registro_vehiculos,
         name='registro_vehiculos'),
    path('registro-proveedores/', views.registro_proveedores,
         name='registro_proveedores'),
    path('auditoria/', views.auditoria, name='auditoria'),
    path('registrar-salida-visitante/<int:visitante_id>/',
         views.registrar_salida_visitante, name='registrar_salida_visitante'),
    path('registrar-llegada-vehiculo/<int:vehiculo_id>/',
         views.registrar_llegada_vehiculo, name='registrar_llegada_vehiculo'),
    path('registrar-salida-proveedor/<int:proveedor_id>/',
         views.registrar_salida_proveedor, name='registrar_salida_proveedor'),
    path('api/visitor-data/', views.get_visitor_data, name='get_visitor_data'),
    path('api/vehicle-data/', views.get_vehicle_data, name='get_vehicle_data'),
    path('api/provider-data/', views.get_provider_data, name='get_provider_data'),

    path('gestion_permisos/', views.gestion_permisos, name='gestion_permisos'),
    path('editar_usuario/<int:user_id>/',
         views.editar_usuario, name='editar_usuario'),
    path('logout/', views.custom_logout, name='logout'),
    path('unauthorized/', views.unauthorized_access, name='unauthorized_access'),
]
