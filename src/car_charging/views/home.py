from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from car_charging.models import ChargingSession


@login_required
def home(request):
    user = request.user
    # monthly_cost = calculate_monthly_cost(user)
    charging_sessions_count = ChargingSession.objects.filter(user_id=user.id).count()
    # spot_prices = get_spot_prices()  # Implement this function based on your logic

    context = {
        # 'monthly_cost': monthly_cost,
        "charging_sessions_count": charging_sessions_count,
        # 'spot_prices': spot_prices,
    }
    return render(request, "car_charging/home.html", context)
