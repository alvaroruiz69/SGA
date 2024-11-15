from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import AuditoriaAccion, Proveedor, Vehiculo, Visitante


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Credenciales inválidas')
    return render(request, 'core/login.html')

@login_required
def home(request):
    return render(request, 'core/home.html')

@login_required
def registro_visitantes(request):
    if request.method == 'POST':
        Visitante.objects.create(
            run=request.POST['run'],
            nombre=request.POST['nombre'],
            apellidos=request.POST['apellidos'],
            numero_tarjeta=request.POST['numero_tarjeta'],
            direccion=request.POST['direccion'],
            motivo_visita=request.POST['motivo_visita'],
            observaciones=request.POST['observaciones']
        )
        messages.success(request, 'Visitante registrado con éxito')
        return redirect('registro_visitantes')
    
    visitantes = Visitante.objects.filter(hora_salida__isnull=True)
    return render(request, 'core/registro_visitantes.html', {'visitantes': visitantes})

@login_required
def registro_vehiculos(request):
    if request.method == 'POST':
        Vehiculo.objects.create(
            matricula=request.POST['matricula'],
            tipo_vehiculo=request.POST['tipo_vehiculo'],
            nombre_conductor=request.POST['nombre_conductor'],
            kilometraje_salida=request.POST['kilometraje_salida'],
            destino=request.POST['destino'],
            numero_personas=request.POST['numero_personas']
        )
        messages.success(request, 'Vehículo registrado con éxito')
        return redirect('registro_vehiculos')
    
    vehiculos = Vehiculo.objects.filter(hora_llegada__isnull=True)
    return render(request, 'core/registro_vehiculos.html', {'vehiculos': vehiculos})

@login_required
def registro_proveedores(request):
    if request.method == 'POST':
        Proveedor.objects.create(
            run=request.POST['run'],
            nombre_conductor=request.POST['nombre_conductor'],
            nombre_empresa=request.POST['nombre_empresa'],
            domicilio=request.POST['domicilio'],
            tipo_vehiculo=request.POST['tipo_vehiculo'],
            matricula=request.POST['matricula'],
            guia_despacho=request.POST['guia_despacho'],
            encargado_recepcion=request.POST['encargado_recepcion']
        )
        messages.success(request, 'Proveedor registrado con éxito')
        return redirect('registro_proveedores')
    
    proveedores = Proveedor.objects.filter(hora_salida__isnull=True)
    return render(request, 'core/registro_proveedores.html', {'proveedores': proveedores})

@login_required
def gestion_permisos(request):
    return render(request, 'core/gestion_permisos.html')

@login_required
def auditoria(request):
    acciones = AuditoriaAccion.objects.all().order_by('-fecha_hora')
    return render(request, 'core/auditoria.html', {'acciones': acciones})

@login_required
def registrar_salida_visitante(request, visitante_id):
    visitante = Visitante.objects.get(id=visitante_id)
    visitante.hora_salida = timezone.now()
    visitante.save()
    messages.success(request, 'Salida de visitante registrada con éxito')
    return redirect('registro_visitantes')

@login_required
def registrar_llegada_vehiculo(request, vehiculo_id):
    vehiculo = Vehiculo.objects.get(id=vehiculo_id)
    vehiculo.hora_llegada = timezone.now()
    vehiculo.kilometraje_llegada = request.POST['kilometraje_llegada']
    vehiculo.save()
    messages.success(request, 'Llegada de vehículo registrada con éxito')
    return redirect('registro_vehiculos')

@login_required
def registrar_salida_proveedor(request, proveedor_id):
    proveedor = Proveedor.objects.get(id=proveedor_id)
    proveedor.hora_salida = timezone.now()
    proveedor.save()
    messages.success(request, 'Salida de proveedor registrada con éxito')
    return redirect('registro_proveedores')
