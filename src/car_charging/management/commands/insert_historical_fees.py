import logging
from django.utils.timezone import make_aware, datetime
from django.core.management.base import BaseCommand

from car_charging.models import GridPrice, UsagePrice, SpotPriceRefund

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "Convenience command that inserts historical fee prices for 01.01.2023 - 01.01.2026."

    def handle(self, *args, **options) -> None:
        GridPrice.objects.get_or_create(
            day_fee=0.199, night_fee=0.099, day_hour_from=6, night_hour_from=22, start_date=make_aware(datetime(2023, 1, 1))
        )
        GridPrice.objects.get_or_create(
            day_fee=0.231, night_fee=0.116, day_hour_from=6, night_hour_from=22, start_date=make_aware(datetime(2024, 1, 1))
        )
        # Grid price unchanged in 2025 and 2026, so no need to create new entries

        UsagePrice.objects.get_or_create(nok_pr_kwh=0.0916, start_date=make_aware(datetime(2023, 1, 1)))
        UsagePrice.objects.get_or_create(nok_pr_kwh=0.1584, start_date=make_aware(datetime(2023, 4, 1)))
        UsagePrice.objects.get_or_create(nok_pr_kwh=0.0951, start_date=make_aware(datetime(2024, 1, 1)))
        UsagePrice.objects.get_or_create(nok_pr_kwh=0.1644, start_date=make_aware(datetime(2024, 4, 1)))
        UsagePrice.objects.get_or_create(nok_pr_kwh=0.0979, start_date=make_aware(datetime(2025, 1, 1)))
        UsagePrice.objects.get_or_create(nok_pr_kwh=0.1693, start_date=make_aware(datetime(2025, 4, 1)))
        UsagePrice.objects.get_or_create(nok_pr_kwh=0.0713, start_date=make_aware(datetime(2026, 1, 1)))

        SpotPriceRefund.objects.get_or_create(deduction_threshold=0.0, reduction_factor=0.0, start_date=make_aware(datetime(2000, 1, 1)))
        SpotPriceRefund.objects.get_or_create(deduction_threshold=0.70, reduction_factor=0.9, start_date=make_aware(datetime(2023, 9, 1)))
        SpotPriceRefund.objects.get_or_create(deduction_threshold=0.73, reduction_factor=0.9, start_date=make_aware(datetime(2024, 1, 1)))
        SpotPriceRefund.objects.get_or_create(deduction_threshold=0.75, reduction_factor=0.9, start_date=make_aware(datetime(2025, 1, 1)))
        SpotPriceRefund.objects.get_or_create(deduction_threshold=0.77, reduction_factor=0.9, start_date=make_aware(datetime(2026, 1, 1)))
