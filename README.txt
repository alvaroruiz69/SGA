Proyecto Django: SGA_Project

Este proyecto es una aplicación web desarrollada con Django y conectada a una base de datos MariaDB gestionada a través de XAMPP. 
El proyecto se desarrolla y gestiona en Visual Studio Code.

---

Prerrequisitos

- Python 3.11 o superior instalado.
- XAMPP con MariaDB (versión 10.4 o superior) instalado y en ejecución.
- Git instalado para gestionar el código con GitHub.
- Visual Studio Code como editor de desarrollo.

---

Configuración del Proyecto

Paso 1: Clonar el Proyecto desde GitHub

1. Abre una terminal en Visual Studio Code.
2. Clona el repositorio desde GitHub en tu máquina local:

   git clone https://github.com/alvaroruiz69/SGA.git

3. Cambia al directorio del proyecto:

   cd SGA_Project

Paso 2: Crear y Activar un Entorno Virtual

1. Crear el entorno virtual:

   python3 -m venv venv

2. Activar el entorno virtual:

   En macOS y Linux:

   source venv/bin/activate

   En Windows:

   .\venv\Scripts\activate

   Si el entorno virtual está activado correctamente, verás "(venv)" al inicio de la línea de comandos.

Paso 3: Instalar Dependencias

Con el entorno virtual activado, instala las dependencias del proyecto:

   pip install -r requirements.txt

Si el archivo requirements.txt no existe, puedes instalar las dependencias principales manualmente:

   pip install django pymysql

Nota: pymysql se usa como conector para MariaDB.

---

Configuración de la Base de Datos

Paso 4: Configurar la Conexión a la Base de Datos en Django

1. Asegúrate de que XAMPP esté en funcionamiento y que el servidor de base de datos MariaDB esté activo.
2. Edita el archivo settings.py de tu proyecto (SGA_Project/settings.py) para que la base de datos se configure así:

   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'sga_db', 
           'USER': 'root',
           'PASSWORD': 'L8xZ54dUk4p', 
           'HOST': 'localhost',
           'PORT': '3306',
           'OPTIONS': {
               'unix_socket': '/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock',
           },
       }
   }

Paso 5: Crear la Base de Datos (si no existe)

Accede a phpMyAdmin en http://localhost/phpmyadmin y crea la base de datos llamada sga_db 

---

Configuración de PyMySQL en Django

Paso 6: Configurar PyMySQL como Conector

En el archivo __init__.py de la carpeta del proyecto (SGA_Project/__init__.py), añade este código para que Django use PyMySQL:

   import pymysql
   pymysql.install_as_MySQLdb()

---

Inicialización de la Base de Datos

Paso 7: Ejecutar Migraciones de la Base de Datos

Este paso crea las tablas necesarias para el sistema de autenticación y administración de Django.

   python manage.py migrate

Paso 8: Crear un Superusuario para el Panel de Administración

Crea un superusuario para acceder al panel de administración de Django.

   python manage.py createsuperuser

Sigue las instrucciones y proporciona un nombre de usuario, correo electrónico y contraseña para el superusuario.

---

Ejecutar la Aplicación

Paso 9: Iniciar el Servidor de Desarrollo

Inicia el servidor de desarrollo de Django para verificar que todo esté funcionando correctamente:

   python manage.py runserver

Accede al servidor en http://127.0.0.1:8000/.

Paso 10: Acceder al Panel de Administración

1. Dirígete a http://127.0.0.1:8000/admin/.
2. Ingresa las credenciales del superusuario que creaste en el Paso 8.

---

Gestión del Proyecto con Git y GitHub

Realizar Cambios y Hacer Commit

1. Asegúrate de que el entorno virtual esté activado y que estés en el directorio del proyecto.
2. Realiza los cambios necesarios en el proyecto.
3. Usa git status para ver los cambios realizados:

   git status

4. Añadir los cambios para el commit:

   git add .

5. Hacer un commit con un mensaje descriptivo:

   git commit -m "Descripción breve del cambio"

Subir Cambios al Repositorio en GitHub

1. Subir los cambios al repositorio remoto en GitHub:

   git push


---

Comandos Útiles para el Desarrollo en Django

- Iniciar una nueva aplicación dentro del proyecto:

  python manage.py startapp <nombre_de_la_aplicacion>

- Aplicar migraciones (después de crear o modificar modelos):

  python manage.py makemigrations
  python manage.py migrate

- Crear un superusuario (si aún no lo has hecho):

  python manage.py createsuperuser

- Ejecutar pruebas:

  python manage.py test

- Salir del entorno virtual:

  deactivate

---

Solución de Problemas

- Problema: `zsh: command not found: python`
  - Solución: Usa python3 en lugar de python, o asegúrate de que el entorno virtual esté activado.

- Problema: Error de versión de MariaDB (MariaDB 10.5 or later is required)
  - Solución: Usa Django 4.x en lugar de Django 5 o instala MariaDB 10.5 o superior usando Homebrew.

---

Guía para iniciar aplicación Django (terminal):
Iniciar xampp 

cd SGA_Project
source venv/bin/activate
python manage.py runserver