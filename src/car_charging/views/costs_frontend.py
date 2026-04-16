import logging
from datetime import datetime, timezone
from django.shortcuts import render
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from car_charging.models import CostDetails

logger = logging.getLogger(__name__)

def costs_view(request):
    """Renders the single page frontend for user costs."""
    available_years = CostDetails.objects.dates('timestamp', 'year', order='DESC')
    return render(request, "car_charging/user_costs.html", {"available_years": available_years})

def _get_dates_from_year(request):
    year_str = request.GET.get('year')
    if year_str and year_str.isdigit():
        year = int(year_str)
        from_date = datetime(year, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        return from_date, to_date
    return None, None

def costs_summary_api(request):
    """API endpoint to get total aggregated costs grouped by user."""
    from_date, to_date = _get_dates_from_year(request)
    data = CostDetails.objects.costs_by_user(from_date=from_date, to_date=to_date)
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)

def costs_history_api(request):
    """API endpoint to get detailed charging history for users or a specific user."""
    user_id = request.GET.get('user_id')
    queryset = CostDetails.objects.all().order_by('-timestamp')
    
    from_date, to_date = _get_dates_from_year(request)
    if from_date:
        queryset = queryset.filter(timestamp__gte=from_date)
    if to_date:
        queryset = queryset.filter(timestamp__lt=to_date)
        
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
        
    from_date, to_date = _get_dates_from_year(request)
    data = CostDetails.objects.costs_by_month_user(user_id=user_id, from_date=from_date, to_date=to_date)
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)
