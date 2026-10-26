import unittest

from tool.product_category_normalizer import (
    load_approved_mapping,
    normalize_product_category,
    resolve_product_category,
)


class ProductCategoryNormalizerTest(unittest.TestCase):
    def test_versioned_mapping_contains_approved_dry_run_results(self):
        mapping = load_approved_mapping()

        # 2,587 reviewed source rows collapse to 2,581 effective aliases after
        # whitespace/punctuation normalization.
        self.assertEqual(len(mapping), 2581)
        self.assertEqual(mapping["芒果"].category, "水果")

    def test_canonical_category_is_preserved(self):
        resolution = resolve_product_category("熟食")

        self.assertEqual(resolution.category, "熟食")
        self.assertEqual(resolution.source, "canonical")

    def test_only_confident_descriptions_are_normalized(self):
        self.assertEqual(normalize_product_category("50箱葡萄酒"), "酒类")
        self.assertIsNone(normalize_product_category("生"))
        self.assertIsNone(normalize_product_category("完全无法识别的新货物"))


if __name__ == "__main__":
    unittest.main()
