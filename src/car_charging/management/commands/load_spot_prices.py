import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandParser

from car_charging.fbr_services import load_spot_prices

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "Load spot price data from https://www.forbrukerradet.no/strompris/spotpriser."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("file_path", type=Path, help="Path to the Excel file containing spot price data.")

    def handle(self, *args, **options) -> None:
        load_spot_prices(options["file_path"])
