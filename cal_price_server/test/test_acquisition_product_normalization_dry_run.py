import unittest

from tool.acquisition_product_normalization_dry_run import (
    NormalizationResult,
    ProductImpact,
    review_priority,
    summary,
)


class AcquisitionProductNormalizationDryRunTest(unittest.TestCase):
    def test_unknown_is_always_manual_p0(self):
        priority, reason = review_priority(2943, NormalizationResult("方樽", "UNKNOWN", "unknown", 0))

        self.assertEqual(priority, "P0")
        self.assertIn("人工", reason)

    def test_summary_keeps_unknown_separate_from_general_cargo(self):
        impacts = [
            ProductImpact("芒果", 8, 1000, 300, 0),
            ProductImpact("无法判断", 5, 500, 100, 0),
        ]
        results = {
            "芒果": NormalizationResult("芒果", "水果", "llm", 0.99),
            "无法判断": NormalizationResult("无法判断", "UNKNOWN", "unknown", 0),
        }

        result = summary(impacts, results)

        self.assertEqual(result["category_order_counts"]["水果"], 8)
        self.assertEqual(result["category_order_counts"]["UNKNOWN"], 5)
        self.assertNotIn("普货", result["category_order_counts"])


if __name__ == "__main__":
    unittest.main()
