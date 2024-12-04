"""
Este módulo contiene las vistas para manejar las funcionalidades de la aplicación 'core'.
"""
# pylint: disable=import-error

import re

import weasyprint
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from core.models import AuditoriaAccion, Proveedor, Vehiculo, Visitante

#
# Validación del general usuarios del sistema
#


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


#
# Funciones auxiliares para RUN
#

def validar_run(run):
    """
    Valida que el RUN siga el formato correcto: 12345678-9.
    """
    if not re.match(r"^\d{7,8}-[kK\d]{1}$", run):
        raise ValidationError(
            "Formato de RUN inválido. Formato correcto: 12345678-9."
        )


def calcular_dv(run):
    """
    Calcula el dígito verificador para un RUN dado (sin guion).
    """
    run = run.replace(".", "").strip()
    suma = 0
    factor = 2

    for digito in reversed(run):
        suma += int(digito) * factor
        factor = 9 if factor == 7 else factor + 1

    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


#
# gestion de visitantes del sistema
#


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
def registrar_salida_visitante(request, visitante_id):
    """
    Maneja el registro de salida visitantes.
    """
    visitante = Visitante.objects.get(id=visitante_id)
    visitante.hora_salida = timezone.now()
    visitante.save()
    messages.success(request, 'Salida de visitante registrada con éxito')
    return redirect('registro_visitantes')


#
# gestion de vehiculos del sistema
#

@login_required
def registro_vehiculos(request):
    """
    Maneja el registro de vehículos.
    """
    if request.method == "POST":
        matricula = request.POST["matricula"]
        tipo_vehiculo = request.POST["tipo_vehiculo"]
        nombre_conductor = request.POST["nombre_conductor"]
        kilometraje_salida = request.POST["kilometraje_salida"]
        destino = request.POST["destino"]
        numero_personas = request.POST["numero_personas"]

        # Validación de la matrícula
        if not Vehiculo.objects.filter(matricula=matricula).exists():
            messages.error(
                request, "La matrícula no existe en la base de datos.")
            return redirect("registro_vehiculos")

        # Validación de los campos
        if not tipo_vehiculo.isalpha():
            messages.error(
                request, "El tipo de vehículo solo debe contener letras.")
            return redirect("registro_vehiculos")

        if not nombre_conductor.replace(' ', '').isalnum():
            messages.error(
                request,
                "El nombre del conductor solo debe contener letras y números.")
            return redirect("registro_vehiculos")

        if not kilometraje_salida.isdigit():
            messages.error(
                request, "El kilometraje de salida debe ser un número.")
            return redirect("registro_vehiculos")

        if not numero_personas.isdigit():
            messages.error(
                request, "El número de personas debe ser un número.")
            return redirect("registro_vehiculos")

        if len(matricula) > 6 or not re.match(r'^[A-Za-z0-9]+$', matricula):
            messages.error(
                request, "La matrícula máximo de 6 caracteres y solo contener letras y números.")
            return redirect("registro_vehiculos")

        # Obtener el último kilometraje de llegada registrado para la matrícula
        try:
            ultimo_vehiculo = Vehiculo.objects.filter(
                matricula=matricula).order_by('-hora_llegada').first()
            if ultimo_vehiculo:
                kilometraje_salida = ultimo_vehiculo.kilometraje_llegada
            else:
                messages.error(
                    request, "No se encontró un registro de llegada para esta matrícula.")
                return redirect("registro_vehiculos")

            # Crear nuevo vehículo
            Vehiculo.objects.create(
                matricula=matricula,
                tipo_vehiculo=tipo_vehiculo,
                nombre_conductor=nombre_conductor,
                kilometraje_salida=kilometraje_salida,
                destino=destino,
                numero_personas=numero_personas,
            )
            messages.success(request, "Vehículo registrado con éxito")
            return redirect("registro_vehiculos")

        except IntegrityError:
            messages.error(
                request, "Error al registrar el vehículo. Intente nuevamente.")
            return redirect("registro_vehiculos")

    vehiculos = Vehiculo.objects.filter(hora_llegada__isnull=True)
    return render(request, "core/registro_vehiculos.html", {"vehiculos": vehiculos})


@login_required
def registrar_llegada_vehiculo(request, vehiculo_id):
    """
    Maneja el registro de llegada de vehículos.
    """
    vehiculo = Vehiculo.objects.get(id=vehiculo_id)
    # Asigna la hora actual como hora de llegada
    vehiculo.hora_llegada = timezone.now()
    vehiculo.save()
    messages.success(request, 'Llegada de vehículo registrada con éxito')
    return redirect('registro_vehiculos')


@login_required
def get_vehicle_data(request):
    """
    Maneja la búsqueda de vehículos por matrícula.
    """
    matricula = request.GET.get('matricula')
    vehiculo = Vehiculo.objects.filter(matricula=matricula).first()

    if vehiculo:
        # Obtener el último kilometraje de llegada registrado para la matrícula
        ultimo_kilometraje = vehiculo.kilometraje_llegada if vehiculo.kilometraje_llegada is not None else 0

        return JsonResponse({
            'exists': True,
            'tipo_vehiculo': vehiculo.tipo_vehiculo,
            'kilometraje_salida': ultimo_kilometraje,
            'destino': vehiculo.destino,
            'numero_personas': vehiculo.numero_personas,
        })
    else:
        return JsonResponse({'exists': False})

#
# Vistas de registro de proveedores
#


