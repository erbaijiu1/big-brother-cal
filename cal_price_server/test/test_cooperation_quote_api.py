import os
import sys
import unittest
from datetime import datetime
from types import SimpleNamespace

from fastapi import HTTPException


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.for_inner.customer_quote_api import (
    _serialize_cooperation_quote,
    list_cooperation_quotes,
)


class TestCooperationQuoteApi(unittest.TestCase):
    def test_serializer_returns_customer_fields_and_category_policy(self):
        config = SimpleNamespace(
            enabled=True,
            currency="CNY",
            price_tiers=(
                '[{"min_quantity":1,"max_quantity":1000,'
                '"min_price":1,"max_price":2,"unit":"kg"}]'
            ),
            delivery_base_fee=150,
            delivery_included_weight=300,
            delivery_excess_rate=0.3,
            sea_crossing_notice="港岛过海按区域计费",
            upstairs_notice="上楼按地址计费",
            cutoff_text="17点前入仓",
            eta_text="次日派送",
            customer_notice="",
            config_updated_at=datetime(2026, 8, 21, 10, 0, 0),
        )
        category = SimpleNamespace(
            category_id=9,
            main_category="普货 & 日杂",
            warehouse_acceptance_policy="AUTO_ACCEPT",
            acceptance_notice="",
        )

        result = _serialize_cooperation_quote(config, category)

        self.assertEqual(result["category_id"], 9)
        self.assertEqual(result["price_tiers"][0]["min_price"], 1.0)
        self.assertEqual(result["delivery_included_weight"], 300)
        self.assertEqual(result["acceptance_policy"], "AUTO_ACCEPT")

    def test_invalid_category_ids_are_rejected_instead_of_returning_all_quotes(self):
        with self.assertRaises(HTTPException) as error:
            list_cooperation_quotes("9,unknown", db=None)

        self.assertEqual(error.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
