import uuid
from types import SimpleNamespace
from django.test import TestCase
from django.utils.timezone import datetime, make_aware
from unittest.mock import ANY, Mock, patch

import car_charging.zaptec_services as zts


class ZaptecServicesTests(TestCase):
    def setUp(self):
        self.charger_id = uuid.uuid4()
        self.device_id = uuid.uuid4()
        self.session_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        self.data = [
            {
                "ChargerId": str(self.charger_id),
                "CommitEndDateTime": "2022-01-01T00:00:00",
                "CommitMetadata": 5,
                "DeviceId": str(self.device_id),
                "DeviceName": "test_device_name",
                "Energy": 100.000,
                "ExternallyEnded": False,
                "Id": str(self.session_id),
                "StartDateTime": "2022-01-01T01:00:00",
                "EndDateTime": "2022-01-01T08:00:00",
                "UserEmail": "test@example.com",
                "UserFullName": "Test User",
                "UserId": str(self.user_id),
                "UserName": "test_user",
                "EnergyDetails": [
                    {
                        "Energy": 50,
                        "Timestamp": "2022-01-01T01:00:00+00:00",
                    },
                    {
                        "Energy": 40,
                        "Timestamp": "2022-01-01T01:30:00+00:00",
                    },
                ],
            },
        ]

    def test_create_charging_sessions(self):
        result = zts.create_charging_sessions(self.data)
        session = result[0]
        energy_details = session.energydetails_set.all()

        self.assertEqual(len(result), 1)
        self.assertEqual(session.charger_id, str(self.charger_id))
        self.assertEqual(session.commit_metadata, 5)
        self.assertEqual(session.device_id, str(self.device_id))
        self.assertEqual(session.device_name, "test_device_name")
        self.assertEqual(session.energy, 100.000)
        self.assertEqual(session.externally_ended, False)
        self.assertEqual(session.session_id, str(self.session_id))
        self.assertEqual(session.user_email, "test@example.com")
        self.assertEqual(session.user_full_name, "Test User")
        self.assertEqual(session.start_date_time, make_aware(datetime(2022, 1, 1, 2, 0, 0)))
        self.assertEqual(session.end_date_time, make_aware(datetime(2022, 1, 1, 9, 0, 0)))
        self.assertEqual(session.commit_end_date_time, make_aware(datetime(2022, 1, 1, 1, 0, 0)))
        self.assertEqual(session.user_id, str(self.user_id))
        self.assertEqual(session.user_name, "test_user")
        self.assertEqual(energy_details.count(), 2)
        self.assertEqual(energy_details[1].energy, 50)
        self.assertEqual(energy_details[1].timestamp, make_aware(datetime(2022, 1, 1, 2, 0, 0)))
        self.assertEqual(energy_details[0].energy, 40)
        self.assertEqual(energy_details[0].timestamp, make_aware(datetime(2022, 1, 1, 2, 30, 0)))

    def test_parse_zaptec_datetime_floating_point(self):
        datetime_string = "2022-01-01T00:00:00.00000+00:00"
        expected_result = make_aware(datetime(2022, 1, 1, 1, 0, 0))

        result = zts.parse_zaptec_datetime(datetime_string)

        self.assertEqual(result, expected_result)

    def test_parse_zaptec_datetime_not_floating_point(self):
        datetime_string = "2022-01-01T00:00:00+00:00"
        expected_result = make_aware(datetime(2022, 1, 1, 1, 0, 0))

        result = zts.parse_zaptec_datetime(datetime_string)

        self.assertEqual(result, expected_result)

    def test_parse_zaptec_datetime_without_timezone_treated_as_utc(self):
        """Test that the parse_zaptec_datetime method correctly treats datetimes without a timezone as UTC."""
        datetime_string = "2022-01-01T00:00:00"
        expected_result = make_aware(datetime(2022, 1, 1, 1, 0, 0))

        result = zts.parse_zaptec_datetime(datetime_string)

        self.assertEqual(result, expected_result)

    def test_parse_zaptec_datetime_dst_conversion(self):
        """Test that the parse_zaptec_datetime method correctly converts from UTC to local time, including during daylight saving time."""
        datetime_string = "2022-07-01T00:00:00+00:00"
        expected_result = make_aware(datetime(2022, 7, 1, 2, 0, 0))

        result = zts.parse_zaptec_datetime(datetime_string)

        self.assertEqual(result, expected_result)

    def test_parse_zaptec_datetime_z_suffix(self):
        """Test that the parse_zaptec_datetime method correctly handles the 'Z' suffix, indicating UTC time."""
        datetime_string = "2022-01-01T00:00:00Z"
        expected_result = make_aware(datetime(2022, 1, 1, 1, 0, 0))

        result = zts.parse_zaptec_datetime(datetime_string)

        self.assertEqual(result, expected_result)

    @patch("car_charging.zaptec_services.request_charge_history")
    @patch("car_charging.zaptec_services.ZaptecToken.objects.first")
    def test_get_charge_history_data_fetches_all_pages(self, mock_first_token, mock_request_charge_history):
        start_date = make_aware(datetime(2025, 1, 1, 0, 0, 0))
        end_date = make_aware(datetime(2025, 1, 2, 0, 0, 0))
        mock_first_token.return_value = SimpleNamespace(token="test-token", is_token_expired=lambda: False)

        first_response = Mock()
        first_response.json.return_value = {"pages": 2, "data": [{"id": "first"}]}
        second_response = Mock()
        second_response.json.return_value = {"pages": 2, "data": [{"id": "second"}]}
        mock_request_charge_history.side_effect = [first_response, second_response]

        result = zts.get_charge_history_data(start_date, end_date)

        self.assertEqual(result, [{"id": "first"}, {"id": "second"}])
        self.assertEqual(mock_request_charge_history.call_count, 2)
        mock_request_charge_history.assert_any_call(
            "test-token",
            ANY,
            start_date,
            end_date,
            page_size=zts.CHARGE_HISTORY_PAGE_SIZE,
            page_index=0,
        )
        mock_request_charge_history.assert_any_call(
            "test-token",
            ANY,
            start_date,
            end_date,
            page_size=zts.CHARGE_HISTORY_PAGE_SIZE,
            page_index=1,
        )

    @patch("car_charging.zaptec_services.request_charge_history")
    @patch("car_charging.zaptec_services.ZaptecToken.objects.first")
    def test_get_charge_history_data_accepts_uppercase_response_keys(self, mock_first_token, mock_request_charge_history):
        start_date = make_aware(datetime(2025, 1, 1, 0, 0, 0))
        end_date = make_aware(datetime(2025, 1, 2, 0, 0, 0))
        mock_first_token.return_value = SimpleNamespace(token="test-token", is_token_expired=lambda: False)

        response = Mock()
        response.json.return_value = {"Pages": 1, "Data": [{"id": "first"}]}
        mock_request_charge_history.return_value = response

        result = zts.get_charge_history_data(start_date, end_date)

        self.assertEqual(result, [{"id": "first"}])

    @patch("car_charging.zaptec_services.request_charge_history")
    @patch("car_charging.zaptec_services.ZaptecToken.objects.first")
    def test_get_charge_history_data_raises_when_pages_field_is_missing(
        self,
        mock_first_token,
        mock_request_charge_history,
    ):
        start_date = make_aware(datetime(2025, 1, 1, 0, 0, 0))
        end_date = make_aware(datetime(2025, 1, 2, 0, 0, 0))
        mock_first_token.return_value = SimpleNamespace(token="test-token", is_token_expired=lambda: False)

        response = Mock()
        response.json.return_value = {"data": [{"id": "first"}]}
        mock_request_charge_history.return_value = response

        with self.assertRaisesMessage(
            zts.ChargeHistoryResponseException,
            "Zaptec charge history response is missing the pages field",
        ):
            zts.get_charge_history_data(start_date, end_date)
