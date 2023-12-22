import os
import requests
from django.forms import Form
from django.utils.timezone import datetime
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from car_charging.forms import DateRangeForm
from car_charging.models import ChargingSession, EnergyDetails, ZaptecToken


def convert_datetime(datetime_string):
    if "." in datetime_string:
        dt = datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S.%f%z")
    else:
        dt = datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S%z")
    return dt


def request_charge_history(access_token: str, installation_id: str, from_date: datetime, to_date: datetime) -> requests.Response:
    """
    Request charge history from Zaptec API in given time interval.
    """
    datetime_format = "%Y-%m-%dT%H:%M:%S.%f%z"
    endpoint_url = "https://api.zaptec.com/api/chargehistory"
    params = {
        "InstallationId": installation_id,
        "GroupBy": "2",
        "DetailLevel": "1",
        "From": from_date.strftime(datetime_format),
        "To": to_date.strftime(datetime_format),
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(endpoint_url, headers=headers, params=params)
    return response


def get_charge_history_data(form: Form) -> list[dict]:
    access_token = ZaptecToken.objects.first().token
    installation_id = os.getenv("INSTALLATION_ID", "")
    start_date = form.cleaned_data["start_date"]
    end_date = form.cleaned_data["end_date"]
    response = request_charge_history(access_token, installation_id, start_date, end_date)
    return response.json()["Data"]


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


def charge_history(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = DateRangeForm(request.POST)
        if form.is_valid():
            data = get_charge_history_data(form)
            new_sessions = create_charging_sessions(data)
            return render(
                request,
                "car_charging/history.html",
                {
                    "new_sessions": new_sessions,
                },
            )
    else:
        form = DateRangeForm()
    return render(request, "car_charging/history.html", {"form": form, "new_sessions": None})