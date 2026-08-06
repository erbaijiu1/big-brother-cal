import os
import sys
import unittest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server_mgr.customer_quote_utils import build_customer_fee_summary, parse_customer_price_tiers


class TestCustomerQuoteUtils(unittest.TestCase):
    def test_customer_fee_summary_keeps_minimum_on_total_only(self):
        result = build_customer_fee_summary(
            [
                {"name": "unit_price", "cn_name": "运输费用", "amount": 20},
                {"name": "delivery_fee", "cn_name": "派送费", "amount": 30},
            ],
            total_price=80,
            minimum_charge=80,
        )

        self.assertEqual(result["calculated_subtotal"], 50)
        self.assertTrue(result["minimum_applied"])
        self.assertEqual(
            result["customer_fee_details"],
            [
                {"code": "transport_fee", "name": "中港运输费", "amount": 20},
                {"code": "delivery_fee", "name": "香港派送费", "amount": 30},
            ],
        )

    def test_customer_fee_summary_uses_safe_names_without_raw_rules(self):
        result = build_customer_fee_summary(
            [
                {
                    "name": "unit_price",
                    "cn_name": "运输费用",
                    "amount": 120,
                    "rule": {"unit_price": 0.6},
                    "applied_value": 200,
                },
                {"name": "delivery_fee", "cn_name": "派送费", "amount": 85},
            ],
            total_price=205,
            minimum_charge=80,
        )

        self.assertFalse(result["minimum_applied"])
        self.assertTrue(all("rule" not in item for item in result["customer_fee_details"]))
        self.assertEqual(sum(item["amount"] for item in result["customer_fee_details"]), 205)

    def test_customer_price_tiers_only_return_safe_valid_fields(self):
        result = parse_customer_price_tiers(
            [
                {
                    "min_quantity": 1,
                    "max_quantity": 100,
                    "min_price": 7,
                    "max_price": 9,
                    "unit": "kg",
                    "internal_cost": 4.5,
                },
                {"min_quantity": 100, "max_quantity": 50, "min_price": 1, "max_price": 2},
            ]
        )

        self.assertEqual(
            result,
            [
                {
                    "min_quantity": 1.0,
                    "max_quantity": 100.0,
                    "min_price": 7.0,
                    "max_price": 9.0,
                    "unit": "kg",
                }
            ],
        )
        self.assertNotIn("internal_cost", result[0])


if __name__ == "__main__":
    unittest.main()
