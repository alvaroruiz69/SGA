"""
Este módulo contiene las vistas para manejar las funcionalidades de la aplicación 'core'.
"""
# pylint: disable=import-error

import re
from datetime import datetime

import weasyprint
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import CSS, HTML

from core.models import Proveedor, Vehiculo, Visitante

from .models import Proveedor, Vehiculo, Visitante

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
    Maneja el registro de visitantes con registro en la auditoría.
    """
    if request.method == "POST":
        # Obtener y limpiar los datos del formulario
        run = request.POST.get("run", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        apellidos = request.POST.get("apellidos", "").strip()
        numero_tarjeta = request.POST.get("numero_tarjeta", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        motivo_visita = request.POST.get("motivo_visita", "").strip()
        observaciones = request.POST.get("observaciones", "").strip()

        # Validación del RUN: calcular dígito verificador si no está
        if "-" not in run:
            cuerpo = run[:-1] if len(run) > 1 else run
            dv_calculado = calcular_dv(cuerpo)
            run = f"{cuerpo}-{dv_calculado}"

        if not re.match(r"^\d{7,8}-[kK\d]{1}$", run):
            messages.error(
                request, "RUN inválido. Formato correcto: 12345678-9."
            )
            return redirect("registro_visitantes")

        # Validaciones adicionales
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre):
            messages.error(request, "El nombre solo debe contener letras.")
            return redirect("registro_visitantes")

        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", apellidos):
            messages.error(
                request, "Los apellidos solo deben contener letras.")
            return redirect("registro_visitantes")

        if not re.match(r"^\d+$", numero_tarjeta):
            messages.error(
                request, "El número de tarjeta debe contener solo números."
            )
            return redirect("registro_visitantes")

        if not re.match(r"^[a-zA-Z0-9\s]+$", direccion):
            messages.error(
                request, "La dirección solo debe contener letras y números."
            )
            return redirect("registro_visitantes")

        if not re.match(r"^[a-zA-Z0-9\s]+$", motivo_visita):
            messages.error(
                request, "El motivo de visita solo debe contener letras y números."
            )
            return redirect("registro_visitantes")

        if observaciones and not re.match(r"^[a-zA-Z0-9\s]+$", observaciones):
            messages.error(
                request, "Las observaciones solo deben contener letras y números."
            )
            return redirect("registro_visitantes")

        # Guardar visitante
        visitante = Visitante.objects.create(  # Ahora almacenamos la instancia en "visitante"
            run=run,
            nombre=nombre,
            apellidos=apellidos,
            numero_tarjeta=numero_tarjeta,
            direccion=direccion,
            motivo_visita=motivo_visita,
            observaciones=observaciones,
            hora_entrada=timezone.now(),
        )

        messages.success(request, "Visitante registrado con éxito.")
        return redirect("registro_visitantes")

    # Recuperar visitantes actuales
    visitantes = Visitante.objects.filter(hora_salida__isnull=True)
    return render(request, "core/registro_visitantes.html", {"visitantes": visitantes})


def calcular_dv(run):
    """
    Calcula el dígito verificador para un RUN dado.
    """
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


@login_required
def get_visitor_data(request):
    """
    Recupera datos del visitante por RUN.
    """
    run = request.GET.get("run", "").strip()
    visitante = Visitante.objects.filter(
        run=run).order_by("-hora_entrada").first()

    if visitante:
        return JsonResponse({
            "exists": True,
            "nombre": visitante.nombre,
            "apellidos": visitante.apellidos,
            "direccion": visitante.direccion,
        })

    return JsonResponse({"exists": False})


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
        matricula = request.POST["matricula"].strip()
        tipo_vehiculo = request.POST["tipo_vehiculo"].strip()
        nombre_conductor = request.POST["nombre_conductor"].strip()
        kilometraje_salida = request.POST["kilometraje_salida"].strip()
        destino = request.POST["destino"].strip()
        numero_personas = request.POST["numero_personas"].strip()

        # Validación de campos
        if len(matricula) > 6 or not re.match(r"^[A-Za-z0-9]+$", matricula):
            messages.error(
                request, "Máximo 6 caracteres y solo letras y números."
            )
            return redirect("registro_vehiculos")

        if not tipo_vehiculo.isalpha():
            messages.error(
                request, "Ingrese solo letras."
            )
            return redirect("registro_vehiculos")

        if not nombre_conductor.replace(" ", "").isalnum():
            messages.error(
                request, "Solo ingrese letras y números."
            )
            return redirect("registro_vehiculos")

        if not kilometraje_salida.isdigit():
            messages.error(
                request, "Ingrese solo números."
            )
            return redirect("registro_vehiculos")

        if not re.match(r"^[a-zA-Z0-9\s]+$", destino):
            messages.error(
                request, "Solo ingrese letras y números."
            )
            return redirect("registro_vehiculos")

        if not numero_personas.isdigit():
            messages.error(
                request, "Ingrese solo números."
            )
            return redirect("registro_vehiculos")

        # Guardar el vehículo
        try:
            # Crear un nuevo vehículo y guardar la instancia
            vehiculo = Vehiculo.objects.create(
                matricula=matricula,
                tipo_vehiculo=tipo_vehiculo,
                nombre_conductor=nombre_conductor,
                kilometraje_salida=int(kilometraje_salida),
                destino=destino,
                numero_personas=int(numero_personas),
                hora_salida=timezone.now(),  # Se guarda la hora de salida actual
            )

            messages.success(request, "Vehículo registrado con éxito.")
        except IntegrityError:
            messages.error(
                request, "Error al registrar el vehículo. Intente nuevamente."
            )
        return redirect("registro_vehiculos")

    # Obtener vehículos que no tienen una llegada registrada
    vehiculos = Vehiculo.objects.filter(hora_llegada__isnull=True)
    return render(request, "core/registro_vehiculos.html", {"vehiculos": vehiculos})


@ login_required
def registrar_llegada_vehiculo(request, vehiculo_id):
    """
    Maneja el registro de llegada de vehículos.
    """
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)

    if request.method == "POST":
        kilometraje_llegada = request.POST.get(
            "kilometraje_llegada", "").strip()

        if not kilometraje_llegada.isdigit():
            messages.error(
                request, "El kilometraje de llegada debe ser un número."
            )
            return redirect("registro_vehiculos")

        # Validar que el kilometraje de llegada sea mayor al de salida
        if int(kilometraje_llegada) <= vehiculo.kilometraje_salida:
            messages.error(
                request, "El kilometraje de llegada debe ser mayor al de salida."
            )
            return redirect("registro_vehiculos")

        # Registrar llegada
        vehiculo.kilometraje_llegada = int(kilometraje_llegada)
        vehiculo.hora_llegada = timezone.now()
        vehiculo.save()

        messages.success(request, "Llegada del vehículo registrada con éxito.")
        return redirect("registro_vehiculos")


@ login_required
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
        })
    else:
        return JsonResponse({'exists': False})

#
# Vistas de registro de proveedores
#


@ login_required
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


@ login_required
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


@ login_required
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
    filter_type = request.GET.get("filter_type")
    filter_value = request.GET.get("filter_value", "").strip()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    resultados = []
    columnas = []
    modelo = ""

    if start_date and end_date:
        if filter_type == "visitante":
            queryset = Visitante.objects.filter(
                hora_entrada__date__range=[start_date, end_date]
            )
            if filter_value:
                queryset = queryset.filter(run__icontains=filter_value)
            columnas = ["RUN", "Nombre", "Apellidos", "Número de Tarjeta", "Dirección",
                        "Motivo de Visita", "Observaciones", "Hora de Entrada", "Hora de Salida"]
            modelo = "Visitantes"
            resultados = list(queryset.values(
                'run', 'nombre', 'apellidos', 'numero_tarjeta', 'direccion',
                'motivo_visita', 'observaciones', 'hora_entrada', 'hora_salida'
            ))

        elif filter_type == "vehiculo":
            queryset = Vehiculo.objects.filter(
                hora_salida__date__range=[start_date, end_date]
            )
            if filter_value:
                queryset = queryset.filter(matricula__icontains=filter_value)
            columnas = ["Matrícula", "Tipo de Vehículo", "Nombre del Conductor", "Kilometraje de Salida",
                        "Destino", "Número de Personas", "Hora de Salida", "Hora de Llegada"]
            modelo = "Vehículos"
            resultados = list(queryset.values(
                'matricula', 'tipo_vehiculo', 'nombre_conductor', 'kilometraje_salida',
                'destino', 'numero_personas', 'hora_salida', 'hora_llegada'
            ))

        elif filter_type == "proveedor":
            queryset = Proveedor.objects.filter(
                hora_ingreso__date__range=[start_date, end_date]
            )
            if filter_value:
                queryset = queryset.filter(Q(run__icontains=filter_value) | Q(
                    nombre_empresa__icontains=filter_value))
            columnas = ["RUN", "Nombre del Conductor", "Nombre de la Empresa", "Domicilio", "Tipo de Vehículo",
                        "Matrícula", "Guía de Despacho", "Encargado de Recepción", "Hora de Ingreso", "Hora de Salida"]
            modelo = "Proveedores"
            resultados = list(queryset.values(
                'run', 'nombre_conductor', 'nombre_empresa', 'domicilio',
                'tipo_vehiculo', 'matricula', 'guia_despacho',
                'encargado_recepcion', 'hora_ingreso', 'hora_salida'
            ))

        elif filter_type == "usuario":
            queryset = User.objects.filter(
                date_joined__date__range=[start_date, end_date]
            )
            if filter_value:
                queryset = queryset.filter(username__icontains=filter_value)
            columnas = ["Usuario", "Nombre Completo",
                        "Email", "Fecha de Ingreso"]
            modelo = "Usuarios"
            resultados = list(queryset.values(
                'username', 'first_name', 'last_name', 'email', 'date_joined'
            ))

    # Generar PDF si se solicita
    if "export_pdf" in request.GET:
        context = {
            "resultados": resultados,
            "columnas": columnas,
            "modelo": modelo,
            "filter_type": filter_type,
            "filter_value": filter_value,
            "start_date": start_date,
            "end_date": end_date,
            "user": request.user,
            "now": timezone.now(),
        }
        html_string = render_to_string("core/auditoria_pdf.html", context)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte_auditoria.pdf"'

        css = CSS(string="""
            @page {
                size: landscape;
                margin: 10px;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                font-size: 11px;
            }
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
        """)

        HTML(string=html_string).write_pdf(response, stylesheets=[css])
        return response

    context = {
        "resultados": resultados,
        "columnas": columnas,
        "modelo": modelo,
        "filter_type": filter_type,
        "filter_value": filter_value,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "core/auditoria.html", context)


#
# Gestion de permisos usuarios del sistema
#

def is_auditor(user):
    return user.groups.filter(name='Auditor').exists()


def is_security_personnel(user):
    return user.groups.filter(name='Seguridad').exists()


@login_required
def gestion_permisos(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # Validaciones del nombre de usuario
        if not re.match(r'^[a-zA-Z]+(\.[a-zA-Z]+){0,2}$', username):
            messages.error(
                request, "El usuario debe tener el formato nombre.apellido.apellido.")
            return redirect('gestion_permisos')

        # Validaciones de contraseña
        if len(password) < 10 or len(password) > 12 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(
                request, "La contraseña debe tener entre 10 y 12 caracteres, incluyendo mayúsculas, minúsculas, números y un carácter especial.")
            return redirect('gestion_permisos')

        # Crear usuario y asignar grupo
        try:
            user = User.objects.create_user(
                username=username, password=password)

            if role == "Auditor":
                group = Group.objects.get(name='Auditor')
            elif role == "Seguridad":
                group = Group.objects.get(name='Seguridad')
            else:
                messages.error(request, "El rol especificado no es válido.")
                return redirect('gestion_permisos')

            user.groups.add(group)
            messages.success(request, "Usuario creado con éxito.")
        except Group.DoesNotExist:
            messages.error(request, "El grupo especificado no existe.")
        except Exception as e:
            messages.error(request, f"Error al crear el usuario: {e}")

    # Listar usuarios sin incluir el grupo Admin
    users = User.objects.exclude(groups__name='Admin')
    paginator = Paginator(users, 10)  # Mostrar 10 usuarios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "core/gestion_permisos.html", {
        "page_obj": page_obj,
    })


@login_required
def editar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        user.username = username
        if password:
            user.set_password(password)
        user.save()

        # Actualizar grupos
        user.groups.clear()
        if role == "Auditor":
            group = Group.objects.get(name='Auditor')
            user.groups.add(group)
        elif role == "Seguridad":
            group = Group.objects.get(name='Seguridad')
            user.groups.add(group)

        messages.success(request, "Usuario editado con éxito.")
        return redirect('gestion_permisos')

    return render(request, "core/gestion_permisos.html", {"selected_user": user})
