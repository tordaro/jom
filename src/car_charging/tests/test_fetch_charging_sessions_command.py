from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase
from django.utils.timezone import datetime, make_aware


class FetchChargingSessionsCommandTests(SimpleTestCase):
    @patch("car_charging.management.commands.fetch_charging_sessions.zts.create_charging_sessions")
    @patch("car_charging.management.commands.fetch_charging_sessions.zts.get_charge_history_data")
    def test_command_calls_service_with_inclusive_end_date(self, mock_get_charge_history_data, mock_create_charging_sessions):
        mock_get_charge_history_data.return_value = [{"id": "session"}]

        call_command("fetch_charging_sessions", "01-01-2025", "02-01-2025")

        mock_get_charge_history_data.assert_called_once_with(
            make_aware(datetime(2025, 1, 1, 0, 0, 0)),
            make_aware(datetime(2025, 1, 3, 0, 0, 0)),
        )
        mock_create_charging_sessions.assert_called_once_with([{"id": "session"}])

    def test_command_rejects_invalid_date_range(self):
        with self.assertRaisesMessage(CommandError, "End date must be later than or equal to start date."):
            call_command("fetch_charging_sessions", "02-01-2025", "01-01-2025")
