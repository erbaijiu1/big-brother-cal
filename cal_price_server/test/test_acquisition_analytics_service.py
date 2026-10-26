import unittest
from datetime import date
from decimal import Decimal

from services.acquisition_analytics_service import (
    build_acquisition_analysis,
    build_category_detail,
    build_order_drilldown,
    normalize_category,
)


def order(
    row_id,
    shipping_date,
    customer,
    product_name,
    fee=100,
    cost=70,
    channel="普A",
    trade_id=None,
    salesman="业务员A",
):
    return {
        "id": row_id,
        "company_tracking_no": f"ORDER-{row_id:03d}",
        "shipping_date": shipping_date,
        "product_name": product_name,
        "shipping_channel": channel,
        "salesman": salesman,
        "shipping_fee": Decimal(str(fee)),
        "shipping_cost": Decimal(str(cost)),
        "goods_weight": Decimal("10"),
        "goods_volume": Decimal("0.1"),
        "trade_id": trade_id if trade_id is not None else row_id,
        "shipping_customer": customer,
        "receiving_address": "香港",
        "scheduling_status": "成本结算",
    }


class AcquisitionAnalyticsServiceTest(unittest.TestCase):
    def test_product_categories_are_explicit_and_unmapped_names_stay_pending(self):
        self.assertEqual(normalize_category("水果"), "水果")
        self.assertEqual(normalize_category("芒果"), "待归一")
        self.assertEqual(normalize_category("  "), "未知品类")

    def test_global_first_order_is_not_reset_by_selected_category(self):
        rows = [
            order(1, date(2026, 1, 1), "客户A", "食品"),
            order(2, date(2026, 3, 1), "客户A", "水果"),
            order(3, date(2026, 3, 2), "客户B", "水果"),
        ]

        result = build_acquisition_analysis(rows, date(2026, 3, 1), date(2026, 3, 31))
        fruit = next(item for item in result["categories"] if item["category"] == "水果")

        self.assertEqual(fruit["order_count"], 2)
        self.assertEqual(fruit["database_first_customer_count"], 1)
        self.assertEqual(fruit["category_first_customer_count"], 2)

    def test_cross_category_follow_up_counts_for_any_category_repurchase(self):
        rows = [
            order(1, date(2026, 1, 1), "客户A", "食品", fee=200, cost=100),
            order(2, date(2026, 1, 20), "客户A", "普货", fee=300, cost=200),
            order(3, date(2026, 4, 20), "截止日期客户", "食品"),
        ]

        result = build_acquisition_analysis(rows, date(2026, 1, 1), date(2026, 4, 20), min_orders=1, min_new_customers=1)
        food = next(item for item in result["categories"] if item["category"] == "食品")

        self.assertEqual(food["cohort_90"]["mature_customers"], 1)
        self.assertEqual(food["cohort_90"]["repurchase_rate_pct"], 100.0)
        self.assertEqual(food["cohort_90"]["same_category_repurchase_rate_pct"], 0.0)
        self.assertEqual(food["cohort_90"]["cumulative_profit_per_customer"], 200.0)

    def test_immature_customer_is_not_counted_as_failed_repurchase(self):
        rows = [
            order(1, date(2026, 4, 15), "客户A", "食品"),
            order(2, date(2026, 4, 20), "截止日期客户", "食品"),
        ]

        result = build_acquisition_analysis(rows, date(2026, 4, 1), date(2026, 4, 20), min_orders=1, min_new_customers=1)
        food = next(item for item in result["categories"] if item["category"] == "食品")

        self.assertEqual(food["cohort_30"]["mature_customers"], 0)
        self.assertIsNone(food["cohort_30"]["repurchase_rate_pct"])
        self.assertEqual(food["cohort_90"]["mature_customers"], 0)

    def test_missing_cost_is_excluded_from_profit_and_rate(self):
        rows = [
            order(1, date(2026, 1, 1), "客户A", "冻品", fee=100, cost=0),
            order(2, date(2026, 1, 2), "客户B", "冻品", fee=100, cost=70),
        ]

        result = build_acquisition_analysis(rows, date(2026, 1, 1), date(2026, 1, 2), min_orders=1, min_new_customers=1)
        frozen = next(item for item in result["categories"] if item["category"] == "冻品")

        self.assertEqual(result["summary"]["total_profit"], 30.0)
        self.assertEqual(result["summary"]["profit_rate_pct"], 30.0)
        self.assertEqual(result["summary"]["profit_order_coverage_pct"], 50.0)
        self.assertEqual(result["summary"]["database_first_profit_covered_count"], 1)
        self.assertEqual(result["summary"]["database_first_profit_coverage_pct"], 50.0)
        self.assertEqual(result["summary"]["avg_database_first_order_profit"], 30.0)
        self.assertEqual(frozen["missing_cost_order_count"], 1)

    def test_same_day_multiple_orders_use_tracking_number_then_id_as_stable_order(self):
        rows = [
            order(2, date(2026, 1, 1), "客户A", "食品"),
            order(1, date(2026, 1, 1), "客户A", "食品"),
            order(3, date(2026, 4, 2), "截止日期客户", "食品"),
        ]

        result = build_acquisition_analysis(rows, date(2026, 1, 1), date(2026, 4, 2), min_orders=1, min_new_customers=1)
        food = next(item for item in result["categories"] if item["category"] == "食品")

        self.assertEqual(food["database_first_customer_count"], 2)
        self.assertEqual(food["cohort_30"]["mature_customers"], 1)
        self.assertEqual(food["cohort_30"]["repurchased_customers"], 1)

    def test_drilldown_preserves_missing_cost_as_null_and_exact_scope(self):
        rows = [
            order(1, date(2026, 1, 1), "客户A", "冻品", fee=100, cost=0),
            order(2, date(2026, 1, 2), "客户B", "冻品", fee=100, cost=70),
        ]

        details = build_order_drilldown(rows, "missing_cost", date(2026, 1, 1), date(2026, 1, 2))

        self.assertEqual(len(details), 1)
        self.assertIsNone(details[0]["shipping_cost"])
        self.assertIsNone(details[0]["gross_profit"])

    def test_customer_coverage_requires_an_identifiable_customer(self):
        rows = [
            order(1, date(2026, 1, 1), None, "食品", trade_id=99),
            order(2, date(2026, 1, 2), "客户B", "食品"),
        ]

        result = build_acquisition_analysis(rows, date(2026, 1, 1), date(2026, 1, 2))

        self.assertEqual(result["quality"]["customer_match_order_count"], 1)
        self.assertEqual(result["quality"]["customer_match_rate_pct"], 50.0)
        self.assertEqual(result["summary"]["database_first_customer_count"], 1)

    def test_category_detail_respects_channel_filter(self):
        rows = [
            order(1, date(2026, 1, 1), "客户A", "水果", channel="水果A"),
            order(2, date(2026, 1, 2), "客户B", "水果", channel="水果B"),
        ]
        analysis = build_acquisition_analysis(
            rows, date(2026, 1, 1), date(2026, 1, 2), category="水果", channel="水果A",
            min_orders=1, min_new_customers=1,
        )

        detail = build_category_detail(analysis, rows, "水果", channel="水果A")

        self.assertEqual(detail["metric"]["order_count"], 1)
        self.assertEqual(len(detail["channels"]), 1)
        self.assertEqual(detail["channels"][0]["name"], "水果A")
        self.assertEqual(detail["channels"][0]["revenue_contribution_pct"], 100.0)
        self.assertEqual(detail["channels"][0]["profit_contribution_pct"], 100.0)

    def test_category_detail_contributions_reconcile_and_use_full_customer_history(self):
        rows = [
            order(9, date(2025, 12, 20), "客户C", "食品", salesman="业务员B"),
            order(1, date(2026, 1, 1), "客户A", "水果", fee=200, cost=100, salesman="业务员A"),
            order(2, date(2026, 1, 2), "客户A", "水果", fee=150, cost=100, salesman="业务员A"),
            order(3, date(2026, 1, 3), "客户B", "水果", fee=300, cost=100, salesman="业务员B"),
            order(4, date(2026, 1, 4), None, "水果", fee=100, cost=70, salesman=None),
            order(5, date(2026, 1, 5), "客户C", "水果", fee=110, cost=70, salesman="业务员B"),
        ]
        analysis = build_acquisition_analysis(
            rows, date(2026, 1, 1), date(2026, 1, 31), category="水果",
            min_orders=1, min_new_customers=1,
        )

        detail = build_category_detail(analysis, rows, "水果")
        salespeople = detail["salesman_contribution"]["items"]
        customers = detail["customer_contribution"]["items"]

        self.assertEqual(sum(item["order_count"] for item in salespeople), detail["metric"]["order_count"])
        self.assertEqual(sum(item["total_revenue"] for item in salespeople), 860.0)
        self.assertEqual(sum(item["revenue"] for item in detail["channels"]), 860.0)
        self.assertAlmostEqual(sum(item["revenue_contribution_pct"] for item in detail["channels"]), 100.0, places=1)
        self.assertEqual(sum(item["total_profit"] for item in salespeople), detail["metric"]["total_profit"])
        self.assertEqual(sum(item["total_profit"] for item in customers), detail["metric"]["total_profit"])
        self.assertAlmostEqual(sum(item["profit_contribution_pct"] for item in customers), 100.0, places=1)
        self.assertEqual(detail["salesman_contribution"]["summary"]["salesman_count"], 2)
        self.assertEqual(detail["salesman_contribution"]["summary"]["unknown_order_count"], 1)
        self.assertEqual(detail["customer_contribution"]["summary"]["customer_count"], 3)
        self.assertEqual(detail["customer_contribution"]["summary"]["profit_excluding_largest_customer"], 190.0)

        customer_c = next(item for item in customers if item["name"] == "客户C")
        self.assertEqual(customer_c["first_shipping_date"], "2025-12-20")
        self.assertEqual(customer_c["last_shipping_date"], "2026-01-05")
        self.assertFalse(customer_c["is_database_first_customer"])

        salesman_a = next(item for item in salespeople if item["name"] == "业务员A")
        self.assertEqual(salesman_a["total_revenue"], 350.0)

    def test_salesman_filter_changes_customer_monthly_and_channel_scope_only(self):
        rows = [
            order(1, date(2026, 1, 1), "客户A", "水果", channel="水果A", salesman="业务员A"),
            order(2, date(2026, 2, 2), "客户B", "水果", channel="水果B", salesman="业务员B"),
        ]
        analysis = build_acquisition_analysis(
            rows, date(2026, 1, 1), date(2026, 2, 28), category="水果",
            min_orders=1, min_new_customers=1,
        )

        detail = build_category_detail(analysis, rows, "水果", salesman="业务员A")

        self.assertEqual(len(detail["salesman_contribution"]["items"]), 2)
        self.assertEqual([item["name"] for item in detail["customer_contribution"]["items"]], ["客户A"])
        self.assertEqual([item["month"] for item in detail["monthly"]], ["2026-01"])
        self.assertEqual([item["name"] for item in detail["channels"]], ["水果A"])
        self.assertEqual(detail["dimension_scope"]["salesman_name"], "业务员A")
        self.assertEqual(detail["customer_contribution"]["summary"]["salesman_filter_name"], "业务员A")

    def test_non_positive_profit_denominator_has_no_concentration_percentage(self):
        rows = [
            order(1, date(2026, 1, 1), "客户A", "水果", fee=100, cost=0, salesman="业务员A"),
            order(2, date(2026, 1, 2), "客户B", "水果", fee=50, cost=80, salesman="业务员B"),
        ]
        analysis = build_acquisition_analysis(
            rows, date(2026, 1, 1), date(2026, 1, 31), category="水果",
            min_orders=1, min_new_customers=1,
        )

        detail = build_category_detail(analysis, rows, "水果")

        self.assertIsNone(detail["salesman_contribution"]["summary"]["top1_profit_concentration_pct"])
        self.assertIsNone(detail["customer_contribution"]["summary"]["top1_profit_concentration_pct"])
        self.assertTrue(all(item["profit_contribution_pct"] is None for item in detail["customer_contribution"]["items"]))
        self.assertTrue(all(item["profit_contribution_pct"] is None for item in detail["channels"]))

    def test_order_drilldown_filters_salesman_and_customer(self):
        rows = [
            order(1, date(2026, 1, 1), "客户A", "水果", salesman="业务员A"),
            order(2, date(2026, 1, 2), "客户B", "水果", salesman="业务员A"),
            order(3, date(2026, 1, 3), "客户A", "水果", salesman="业务员B"),
        ]

        details = build_order_drilldown(
            rows, "all", date(2026, 1, 1), date(2026, 1, 31),
            category="水果", salesman="业务员A", customer="客户A",
        )

        self.assertEqual([item["id"] for item in details], [1])
        self.assertEqual(details[0]["salesman"], "业务员A")


if __name__ == "__main__":
    unittest.main()
