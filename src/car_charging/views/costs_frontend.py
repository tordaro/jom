import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from car_charging.models import CostDetails

logger = logging.getLogger(__name__)

def costs_view(request):
    """Renders the single page frontend for user costs."""
    return render(request, "car_charging/user_costs.html")

def costs_summary_api(request):
    """API endpoint to get total aggregated costs grouped by user."""
    data = CostDetails.objects.costs_by_user()
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)

def costs_history_api(request):
    """API endpoint to get detailed charging history for users or a specific user."""
    user_id = request.GET.get('user_id')
    queryset = CostDetails.objects.all().order_by('-timestamp')
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
        
    data = list(queryset.values(
        'timestamp', 
        'energy', 
        'spot_cost', 
        'grid_cost', 
        'usage_cost', 
        'fund_cost', 
        'refund', 
        'total_cost', 
        'user_full_name',
        'user_id'
    ))
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)

def costs_monthly_history_api(request):
    """API endpoint to get monthly aggregated costs for a specific user."""
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)
    data = CostDetails.objects.costs_by_month_user(user_id=user_id)
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)
