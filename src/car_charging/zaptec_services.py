import os
import requests
from datetime import datetime, timezone
from django.utils.timezone import localtime

from car_charging.models import ChargingSession, EnergyDetails, ZaptecToken


CHARGE_HISTORY_PAGE_SIZE = 100


def request_charge_history(
    access_token: str,
    installation_id: str,
    from_date: datetime,
    to_date: datetime,
    page_size: int = CHARGE_HISTORY_PAGE_SIZE,
    page_index: int = 0,
) -> requests.Response:
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
        "PageSize": page_size,
        "PageIndex": page_index,
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(endpoint_url, headers=headers, params=params)
    return response


def _get_charge_history_page_data(response_data: dict) -> list[dict]:
    page_data = response_data.get("data")
    if page_data is None:
        page_data = response_data.get("Data")
    return page_data or []


def _get_charge_history_pages(response_data: dict) -> int | None:
    pages = response_data.get("pages")
    if pages is None:
        pages = response_data.get("Pages")
    return pages


def request_token(username: str, password: str) -> requests.Response:
    url = "https://api.zaptec.com/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "password", "username": username, "password": password}

    response = requests.post(url, data=data, headers=headers)
    return response


class TokenRenewalException(Exception):
    """Exception raised when token renewal fails."""

    def __init__(self, message: str = "Failed to renew Zaptec token", status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} - Status Code: {self.status_code}"


class ChargeHistoryResponseException(Exception):
    """Exception raised when Zaptec charge history responses are missing required fields."""


def renew_token(username: str, password: str) -> ZaptecToken:
    response = request_token(username, password)
    if response.status_code != 200:
        raise TokenRenewalException(status_code=response.status_code)

    response_data = response.json()
    new_token = ZaptecToken.objects.create(
        token=response_data.get("access_token", ""),
        token_type=response_data.get("token_type", ""),
        expires_in=response_data.get("expires_in", None),
    )
    return new_token


def parse_zaptec_datetime(datetime_string: str) -> datetime:
    """Parse a Zaptec timestamp into an aware datetime in the Django timezone.

    Zaptec responses are inconsistent: timestamps may include an explicit UTC
    offset, a trailing Z, fractional seconds, or no timezone information at
    all. This project treats timestamps without timezone information as UTC and
    then converts the result to the active Django timezone.
    """
    normalized_datetime = datetime_string.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized_datetime)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return localtime(dt)


def create_charging_sessions(api_data: list[dict]) -> list[ChargingSession]:
    """
    Create new ChargingSession and EnergyDetails objects from the given API data.
    All timestamps are normalized to the Django timezone before saving.
    """
    new_sessions = []
    for session_data in api_data:
        commit_end_date_time = session_data.get("CommitEndDateTime", None)
        if commit_end_date_time:
            commit_end_date_time = parse_zaptec_datetime(commit_end_date_time)

        session, is_created = ChargingSession.objects.get_or_create(
            session_id=session_data["Id"],
            defaults={
                "user_full_name": session_data.get("UserFullName", ""),
                "user_id": session_data.get("UserId", None),
                "user_name": session_data.get("UserName", ""),
                "user_email": session_data.get("UserEmail", ""),
                "device_id": session_data["DeviceId"],
                "start_date_time": parse_zaptec_datetime(session_data["StartDateTime"]),
                "end_date_time": parse_zaptec_datetime(session_data["EndDateTime"]),
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
                    timestamp=parse_zaptec_datetime(detail_data["Timestamp"]),
                )

    return new_sessions


def get_charge_history_data(start_date: datetime, end_date: datetime) -> list[dict]:
    """
    Get charge history data from Zaptec API.
    """
    zaptec_token = ZaptecToken.objects.first()
    if not zaptec_token or zaptec_token.is_token_expired():
        # TODO: Test this when zaptec_token is None
        username = os.getenv("ZAPTEC_USERNAME", "")
        password = os.getenv("ZAPTEC_PASSWORD", "")
        zaptec_token = renew_token(username, password)

    access_token = zaptec_token.token
    installation_id = os.getenv("INSTALLATION_ID", "")
    first_response = request_charge_history(
        access_token,
        installation_id,
        start_date,
        end_date,
        page_size=CHARGE_HISTORY_PAGE_SIZE,
        page_index=0,
    )
    first_response.raise_for_status()
    first_response_data = first_response.json()
    all_charge_history = _get_charge_history_page_data(first_response_data)

    total_pages = _get_charge_history_pages(first_response_data)
    if total_pages is None:
        raise ChargeHistoryResponseException("Zaptec charge history response is missing the pages field")

    for page_index in range(1, total_pages):
        response = request_charge_history(
            access_token,
            installation_id,
            start_date,
            end_date,
            page_size=CHARGE_HISTORY_PAGE_SIZE,
            page_index=page_index,
        )
        response.raise_for_status()
        response_data = response.json()
        all_charge_history.extend(_get_charge_history_page_data(response_data))

    return all_charge_history
