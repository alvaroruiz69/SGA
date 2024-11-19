"""
Este módulo contiene las vistas para manejar las funcionalidades de la aplicación 'core'.
"""
# pylint: disable=import-error

import re

import weasyprint
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from core.models import AuditoriaAccion, Proveedor, Vehiculo, Visitante


def login_view(request):
    """
    Maneja el inicio de sesión del usuario.
    """
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Credenciales inválidas")
    return render(request, "core/login.html")


@login_required
def home(request):
    """
    Maneja el inicio de sesión del usuario.
    """
    return render(request, "core/home.html")


@login_required
def get_visitor_data(request):
    """
    Maneja el registro de salida visitantes.
    """
    run = request.GET.get('run')
    visitor = Visitante.objects.filter(
        run=run).order_by('-hora_entrada').first()
    if visitor:
        return JsonResponse({
            'exists': True,
            'nombre': visitor.nombre,
            'apellidos': visitor.apellidos,
            'direccion': visitor.direccion
        })
    else:
        return JsonResponse({'exists': False})


@login_required
def registro_visitantes(request):
    """
    Maneja el registro de visitantes.
    """
    if request.method == 'POST':
        # Validación del servidor
        run = request.POST.get('run')
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        numero_tarjeta = request.POST.get('numero_tarjeta')

        if not run or not nombre or not apellidos or not numero_tarjeta:
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('registro_visitantes')

        if not re.match(r'^\d{7,8}-[\d|kK]{1}$', run):
            messages.error(request, 'Formato de RUN inválido.')
            return redirect('registro_visitantes')

        if not nombre.replace(' ', '').isalpha() or not apellidos.replace(' ', '').isalpha():
            messages.error(
                request, 'El nombre y apellidos deben contener solo letras.')
            return redirect('registro_visitantes')

        if not numero_tarjeta.isdigit():
            messages.error(
                request, 'El número de tarjeta debe contener solo números.')
            return redirect('registro_visitantes')

        # Crear nuevo visitante
        Visitante.objects.create(
            run=run,
            nombre=nombre,
            apellidos=apellidos,
            numero_tarjeta=numero_tarjeta,
            direccion=request.POST.get('direccion'),
            motivo_visita=request.POST.get('motivo_visita'),
            observaciones=request.POST.get('observaciones'),
            hora_entrada=timezone.now()
        )
        messages.success(request, 'Visitante registrado con éxito')
        return redirect('registro_visitantes')

    visitantes = Visitante.objects.filter(hora_salida__isnull=True)
    return render(request, 'core/registro_visitantes.html', {'visitantes': visitantes})


@login_required
def registro_vehiculos(request):
    """
    Maneja el registro de vehiculos.
    """
    if request.method == "POST":
        Vehiculo.objects.create(
            matricula=request.POST["matricula"],
            tipo_vehiculo=request.POST["tipo_vehiculo"],
            nombre_conductor=request.POST["nombre_conductor"],
            kilometraje_salida=request.POST["kilometraje_salida"],
            destino=request.POST["destino"],
            numero_personas=request.POST["numero_personas"],
        )
        messages.success(request, "Vehículo registrado con éxito")
        return redirect("registro_vehiculos")

    vehiculos = Vehiculo.objects.filter(hora_llegada__isnull=True)
    return render(request, "core/registro_vehiculos.html", {"vehiculos": vehiculos})


@login_required
def registro_proveedores(request):
    """
    Maneja el registro de proveedores.
    """
    if request.method == "POST":
        Proveedor.objects.create(
            run=request.POST["run"],
            nombre_conductor=request.POST["nombre_conductor"],
            nombre_empresa=request.POST["nombre_empresa"],
            domicilio=request.POST["domicilio"],
            tipo_vehiculo=request.POST["tipo_vehiculo"],
            matricula=request.POST["matricula"],
            guia_despacho=request.POST["guia_despacho"],
            encargado_recepcion=request.POST["encargado_recepcion"],
        )
        messages.success(request, "Proveedor registrado con éxito")
        return redirect("registro_proveedores")

    proveedores = Proveedor.objects.filter(hora_salida__isnull=True)
    return render(
        request, "core/registro_proveedores.html", {"proveedores": proveedores}
    )


@login_required
def gestion_permisos(request):
    """
    Maneja la gestion de permisos.
    """
    return render(request, "core/gestion_permisos.html")


@login_required
def registrar_salida_visitante(request, visitante_id):
    """
    Maneja el registro de salida visitantes.
    """
    visitante = Visitante.objects.get(id=visitante_id)
    visitante.hora_salida = timezone.now()
    visitante.save()
    messages.success(request, 'Salida de visitante registrada con éxito')
    return redirect('registro_visitantes')


@login_required
def registrar_llegada_vehiculo(request, vehiculo_id):
    """
    Maneja el registro de llegada vehiculos.
    """
    vehiculo = Vehiculo.objects.get(id=vehiculo_id)
    kilometraje_llegada = int(request.POST["kilometraje_llegada"])

    # Valida el kilometraje de llegada sea mayor que el de salida
    if kilometraje_llegada <= vehiculo.kilometraje_salida:
        messages.error(
            request, "El kilometraje de llegada debe ser mayor al kilometraje de salida"
        )
        return redirect("registro_vehiculos")

    vehiculo.hora_llegada = timezone.now()
    vehiculo.kilometraje_llegada = kilometraje_llegada
    vehiculo.save()
    messages.success(request, "Llegada de vehículo registrada con éxito")
    return redirect("registro_vehiculos")


@login_required
def registrar_salida_proveedor(request, proveedor_id):
    """
    Maneja el registro de salida proveedores.
    """
    proveedor = Proveedor.objects.get(id=proveedor_id)
    proveedor.hora_salida = timezone.now()
    proveedor.save()
    messages.success(request, "Salida de proveedor registrada con éxito")
    return redirect("registro_proveedores")


@login_required
def auditoria(request):
    """
    Maneja el registro de auditorias del sistema.
    """
    acciones = AuditoriaAccion.objects.all().order_by("-fecha_hora")

    filter_type = request.GET.get("filter_type")
    filter_value = request.GET.get("filter_value", "").strip()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Apply filters if provided
    if filter_type and filter_value:
        if filter_type == "run":
            acciones = acciones.filter(
                Q(accion__icontains=f"RUN: {filter_value}")
                | Q(accion__icontains=f"run: {filter_value}")
            )
        elif filter_type == "matricula":
            acciones = acciones.filter(
                Q(accion__icontains=f"matrícula: {filter_value}")
                | Q(accion__icontains=f"matricula: {filter_value}")
            )
        elif filter_type == "proveedor":
            acciones = acciones.filter(
                Q(accion__icontains=f"proveedor: {filter_value}")
                | Q(accion__icontains=f"empresa: {filter_value}")
            )
        elif filter_type == "usuario":
            acciones = acciones.filter(
                usuario__username__icontains=filter_value)

    # Apply date filters if provided
    if start_date:
        acciones = acciones.filter(fecha_hora__date__gte=start_date)
    if end_date:
        acciones = acciones.filter(fecha_hora__date__lte=end_date)

    context = {
        "acciones": acciones,
        "filter_type": filter_type,
        "filter_value": filter_value,
        "start_date": start_date,
        "end_date": end_date,
    }

    # Export to PDF
    if "export_pdf" in request.GET:
        html_string = render_to_string("core/auditoria_pdf.html", context)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="auditoria.pdf"'
        weasyprint.HTML(string=html_string).write_pdf(response)
        return response

    return render(request, "core/auditoria.html", context)
