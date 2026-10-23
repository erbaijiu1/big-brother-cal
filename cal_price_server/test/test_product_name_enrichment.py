import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


TOOL_PATH = Path(__file__).resolve().parents[1] / "tool" / "product_name_enrichment.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("product_name_enrichment", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProductNameEnrichmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_extracts_description_from_retained_legacy_row(self):
        raw_values = [None] * 16
        raw_values[15] = "  17件茅台，缠黑膜打木架\r\n  "
        raw_row = ["row-id", {}, raw_values]

        self.assertEqual(
            self.tool.extract_consignment_description(json.dumps(raw_row, ensure_ascii=False)),
            "17件茅台，缠黑膜打木架",
        )

    def test_specific_rules_run_before_broad_rules(self):
        self.assertEqual(self.tool.classify_with_rules("50箱葡萄酒")[0], "酒类")
        self.assertEqual(self.tool.classify_with_rules("榴莲冰皮月饼")[0], "食品")
        self.assertEqual(self.tool.classify_with_rules("50箱菠萝浆")[0], "食品")
        self.assertEqual(self.tool.classify_with_rules("熟冻品丸子")[0], "熟食")

    def test_operational_descriptions_remain_unknown(self):
        self.assertIsNone(self.tool.classify_with_rules("正报"))
        self.assertIsNone(self.tool.classify_with_rules("在仓全部出"))
        self.assertIsNone(self.tool.classify_with_rules("第八批正报"))
        self.assertIsNone(self.tool.classify_with_rules("包车2"))
        self.assertIsNone(self.tool.classify_with_rules("132+42+190=364件"))
        self.assertTrue(self.tool.is_non_product_description("第八批正报"))
        self.assertTrue(self.tool.is_non_product_description("132+42+190=364件"))
        self.assertFalse(self.tool.is_non_product_description("50箱芒果，包车出货"))

    def test_rules_resolve_before_llm_and_reject_low_confidence(self):
        class FakeClassifier:
            def classify(self, descriptions):
                return {
                    "观赏兰花": ("普货", 0.95),
                    "看不清": ("食品", 0.5),
                }

        candidates = [
            self.tool.ProductCandidate(1, "A", "进口面粉"),
            self.tool.ProductCandidate(2, "B", "观赏兰花"),
            self.tool.ProductCandidate(3, "C", "看不清"),
            self.tool.ProductCandidate(4, "D", None),
        ]

        resolutions = self.tool.resolve_product_names(candidates, FakeClassifier())

        self.assertEqual(
            [(item.performance_id, item.product_name, item.source) for item in resolutions],
            [(1, "食品", "rule"), (2, "普货", "llm")],
        )

    def test_llm_classifier_accepts_only_allowed_high_confidence_results(self):
        response = Mock()
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "items": [
                                    {"key": "item_0", "product_name": "水产海鲜", "confidence": 0.96},
                                    {"key": "item_1", "product_name": "食品", "confidence": 0.4},
                                    {"key": "item_2", "product_name": "危险品", "confidence": 0.99},
                                ]
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ]
        }
        classifier = self.tool.LlmProductClassifier("https://llm.example/v1", "secret", "test-model")

        with patch.object(self.tool.requests, "post", return_value=response):
            classified = classifier.classify(["冻海参", "模糊货物", "越界货物"])

        self.assertEqual(classified, {"冻海参": ("水产海鲜", 0.96)})
        response.raise_for_status.assert_called_once()



if __name__ == "__main__":
    unittest.main()