@login_required
def registro_proveedores(request):
    """
    Maneja el registro de proveedores con validación de RUN, autocompletado de datos y generación automática de guion.
    """
    if request.method == "POST":
        # Obtener y limpiar el RUN ingresado
        run = request.POST.get("run", "").strip()

        # Generar guion y dígito verificador automáticamente si no están presentes
        if "-" not in run:
            dv = calcular_dv(run)
            run = f"{run}-{dv}"

        # Validar el formato del RUN
        try:
            validar_run(run)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect("registro_proveedores")

        # Validar los demás campos
        nombre_conductor = request.POST["nombre_conductor"]
        nombre_empresa = request.POST["nombre_empresa"]
        domicilio = request.POST["domicilio"]
        tipo_vehiculo = request.POST["tipo_vehiculo"]
        matricula = request.POST["matricula"]
        guia_despacho = request.POST["guia_despacho"]
        encargado_recepcion = request.POST["encargado_recepcion"]

        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre_conductor):
            messages.error(
                request, "El nombre del conductor solo debe contener letras.")
            return redirect("registro_proveedores")

        if not re.match(r"^[a-zA-Z0-9\s]+$", nombre_empresa):
            messages.error(
                request, "El nombre de la empresa solo debe contener letras y números.")
            return redirect("registro_proveedores")

        if not re.match(r"^[a-zA-Z0-9\s]+$", domicilio):
            messages.error(
                request, "El domicilio solo debe contener letras y números.")
            return redirect("registro_proveedores")

        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", tipo_vehiculo):
            messages.error(
                request, "El tipo de vehículo solo debe contener letras.")
            return redirect("registro_proveedores")

        if not re.match(r"^[A-Za-z0-9]+$", matricula):
            messages.error(
                request, "La matrícula solo debe contener letras y números.")
            return redirect("registro_proveedores")

        if not re.match(r"^\d+$", guia_despacho):
            messages.error(
                request, "La guía de despacho solo debe contener números.")
            return redirect("registro_proveedores")

        if not re.match(r"^[a-zA-Z\s]+$", encargado_recepcion):
            messages.error(
                request, "El encargado de recepción solo debe contener letras.")
            return redirect("registro_proveedores")

        # Registrar proveedor
        try:
            Proveedor.objects.create(
                run=run,
                nombre_conductor=nombre_conductor,
                nombre_empresa=nombre_empresa,
                domicilio=domicilio,
                tipo_vehiculo=tipo_vehiculo,
                matricula=matricula,
                guia_despacho=guia_despacho,
                encargado_recepcion=encargado_recepcion,
            )
            messages.success(request, "Proveedor registrado con éxito.")
        except Exception as e:
            messages.error(request, f"Error al registrar proveedor: {e}")
        return redirect("registro_proveedores")

    # Manejo de la búsqueda de un proveedor existente (GET para autocompletar datos)
    if request.method == "GET" and "run" in request.GET:
        run = request.GET.get("run", "").strip()
        proveedor = Proveedor.objects.filter(run=run).first()
        if proveedor:
            return JsonResponse({
                "exists": True,
                "nombre_conductor": proveedor.nombre_conductor,
                "nombre_empresa": proveedor.nombre_empresa,
                "domicilio": proveedor.domicilio,
                "tipo_vehiculo": proveedor.tipo_vehiculo,
                "matricula": proveedor.matricula,
                "guia_despacho": proveedor.guia_despacho,
                "encargado_recepcion": proveedor.encargado_recepcion,
            })
        return JsonResponse({"exists": False})

    # Mostrar lista de proveedores actuales
    proveedores = Proveedor.objects.filter(hora_salida__isnull=True)
    return render(request, "core/registro_proveedores.html", {"proveedores": proveedores})


@login_required
def get_provider_data(request):
    """
    Endpoint para buscar datos de un proveedor por RUN.
    """
    run = request.GET.get('run', '').strip()
    if not run:
        return JsonResponse({'error': 'RUN es obligatorio'}, status=400)

    proveedor = Proveedor.objects.filter(run=run).first()
    if proveedor:
        return JsonResponse({
            'exists': True,
            'nombre_conductor': proveedor.nombre_conductor,
            'nombre_empresa': proveedor.nombre_empresa,
            'domicilio': proveedor.domicilio,
            'tipo_vehiculo': proveedor.tipo_vehiculo,
            'matricula': proveedor.matricula,
            'guia_despacho': proveedor.guia_despacho,
            'encargado_recepcion': proveedor.encargado_recepcion,
        })
    return JsonResponse({'exists': False})


@login_required
def registrar_salida_proveedor(request, proveedor_id):
    """
    Maneja el registro de salida de proveedores.
    """
    proveedor = Proveedor.objects.get(id=proveedor_id)
    proveedor.hora_salida = timezone.now()
    proveedor.save()
    messages.success(request, "Salida de proveedor registrada con éxito.")
    return redirect("registro_proveedores")

#
# Gestion de auditorias del sistema
#


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

    # Exporta a PDF
    if "export_pdf" in request.GET:
        html_string = render_to_string("core/auditoria_pdf.html", context)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="auditoria.pdf"'
        weasyprint.HTML(string=html_string).write_pdf(response)
        return response

    return render(request, "core/auditoria.html", context)
#
# Gestion de permisos usuarios del sistema
#


@login_required
def gestion_permisos(request):
    """
    Maneja la gestion de permisos.
    """
    return render(request, "core/gestion_permisos.html")
