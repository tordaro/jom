# Generated by Django 5.0 on 2024-02-09 14:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("car_charging", "0007_alter_chargingsession_energy_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="spotprices",
            name="end_time",
            field=models.DateTimeField(null=True, verbose_name="End time"),
        ),
    ]
