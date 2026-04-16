from django.urls import path

from car_charging.views import EnergyDetailsListView, history, index, auth_token, ChargingSessionListView, costs_frontend

app_name = "charging"

urlpatterns = [
    path("", index, name="index"),
    path("token", auth_token.token_status, name="token_status"),
    path("renew_token", auth_token.renew_token, name="renew_token"),
    path("history", history.ChargeHistoryView.as_view(), name="history"),
    path("sessions", ChargingSessionListView.as_view(), name="session_list"),
    path("energy", EnergyDetailsListView.as_view(), name="energy_detail_list"),
    path("user_costs/", costs_frontend.costs_view, name="user_costs"),
    path("api/costs/summary", costs_frontend.costs_summary_api, name="costs_summary_api"),
    path("api/costs/history", costs_frontend.costs_history_api, name="costs_history_api"),
    path("api/costs/monthly_history", costs_frontend.costs_monthly_history_api, name="costs_monthly_history_api"),
]
