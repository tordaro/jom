from django.urls import path

from car_charging.views import index, costs_frontend

app_name = "charging"

urlpatterns = [
    path("", index, name="index"),
    path("user_costs/", costs_frontend.costs_view, name="user_costs"),
    path("api/costs/summary", costs_frontend.costs_summary_api, name="costs_summary_api"),
    path("api/costs/history", costs_frontend.costs_history_api, name="costs_history_api"),
    path("api/costs/monthly_history", costs_frontend.costs_monthly_history_api, name="costs_monthly_history_api"),
]
