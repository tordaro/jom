from datetime import timedelta
from django.utils.timezone import datetime, make_aware
from django.core.management.base import BaseCommand, CommandError, CommandParser

from car_charging.cost_services import create_cost_details


class Command(BaseCommand):
    help = "Create or update cost details for an optional inclusive date range."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("-s", "--start-date", type=lambda d: datetime.strptime(d, "%d-%m-%Y"), help="Start date, inclusive (dd-mm-YYYY).")
        parser.add_argument("-e", "--end-date", type=lambda d: datetime.strptime(d, "%d-%m-%Y"), help="End date, inclusive (dd-mm-YYYY).")

    def handle(self, *args, **options) -> None:
        start_date = None
        end_date_exclusive = None

        if options.get("start_date"):
            start_date = make_aware(options["start_date"])
        if options.get("end_date"):
            end_date_exclusive = make_aware(options["end_date"]) + timedelta(days=1)

        if start_date and end_date_exclusive and end_date_exclusive <= start_date:
            raise CommandError("End date must be later than or equal to start date.")

        create_cost_details(from_date=start_date, to_date=end_date_exclusive)
