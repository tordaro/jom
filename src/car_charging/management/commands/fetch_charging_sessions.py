import logging
from datetime import timedelta
from django.utils.timezone import datetime, make_aware
from django.core.management.base import BaseCommand, CommandError, CommandParser

import car_charging.zaptec_services as zts

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "Load charging sessions and energy details from the Zaptec API."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("start", type=lambda d: datetime.strptime(d, "%d-%m-%Y"), help="Start date, inclusive (dd-mm-YYYY).")
        parser.add_argument("end", type=lambda d: datetime.strptime(d, "%d-%m-%Y"), help="End date, inclusive (dd-mm-YYYY).")

    def handle(self, *args, **options) -> None:
        start_date = make_aware(options["start"])
        end_date_exclusive = make_aware(options["end"]) + timedelta(days=1)

        if end_date_exclusive <= start_date:
            raise CommandError("End date must be later than or equal to start date.")

        charging_data = zts.get_charge_history_data(start_date, end_date_exclusive)
        _ = zts.create_charging_sessions(charging_data)
