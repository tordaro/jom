from django.db import models
from django.utils.translation import gettext_lazy as _

class ChargingSession(models.Model):
    session_id = models.UUIDField(verbose_name=_("ID"))
    user_full_name = models.CharField(max_length=100, verbose_name=_("User Full Name"))
    user_id = models.UUIDField(verbose_name=_("User ID"))
    user_name = models.EmailField(verbose_name=_("User Name"), blank=True, null=True)
    user_email = models.EmailField(verbose_name=_("User Email"), blank=True, null=True)
    device_id = models.CharField(max_length=100, verbose_name=_("Device ID"))
    start_date_time = models.DateTimeField(verbose_name=_("Start Date Time"))
    end_date_time = models.DateTimeField(verbose_name=_("End Date Time"))
    energy = models.DecimalField(max_digits=8, decimal_places=6, verbose_name=_("Energy"))
    commit_metadata = models.IntegerField(verbose_name=_("Commit Metadata"), blank=True, null=True)
    commit_end_date_time = models.DateTimeField(verbose_name=_("Commit End Date Time"), blank=True, null=True)
    charger_id = models.UUIDField(verbose_name=_("Charger ID"))
    device_name = models.CharField(max_length=100, verbose_name=_("Device Name"), blank=True)
    externally_ended = models.BooleanField(verbose_name=_("Externally Ended"), blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'charging_session'
        ordering = ['start_date_time']
        verbose_name = _('Charging Session')
        verbose_name_plural = _('Charging Sessions')