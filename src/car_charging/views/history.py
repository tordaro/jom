import os
from django.forms import Form
from django.urls import reverse_lazy
from django.shortcuts import render
from django.contrib import messages
from django.views.generic.edit import FormView
from django.utils.timezone import datetime

from car_charging.zaptec_services import request_charge_history, renew_token
from car_charging.forms import DateRangeForm
from car_charging.models import ChargingSession, EnergyDetails, ZaptecToken


def convert_datetime(datetime_string):
    if "." in datetime_string:
        dt = datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S.%f%z")
    else:
        dt = datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S%z")
    return dt


class ChargeHistoryView(FormView):
    template_name = "car_charging/history.html"
    form_class = DateRangeForm
    success_url = reverse_lazy("charging:session_list")

    def form_valid(self, form: Form):
        data = self.get_charge_history_data(form)
        new_sessions = self.create_charging_sessions(data)

        if not data:
            messages.info(self.request, "No data retrieved for the given date range.")
            return render(self.request, self.template_name, {"form": form})
        elif not new_sessions:
            messages.info(self.request, "Data retrieved but no new sessions created.")
            self.request.session["no_new_sessions"] = True
            return render(self.request, self.template_name, {"form": form})
        else:
            messages.success(self.request, f"{len(new_sessions)} new charging sessions created.")
            return super().form_valid(form)

    def form_invalid(self, form: Form):
        return super().form_invalid(form)

    @staticmethod
    def get_charge_history_data(form: Form) -> list[dict]:
        zaptec_token = ZaptecToken.objects.first()
        if not zaptec_token or zaptec_token.is_token_expired():
            # TODO: Test this when zaptec_token is None
            username = os.getenv("ZAPTEC_USERNAME", "")
            password = os.getenv("ZAPTEC_PASSWORD", "")
            zaptec_token = renew_token(username, password)
        access_token = zaptec_token.token
        installation_id = os.getenv("INSTALLATION_ID", "")
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        response = request_charge_history(access_token, installation_id, start_date, end_date)
        return response.json()["Data"]

    @staticmethod
    def create_charging_sessions(data: list[dict]) -> list[ChargingSession]:
        new_sessions = []
        for session_data in data:
            commit_end_date_time = session_data.get("CommitEndDateTime", None)
            commit_end_date_time = commit_end_date_time + "+00:00" if commit_end_date_time else None
            session, is_created = ChargingSession.objects.get_or_create(
                session_id=session_data["Id"],
                defaults={
                    "user_full_name": session_data.get("UserFullName", ""),
                    "user_id": session_data.get("UserId", None),
                    "user_name": session_data.get("UserName", ""),
                    "user_email": session_data.get("UserEmail", ""),
                    "device_id": session_data["DeviceId"],
                    "start_date_time": convert_datetime(session_data["StartDateTime"] + "+00:00"),
                    "end_date_time": convert_datetime(session_data["EndDateTime"] + "+00:00"),
                    "energy": session_data["Energy"],
                    "commit_metadata": session_data.get("CommitMetadata", None),
                    "commit_end_date_time": commit_end_date_time,
                    "charger_id": session_data["ChargerId"],
                    "device_name": session_data.get("DeviceName", ""),
                    "externally_ended": session_data.get("ExternallyEnded", None),
                },
            )
            if not is_created:
                continue
            else:
                new_sessions.append(session)
                energy_details = session_data["EnergyDetails"]
                for detail_data in energy_details:
                    EnergyDetails.objects.create(
                        charging_session=session,
                        energy=detail_data["Energy"],
                        timestamp=convert_datetime(detail_data["Timestamp"]),
                    )
        return new_sessions
