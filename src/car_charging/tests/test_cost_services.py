import uuid
from django.core.exceptions import ValidationError
from django.test import TestCase
from decimal import Decimal
from django.utils.timezone import datetime, make_aware

from car_charging.cost_services import create_cost_details
from car_charging.models import EnergyDetails, GridPrice, SpotPrice, SpotPriceRefund, UsagePrice, CostDetails, ChargingSession


class CostServicesTestCase(TestCase):
    """Test case for the cost details service."""

    def setUp(self):
        self.datetime_1 = make_aware(datetime(2025, 1, 1, 10))
        self.datetime_2 = make_aware(datetime(2025, 3, 1, 15))

        self.grid_price = GridPrice.objects.create(
            day_fee=Decimal("0.50"),
            night_fee=Decimal("0.30"),
            day_hour_from=6,
            night_hour_from=22,
            start_date=self.datetime_1.date(),
        )
        self.charging_session = ChargingSession.objects.create(
            session_id=uuid.uuid4(),
            charger_id=uuid.uuid4(),
            device_id=uuid.uuid4(),
            start_date_time=self.datetime_1,
            end_date_time=self.datetime_2,
            price_area=4,
            energy=2.31,
        )
        self.energy_details = EnergyDetails.objects.create(
            charging_session=self.charging_session,
            energy=Decimal("15.5"),
            timestamp=self.datetime_1,
        )
        self.usage_price = UsagePrice.objects.create(
            nok_pr_kwh=Decimal("0.40"),
            start_date=self.datetime_1.date(),
        )
        self.spot_price_refund = SpotPriceRefund.objects.create(
            deduction_threshold=Decimal("0.35"),
            reduction_factor=Decimal("0.1"),
            start_date=self.datetime_1.date(),
        )
        self.spot_price = SpotPrice.objects.create(
            nok_pr_kwh=Decimal("0.95"),
            start_time=self.datetime_1,
            price_area=4,
        )

    def test_correct_instance(self):
        """Test all the create_cost_details method sets all the correct price instances."""
        create_cost_details()

        cost_details = CostDetails.objects.first()

        self.assertEqual(cost_details.energy_detail, self.energy_details)
        self.assertEqual(cost_details.spot_price, self.spot_price)
        self.assertEqual(cost_details.grid_price, self.grid_price)
        self.assertEqual(cost_details.usage_price, self.usage_price)
        self.assertEqual(cost_details.spot_price_refund, self.spot_price_refund)

    def test_sets_correct_grid_price(self):
        """Test that the create_cost_details method sets the correct grid price instance."""
        datetime_3 = make_aware(datetime(2024, 12, 1, 10))
        GridPrice.objects.create(
            day_fee=Decimal("0.40"),
            night_fee=Decimal("0.20"),
            day_hour_from=6,
            night_hour_from=22,
            start_date=self.datetime_2.date(),
        )
        GridPrice.objects.create(
            day_fee=Decimal("0.30"),
            night_fee=Decimal("0.10"),
            day_hour_from=6,
            night_hour_from=22,
            start_date=datetime_3.date(),
        )

        create_cost_details()
        cost_details = CostDetails.objects.first()

        self.assertEqual(cost_details.grid_price, self.grid_price)

    def test_sets_correct_usage_price(self):
        """Test that the create_cost_details method sets the correct usage price instance."""
        datetime_3 = make_aware(datetime(2024, 12, 1, 10))
        UsagePrice.objects.create(
            nok_pr_kwh=Decimal("0.50"),
            start_date=self.datetime_2.date(),
        )
        UsagePrice.objects.create(
            nok_pr_kwh=Decimal("0.60"),
            start_date=datetime_3.date(),
        )

        create_cost_details()
        cost_details = CostDetails.objects.first()

        self.assertEqual(cost_details.usage_price, self.usage_price)

    def test_sets_correct_spot_price_refund(self):
        """Test that the create_cost_details method sets the correct spot price refund instance."""
        datetime_3 = make_aware(datetime(2024, 12, 1, 10))
        SpotPriceRefund.objects.create(
            deduction_threshold=Decimal("0.40"),
            reduction_factor=Decimal("0.2"),
            start_date=self.datetime_2.date(),
        )
        SpotPriceRefund.objects.create(
            deduction_threshold=Decimal("0.30"),
            reduction_factor=Decimal("0.1"),
            start_date=datetime_3.date(),
        )

        create_cost_details()
        cost_details = CostDetails.objects.first()

        self.assertEqual(cost_details.spot_price_refund, self.spot_price_refund)

    def test_sets_correct_spot_price(self):
        """Test that the create_cost_details method sets the correct spot price instance."""
        datetime_3 = make_aware(datetime(2024, 12, 1, 10))
        SpotPrice.objects.create(
            nok_pr_kwh=Decimal("0.85"),
            start_time=self.datetime_2,
            price_area=4,
        )
        SpotPrice.objects.create(
            nok_pr_kwh=Decimal("0.75"),
            start_time=datetime_3,
            price_area=4,
        )

        create_cost_details()
        cost_details = CostDetails.objects.first()

        self.assertEqual(cost_details.spot_price, self.spot_price)

    def test_date_range_filters_energy_details_and_keeps_effective_prices(self):
        """Test that date filtering only affects energy rows, not the applicable dated prices."""
        in_range_timestamp = make_aware(datetime(2025, 1, 10, 11))
        out_of_range_timestamp = make_aware(datetime(2025, 1, 11, 11))

        in_range_detail = EnergyDetails.objects.create(
            charging_session=self.charging_session,
            energy=Decimal("3.5"),
            timestamp=in_range_timestamp,
        )
        out_of_range_detail = EnergyDetails.objects.create(
            charging_session=self.charging_session,
            energy=Decimal("4.5"),
            timestamp=out_of_range_timestamp,
        )
        in_range_spot_price = SpotPrice.objects.create(
            nok_pr_kwh=Decimal("1.10"),
            start_time=in_range_timestamp,
            price_area=4,
        )
        SpotPrice.objects.create(
            nok_pr_kwh=Decimal("1.20"),
            start_time=out_of_range_timestamp,
            price_area=4,
        )

        create_cost_details(from_date=make_aware(datetime(2025, 1, 10)), to_date=make_aware(datetime(2025, 1, 11)))

        self.assertFalse(CostDetails.objects.filter(energy_detail=self.energy_details).exists())
        self.assertTrue(CostDetails.objects.filter(energy_detail=in_range_detail).exists())
        self.assertFalse(CostDetails.objects.filter(energy_detail=out_of_range_detail).exists())

        cost_details = CostDetails.objects.get(energy_detail=in_range_detail)
        self.assertEqual(cost_details.spot_price, in_range_spot_price)
        self.assertEqual(cost_details.grid_price, self.grid_price)
        self.assertEqual(cost_details.usage_price, self.usage_price)
        self.assertEqual(cost_details.spot_price_refund, self.spot_price_refund)

    def test_rerun_updates_existing_cost_details(self):
        """Test that rerunning the service recomputes an existing cost detail row."""
        create_cost_details()

        self.grid_price.day_fee = Decimal("0.60")
        self.grid_price.save()

        create_cost_details()

        cost_details = CostDetails.objects.get(energy_detail=self.energy_details)

        self.assertEqual(CostDetails.objects.count(), 1)
        self.assertEqual(cost_details.grid_cost, self.energy_details.energy * Decimal("0.60"))

    def test_no_spot_price(self):
        """
        Test that the create_cost_details method throws an error if there is no corresponding spot price.
        Not really important which exception is raised, for now.
        """
        self.spot_price.delete()

        with self.assertRaisesMessage(ValidationError, "SpotPrice"):
            create_cost_details()

    def test_no_grid_price(self):
        """
        Test that the create_cost_details method throws an error if there is no corresponding grid price.
        Not really important which exception is raised, for now.
        """
        self.grid_price.delete()

        with self.assertRaisesMessage(ValidationError, "GridPrice"):
            create_cost_details()

    def test_no_usage_price(self):
        """
        Test that the create_cost_details method throws an error if there is no corresponding usage price.
        Not really important which exception is raised, for now.
        """
        self.usage_price.delete()

        with self.assertRaisesMessage(ValidationError, "UsagePrice"):
            create_cost_details()

    def test_no_spot_price_refund(self):
        """
        Test that the create_cost_details method throws an error if there is no corresponding spot price refund.
        Not really important which exception is raised, for now.
        """
        self.spot_price_refund.delete()

        with self.assertRaisesMessage(ValidationError, "SpotPriceRefund"):
            create_cost_details()

    def test_wrong_spot_price_area(self):
        """
        Test that the create_cost_details method throws an error if there is no corresponding spot price for the price area.
        Not really important which exception is raised, for now.
        """
        self.spot_price.price_area = 5
        self.spot_price.save()

        with self.assertRaisesMessage(ValidationError, "SpotPrice"):
            create_cost_details()
