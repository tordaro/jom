# Generated by Django 5.0.4 on 2024-05-07 13:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("car_charging", "0012_alter_spotprice_start_time_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="spotprice",
            index=models.Index(fields=["start_time"], name="spot_price_start_t_8abc5c_idx"),
        ),
        migrations.AddIndex(
            model_name="spotprice",
            index=models.Index(fields=["price_area"], name="spot_price_price_a_9bdecc_idx"),
        ),
        migrations.AddIndex(
            model_name="spotprice",
            index=models.Index(fields=["start_time", "price_area"], name="spot_price_start_t_675c7f_idx"),
        ),
    ]
