from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registro-visitantes/', views.registro_visitantes, name='registro_visitantes'),
    path('registro-vehiculos/', views.registro_vehiculos, name='registro_vehiculos'),
    path('registro-proveedores/', views.registro_proveedores, name='registro_proveedores'),
    path('gestion-permisos/', views.gestion_permisos, name='gestion_permisos'),
    path('auditoria/', views.auditoria, name='auditoria'),
    path('registrar-salida-visitante/<int:visitante_id>/', views.registrar_salida_visitante, name='registrar_salida_visitante'),
    path('registrar-llegada-vehiculo/<int:vehiculo_id>/', views.registrar_llegada_vehiculo, name='registrar_llegada_vehiculo'),
    path('registrar-salida-proveedor/<int:proveedor_id>/', views.registrar_salida_proveedor, name='registrar_salida_proveedor'),
]
