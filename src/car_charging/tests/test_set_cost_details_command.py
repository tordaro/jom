from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase
from django.utils.timezone import datetime, make_aware


class SetCostDetailsCommandTests(SimpleTestCase):
    @patch("car_charging.management.commands.set_cost_details.create_cost_details")
    def test_command_calls_service_with_inclusive_end_date(self, mock_create_cost_details):
        call_command("set_cost_details", "--start-date", "10-01-2025", "--end-date", "11-01-2025")

        mock_create_cost_details.assert_called_once_with(
            from_date=make_aware(datetime(2025, 1, 10, 0, 0, 0)),
            to_date=make_aware(datetime(2025, 1, 12, 0, 0, 0)),
        )

    @patch("car_charging.management.commands.set_cost_details.create_cost_details")
    def test_command_accepts_open_ended_range(self, mock_create_cost_details):
        call_command("set_cost_details", "--start-date", "10-01-2025")

        mock_create_cost_details.assert_called_once_with(
            from_date=make_aware(datetime(2025, 1, 10, 0, 0, 0)),
            to_date=None,
        )

    def test_command_rejects_invalid_date_range(self):
        with self.assertRaisesMessage(CommandError, "End date must be later than or equal to start date."):
            call_command("set_cost_details", "--start-date", "11-01-2025", "--end-date", "10-01-2025")
