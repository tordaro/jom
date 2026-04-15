from typing import Any, cast
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from car_charging.managers.cost_details_manager import CostDetailsManager


class CostDetails(models.Model):
    required_price_fields = ("spot_price", "grid_price", "usage_price", "spot_price_refund")

    objects = CostDetailsManager()
    energy_detail = models.OneToOneField("EnergyDetails", on_delete=models.CASCADE, primary_key=True)
    spot_price = models.ForeignKey("SpotPrice", on_delete=models.SET_NULL, null=True)
    grid_price = models.ForeignKey("GridPrice", on_delete=models.SET_NULL, null=True)
    usage_price = models.ForeignKey("UsagePrice", on_delete=models.SET_NULL, null=True)
    spot_price_refund = models.ForeignKey("SpotPriceRefund", on_delete=models.SET_NULL, null=True)

    session_id = models.IntegerField(_("Charging session"), editable=False)
    energy = models.DecimalField(_("Energy [kWh]"), editable=False, max_digits=10, decimal_places=6)
    timestamp = models.DateTimeField(verbose_name=_("Timestamp"), editable=False)
    price_area = models.IntegerField(_("Price area"), editable=False)
    spot_price_nok = models.DecimalField(_("Spot price per kWh [NOK/kWh]"), editable=False, max_digits=10, decimal_places=7)
    grid_price_nok = models.DecimalField(_("Grid price per kWh [NOK/kWh]"), editable=False, max_digits=10, decimal_places=7)
    usage_price_nok = models.DecimalField(_("Usage price per kWh [NOK/kWh]"), editable=False, max_digits=10, decimal_places=7)
    refund_price_nok = models.DecimalField(_("Refund per kWh [NOK/kWh]"), editable=False, max_digits=10, decimal_places=7)
    fund_price_nok = models.DecimalField(
        _("Energy fund price per kWh [NOK/kWh]"), editable=False, max_digits=10, decimal_places=7, default=Decimal(0.01)
    )  # Been the same since 2001
    user_full_name = models.CharField(verbose_name=_("User Full Name"), editable=False, max_length=100, blank=True)
    user_id = models.UUIDField(_("User ID"), editable=False, blank=True, null=True)

    spot_cost = models.DecimalField(_("Spot cost [NOK]"), editable=False, max_digits=11, decimal_places=7)
    grid_cost = models.DecimalField(_("Grid cost [NOK]"), editable=False, max_digits=11, decimal_places=7)
    usage_cost = models.DecimalField(_("Usage cost [NOK]"), editable=False, max_digits=11, decimal_places=7)
    fund_cost = models.DecimalField(_("Fund cost [NOK]"), editable=False, max_digits=11, decimal_places=7)
    refund = models.DecimalField(_("Refund [NOK]"), editable=False, max_digits=11, decimal_places=7)
    total_cost = models.DecimalField(_("Total cost [NOK]"), editable=False, max_digits=11, decimal_places=7)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def _validation_context(self) -> str:
        if getattr(self, "energy_detail", None) is None:
            return "energy_detail=<missing>"

        return (
            f"energy_detail={self.energy_detail_id}, "
            f"timestamp={self.energy_detail.timestamp}, "
            f"price_area={self.energy_detail.charging_session.price_area}"
        )

    def validate_energy_detail(self) -> None:
        if getattr(self, "energy_detail", None) is None:
            raise ValidationError({"energy_detail": "CostDetails requires an energy_detail before it can be calculated."})

    def validate_required_prices(self) -> None:
        validation_errors: dict[str, list[str]] = {}

        for field_name in self.required_price_fields:
            if getattr(self, f"{field_name}_id") is None:
                validation_errors[field_name] = [f"Missing required price for {field_name} ({self._validation_context()})."]

        if validation_errors:
            raise ValidationError(cast(Any, validation_errors))

    def clean(self) -> None:
        super().clean()
        self.validate_energy_detail()
        self.validate_required_prices()

    def populate_from_energy_detail(self) -> None:
        self.set_session_id()
        self.set_energy()
        self.set_timestamp()
        self.set_price_area()
        self.set_user()

    def calculate_costs(self) -> None:
        self.set_spot_price_nok()
        self.set_grid_price_nok()
        self.set_usage_price_nok()
        self.set_refund_price_nok()
        self.set_spot_cost()
        self.set_grid_cost()
        self.set_usage_cost()
        self.set_fund_cost()
        self.set_refund()
        self.set_total_cost()

    def set_session_id(self) -> None:
        self.session_id = self.energy_detail.charging_session.id

    def set_energy(self) -> None:
        self.energy = self.energy_detail.energy

    def set_timestamp(self) -> None:
        self.timestamp = self.energy_detail.timestamp

    def set_price_area(self) -> None:
        self.price_area = self.energy_detail.charging_session.price_area

    def set_spot_price_nok(self) -> None:
        self.spot_price_nok = self.spot_price.get_price(self.timestamp, self.price_area)

    def set_grid_price_nok(self) -> None:
        self.grid_price_nok = self.grid_price.get_price(self.timestamp)

    def set_usage_price_nok(self) -> None:
        self.usage_price_nok = self.usage_price.get_price(self.timestamp)

    def set_refund_price_nok(self) -> None:
        self.refund_price_nok = self.spot_price_refund.calculate_refund_price(self.timestamp, self.spot_price_nok)

    def set_user(self) -> None:
        self.user_id = self.energy_detail.charging_session.user_id
        self.user_full_name = self.energy_detail.charging_session.user_full_name

    def set_grid_cost(self) -> None:
        self.grid_cost = self.energy * self.grid_price_nok

    def set_spot_cost(self) -> None:
        self.spot_cost = self.energy * self.spot_price_nok

    def set_usage_cost(self) -> None:
        self.usage_cost = self.energy * self.usage_price_nok

    def set_fund_cost(self) -> None:
        self.fund_cost = self.energy * self.fund_price_nok

    def set_refund(self) -> None:
        self.refund = self.energy * self.refund_price_nok

    def set_total_cost(self) -> None:
        self.total_cost = self.grid_cost + self.spot_cost + self.usage_cost + self.fund_cost - self.refund

    def save(self, *args, **kwargs):
        self.validate_energy_detail()
        self.populate_from_energy_detail()
        self.clean()
        self.calculate_costs()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.energy_detail.id)

    class Meta:
        db_table = "cost_details"
        verbose_name = _("Cost detail")
        verbose_name_plural = _("Cost details")
