import uuid
from django.core.exceptions import ValidationError
from django.test import TestCase
from decimal import Decimal
from django.utils.timezone import datetime, make_aware

from car_charging.models import EnergyDetails, GridPrice, SpotPrice, SpotPriceRefund, UsagePrice, CostDetails, ChargingSession


class CostDetailsTestCase(TestCase):
    """Test case for cost details methods. All methods are triggered by the save method, which is called by the create method, in the setup."""

    def setUp(self):
        self.datetime_1 = make_aware(datetime(2025, 1, 1, 10))
        self.datetime_2 = make_aware(datetime(2025, 1, 1, 15))

        self.grid_price = GridPrice.objects.create(
            day_fee=Decimal("0.50"), night_fee=Decimal("0.30"), day_hour_from=6, night_hour_from=22, start_date=self.datetime_1.date()
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
        self.energy_details = EnergyDetails.objects.create(charging_session=self.charging_session, energy=Decimal("15.5"), timestamp=self.datetime_1)
        self.usage_price = UsagePrice.objects.create(nok_pr_kwh=Decimal("0.40"), start_date=self.datetime_1.date())
        self.spot_price_refund = SpotPriceRefund.objects.create(
            deduction_threshold=Decimal("0.35"), reduction_factor=Decimal("0.1"), start_date=self.datetime_1.date()
        )
        self.spot_price = SpotPrice.objects.create(nok_pr_kwh=Decimal("0.95"), start_time=self.datetime_1, price_area=4)

        self.cost_details = CostDetails.objects.create(
            energy_detail=self.energy_details,
            spot_price=self.spot_price,
            grid_price=self.grid_price,
            usage_price=self.usage_price,
            spot_price_refund=self.spot_price_refund,
        )

    def test_cost_details_initialization(self):
        """Test initialization of CostDetails model."""
        self.assertEqual(self.cost_details.energy_detail, self.energy_details)
        self.assertEqual(self.cost_details.grid_price, self.grid_price)
        self.assertEqual(self.cost_details.usage_price, self.usage_price)
        self.assertEqual(self.cost_details.spot_price_refund, self.spot_price_refund)

    def test_copy_values(self):
        """Test that relevant values from the related models are copied to the cost detail."""
        self.assertEqual(self.cost_details.energy, self.energy_details.energy)
        self.assertEqual(self.cost_details.timestamp, self.energy_details.timestamp)
        self.assertEqual(self.cost_details.session_id, self.charging_session.id)
        self.assertEqual(self.cost_details.price_area, self.charging_session.price_area)

    def test_set_spot_price(self):
        """Test that the set spot price method."""
        self.assertEqual(self.cost_details.spot_price_nok, self.spot_price.nok_pr_kwh)

    def test_set_grid_price(self):
        """Test the grid price set method."""
        grid_price = self.grid_price.get_price(self.datetime_1)

        self.assertEqual(self.cost_details.grid_price_nok, grid_price)

    def test_set_usage_price(self):
        """Test the usage price set method."""
        usage_price = self.usage_price.get_price(self.datetime_1)

        self.assertEqual(self.cost_details.usage_price_nok, usage_price)

    def test_set_user(self):
        """Test the set user method."""
        self.assertEqual(self.cost_details.user_id, self.charging_session.user_id)
        self.assertEqual(self.cost_details.user_full_name, self.charging_session.user_full_name)

    def test_set_spot_cost(self):
        """Test that the set spot cost method calculates the correct price."""
        energy = self.energy_details.energy
        spot_price_nok = self.spot_price.nok_pr_kwh

        self.assertEqual(self.cost_details.spot_cost, energy * spot_price_nok)

    def test_set_grid_cost(self):
        """Test that the set grid cost method calculates the correct price."""
        energy = self.energy_details.energy
        grid_fee = self.grid_price.day_fee

        self.assertEqual(self.cost_details.grid_cost, energy * grid_fee)

    def test_set_usage_cost(self):
        """Test that the set usage cost method calculates the correct price."""
        energy = self.energy_details.energy
        usage_price_nok = self.usage_price.nok_pr_kwh

        self.assertEqual(self.cost_details.usage_cost, energy * usage_price_nok)

    def test_set_fund_cost(self):
        """Test that the set fund cost method calculates the correct price."""
        energy = self.energy_details.energy
        fund_price_nok = self.cost_details.fund_price_nok

        self.assertEqual(self.cost_details.fund_cost, energy * fund_price_nok)

    def test_set_spot_price_refund(self):
        """Test the spot price refund set method."""
        spot_price_refund = self.spot_price_refund.calculate_refund_price(self.datetime_1, self.spot_price.get_price(self.datetime_1, 4))

        self.assertEqual(self.cost_details.refund_price_nok, spot_price_refund)

    def test_set_total_cost(self):
        """Test that the set total cost method calculates the correct total cost."""
        spot_cost = self.cost_details.spot_cost
        grid_cost = self.cost_details.grid_cost
        usage_cost = self.cost_details.usage_cost
        fund_cost = self.cost_details.fund_cost
        refund = self.cost_details.refund
        total_cost = spot_cost + grid_cost + usage_cost + fund_cost - refund

        self.assertEqual(self.cost_details.total_cost, total_cost)

    def test_save_raises_validation_error_when_spot_price_is_missing(self):
        """Test that saving CostDetails without all required prices fails clearly."""
        cost_details = CostDetails(
            energy_detail=self.energy_details,
            grid_price=self.grid_price,
            usage_price=self.usage_price,
            spot_price_refund=self.spot_price_refund,
        )

        with self.assertRaisesMessage(ValidationError, "spot_price"):
            cost_details.save()
