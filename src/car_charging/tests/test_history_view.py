import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import datetime, make_aware
from unittest.mock import patch

import car_charging.zaptec_services as zts
from car_charging.models import ZaptecToken
from car_charging.views.history import ChargeHistoryView


class ChargingHistoryViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.charger_id = uuid.uuid4()
        self.device_id = uuid.uuid4()
        self.session_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        self.timestamp = make_aware((datetime(2022, 1, 1, 2)))
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
        self.zaptec_token = ZaptecToken.objects.create(
            token="test_token",
            expires_in=60 * 60 * 24,
        )

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
        # EnergyDetails are ordered by timestamp desc
        self.assertEqual(energy_details[1].energy, 50)
        self.assertEqual(energy_details[1].timestamp, make_aware(datetime(2022, 1, 1, 2, 0, 0)))
        self.assertEqual(energy_details[0].energy, 40)
        self.assertEqual(energy_details[0].timestamp, make_aware(datetime(2022, 1, 1, 2, 30, 0)))

    def test_charge_history_get(self):
        client = Client()
        response = client.get(reverse("charging:history"))
        self.assertEqual(response.status_code, 200)

    @patch("car_charging.zaptec_services.get_charge_history_data")
    def test_charge_history_post(self, mock_get_charge_history_data):
        mock_get_charge_history_data.return_value = self.data
        form_data = {
            "start_date": "2022-01-01",
            "end_date": "2022-01-31",
        }
        response = self.client.post(reverse("charging:history"), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url=reverse("charging:session_list"), status_code=302, target_status_code=200)

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
        datetime_string = "2022-01-01T00:00:00"
        expected_result = make_aware(datetime(2022, 1, 1, 1, 0, 0))

        result = zts.parse_zaptec_datetime(datetime_string)

        self.assertEqual(result, expected_result)

    def test_parse_zaptec_datetime_dst_conversion(self):
        datetime_string = "2022-07-01T00:00:00+00:00"
        expected_result = make_aware(datetime(2022, 7, 1, 2, 0, 0))

        result = zts.parse_zaptec_datetime(datetime_string)

        self.assertEqual(result, expected_result)

    def test_parse_zaptec_datetime_z_suffix(self):
        datetime_string = "2022-01-01T00:00:00Z"
        expected_result = make_aware(datetime(2022, 1, 1, 1, 0, 0))

        result = zts.parse_zaptec_datetime(datetime_string)

        self.assertEqual(result, expected_result)
