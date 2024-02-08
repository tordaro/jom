# Generated by Django 5.0 on 2024-01-30 15:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("car_charging", "0005_chargingsession_price_area"),
    ]

    operations = [
        migrations.AddField(
            model_name="energydetails",
            name="spot_price",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="car_charging.spotprices"),
        ),
    ]
