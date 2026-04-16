import os
import django
from django.test.client import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jom.settings")
django.setup()

client = Client()
response_summary = client.get('/charging/api/costs/summary')
print("Summary Status:", response_summary.status_code)

response_history = client.get('/charging/api/costs/history')
print("History Status:", response_history.status_code)

print("HTML View Status:", client.get('/charging/user_costs/').status_code)
