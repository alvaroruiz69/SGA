# Generated by Django 4.2.16 on 2024-12-08 01:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_auditoriaaccion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditoriaaccion",
            name="fecha_hora",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
