from datetime import date, datetime
from typing import Never
from django.core.exceptions import ValidationError

from car_charging.models import SpotPrice, GridPrice, CostDetails, EnergyDetails, UsagePrice, SpotPriceRefund


def _raise_missing_price(price_name: str, energy_detail: EnergyDetails, lookup_value: object) -> Never:
    raise ValidationError(
        f"Missing {price_name} for EnergyDetails {energy_detail.id} at {energy_detail.timestamp} " f"with lookup value {lookup_value}."
    )


def _get_spot_price(energy_detail: EnergyDetails, cache: dict[tuple[int, datetime], SpotPrice | None]) -> SpotPrice:
    hourly_timestamp = energy_detail.get_hourly_timestamp()
    price_area = energy_detail.charging_session.price_area
    cache_key = (price_area, hourly_timestamp)

    if cache_key not in cache:
        cache[cache_key] = SpotPrice.objects.filter(price_area=price_area, start_time=hourly_timestamp).order_by("-start_time").first()

    spot_price = cache[cache_key]
    if spot_price is None:
        _raise_missing_price("SpotPrice", energy_detail, cache_key)
    return spot_price


def _get_grid_price(energy_detail: EnergyDetails, cache: dict[date, GridPrice | None]) -> GridPrice:
    target_date = energy_detail.timestamp.date()

    if target_date not in cache:
        cache[target_date] = GridPrice.objects.filter(start_date__lte=target_date).order_by("-start_date").first()

    grid_price = cache[target_date]
    if grid_price is None:
        _raise_missing_price("GridPrice", energy_detail, target_date)
    return grid_price


def _get_usage_price(energy_detail: EnergyDetails, cache: dict[date, UsagePrice | None]) -> UsagePrice:
    target_date = energy_detail.timestamp.date()

    if target_date not in cache:
        cache[target_date] = UsagePrice.objects.filter(start_date__lte=target_date).order_by("-start_date").first()

    usage_price = cache[target_date]
    if usage_price is None:
        _raise_missing_price("UsagePrice", energy_detail, target_date)
    return usage_price


def _get_refund_price(energy_detail: EnergyDetails, cache: dict[date, SpotPriceRefund | None]) -> SpotPriceRefund:
    target_date = energy_detail.timestamp.date()

    if target_date not in cache:
        cache[target_date] = SpotPriceRefund.objects.filter(start_date__lte=target_date).order_by("-start_date").first()

    refund_price = cache[target_date]
    if refund_price is None:
        _raise_missing_price("SpotPriceRefund", energy_detail, target_date)
    return refund_price


def create_cost_details(from_date: datetime | None = None, to_date: datetime | None = None) -> None:
    energy_details = EnergyDetails.objects.all().select_related("charging_session")

    if from_date:
        energy_details = energy_details.filter(timestamp__gte=from_date)
    if to_date:
        energy_details = energy_details.filter(timestamp__lt=to_date)
    energy_details = energy_details.order_by("timestamp", "id")

    spot_price_cache: dict[tuple[int, datetime], SpotPrice | None] = {}
    grid_price_cache: dict[date, GridPrice | None] = {}
    usage_price_cache: dict[date, UsagePrice | None] = {}
    refund_price_cache: dict[date, SpotPriceRefund | None] = {}

    for energy_detail in energy_details:
        spot_price = _get_spot_price(energy_detail, spot_price_cache)
        grid_price = _get_grid_price(energy_detail, grid_price_cache)
        usage_price = _get_usage_price(energy_detail, usage_price_cache)
        refund_price = _get_refund_price(energy_detail, refund_price_cache)

        cost_detail = CostDetails.objects.filter(energy_detail=energy_detail).first()
        if cost_detail is None:
            CostDetails.objects.create(
                energy_detail=energy_detail,
                spot_price=spot_price,
                grid_price=grid_price,
                usage_price=usage_price,
                spot_price_refund=refund_price,
            )
            continue

        cost_detail.spot_price = spot_price
        cost_detail.grid_price = grid_price
        cost_detail.usage_price = usage_price
        cost_detail.spot_price_refund = refund_price
        cost_detail.save()
