"""
Este módulo contiene los modelos para la aplicación core del sistema de gestión de acceso.
"""
from django.contrib.auth.models import User  # pylint: disable=E5142
from django.db import models
from django.utils import timezone


class Visitante(models.Model):
    run = models.CharField(max_length=12)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    numero_tarjeta = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    motivo_visita = models.TextField()
    observaciones = models.TextField(blank=True, null=True)
    hora_entrada = models.DateTimeField(default=timezone.now)
    hora_salida = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellidos} - RUN: {self.run}"

    class Meta:
        ordering = ['-hora_entrada']


class Vehiculo(models.Model):
    matricula = models.CharField(max_length=10)
    tipo_vehiculo = models.CharField(max_length=50)
    nombre_conductor = models.CharField(max_length=100)
    kilometraje_salida = models.IntegerField()
    kilometraje_llegada = models.IntegerField(null=True, blank=True)
    destino = models.CharField(max_length=200)
    numero_personas = models.IntegerField()
    hora_salida = models.DateTimeField(auto_now_add=True)
    hora_llegada = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.matricula} - {self.nombre_conductor}"


class Proveedor(models.Model):
    run = models.CharField(max_length=12)
    nombre_conductor = models.CharField(max_length=100)
    nombre_empresa = models.CharField(max_length=100)
    domicilio = models.CharField(max_length=200)
    tipo_vehiculo = models.CharField(max_length=50)
    matricula = models.CharField(max_length=10)
    guia_despacho = models.CharField(max_length=50)
    encargado_recepcion = models.CharField(max_length=100)
    hora_ingreso = models.DateTimeField(auto_now_add=True)
    hora_salida = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre_empresa} - {self.nombre_conductor}"


class AuditoriaAccion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=200)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.accion}"
