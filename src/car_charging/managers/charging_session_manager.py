from django.db import models
from django.db.models import Max
from django.db.models.query import QuerySet


class ChargingSessionManager(models.Manager):
    def get_unique_users(self) -> list[dict[str, str | float | None]]:
        """Return a list of dictionaries with unique user data for each unique user who has charging sessions."""
        users_data: QuerySet = (
            self.get_queryset().values("user_id").annotate(user_full_name=Max("user_full_name"), user_email=Max("user_email")).order_by("user_id")
        )
        return list(users_data)
