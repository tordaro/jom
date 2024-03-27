# Generated by Django 5.0 on 2024-03-27 22:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("car_charging", "0008_alter_spotprices_end_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="energydetails",
            name="cost",
            field=models.DecimalField(decimal_places=6, editable=False, max_digits=8, null=True, verbose_name="Cost [kr]"),
        ),
    ]
