import uuid
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch


class ChargingHistoryViewTests(TestCase):
    def setUp(self):
        self.client = Client()

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
