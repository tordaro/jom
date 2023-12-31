# Generated by Django 5.0 on 2023-12-14 11:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChargingSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.UUIDField(verbose_name='ID')),
                ('user_full_name', models.CharField(max_length=100, verbose_name='User Full Name')),
                ('user_id', models.UUIDField(verbose_name='User ID')),
                ('user_name', models.EmailField(blank=True, max_length=254, null=True, verbose_name='User Name')),
                ('user_email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='User Email')),
                ('device_id', models.CharField(max_length=100, verbose_name='Device ID')),
                ('start_date_time', models.DateTimeField(verbose_name='Start Date Time')),
                ('end_date_time', models.DateTimeField(verbose_name='End Date Time')),
                ('energy', models.DecimalField(decimal_places=6, max_digits=8, verbose_name='Energy')),
                ('commit_metadata', models.IntegerField(blank=True, null=True, verbose_name='Commit Metadata')),
                ('commit_end_date_time', models.DateTimeField(blank=True, null=True, verbose_name='Commit End Date Time')),
                ('charger_id', models.UUIDField(verbose_name='Charger ID')),
                ('device_name', models.CharField(blank=True, max_length=100, verbose_name='Device Name')),
                ('externally_ended', models.BooleanField(blank=True, null=True, verbose_name='Externally Ended')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Charging Session',
                'verbose_name_plural': 'Charging Sessions',
                'db_table': 'charging_session',
                'ordering': ['start_date_time'],
            },
        ),
        migrations.CreateModel(
            name='EnergyDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('energy', models.DecimalField(decimal_places=6, max_digits=8, verbose_name='Energy')),
                ('timestamp', models.DateTimeField(verbose_name='Timestamp')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('charging_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='car_charging.chargingsession')),
            ],
            options={
                'verbose_name': 'Energy Detail',
                'verbose_name_plural': 'Energy Details',
                'db_table': 'energy_details',
                'ordering': ['timestamp'],
            },
        ),
    ]
