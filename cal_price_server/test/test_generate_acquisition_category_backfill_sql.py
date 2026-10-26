import csv
import tempfile
import unittest
from pathlib import Path

from tool.generate_acquisition_category_backfill_sql import (
    export_runtime_mapping,
    generate_apply_sql,
    generate_rollback_sql,
    load_mappings,
    sql_text,
)


class GenerateAcquisitionCategoryBackfillSqlTest(unittest.TestCase):
    def test_unknown_and_low_confidence_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            preview = Path(directory) / "preview.csv"
            with preview.open("w", encoding="utf-8-sig", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=[
                    "raw_product_name", "normalized_category", "source", "confidence", "order_count",
                ])
                writer.writeheader()
                writer.writerow({"raw_product_name": "芒果", "normalized_category": "水果", "source": "rule", "confidence": "1", "order_count": "11"})
                writer.writerow({"raw_product_name": "观赏鱼", "normalized_category": "普货", "source": "llm", "confidence": "0.8", "order_count": "44"})
                writer.writerow({"raw_product_name": "生", "normalized_category": "UNKNOWN", "source": "unknown", "confidence": "0", "order_count": "149"})

            rows = load_mappings(preview, 0.9)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].raw_product_name, "芒果")

    def test_generated_sql_is_exact_and_reversible(self):
        with tempfile.TemporaryDirectory() as directory:
            preview = Path(directory) / "preview.csv"
            with preview.open("w", encoding="utf-8-sig", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=[
                    "raw_product_name", "normalized_category", "source", "confidence", "order_count",
                ])
                writer.writeheader()
                writer.writerow({"raw_product_name": "芒果'特选", "normalized_category": "水果", "source": "rule", "confidence": "1", "order_count": "2"})
            rows = load_mappings(preview, 0.9)

        apply_sql = generate_apply_sql(rows, "test_v1", "digest")
        rollback_sql = generate_rollback_sql(rows, "test_v1")

        self.assertIn(sql_text("芒果'特选"), apply_sql)
        self.assertIn("changed_rows <> 2", apply_sql)
        self.assertIn("z_bak_acq_product_test_v1", rollback_sql)
        self.assertIn("只恢复 product_name", rollback_sql)

    def test_runtime_mapping_can_be_loaded_as_versioned_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            preview = Path(directory) / "preview.csv"
            mapping = Path(directory) / "mapping.csv"
            with preview.open("w", encoding="utf-8-sig", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=[
                    "raw_product_name", "normalized_category", "source", "confidence", "order_count",
                ])
                writer.writeheader()
                writer.writerow({"raw_product_name": "芒果", "normalized_category": "水果", "source": "rule", "confidence": "1", "order_count": "11"})

            rows = load_mappings(preview, 0.9)
            export_runtime_mapping(rows, mapping)
            written = list(csv.DictReader(mapping.open(encoding="utf-8-sig")))

        self.assertEqual(written[0]["raw_product_name"], "芒果")
        self.assertEqual(written[0]["normalized_category"], "水果")


if __name__ == "__main__":
    unittest.main()
