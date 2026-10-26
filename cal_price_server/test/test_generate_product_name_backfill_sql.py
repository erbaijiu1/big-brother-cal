import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tool.generate_product_name_backfill_sql import generate_apply_sql, load_rows


class GenerateProductNameBackfillSqlTest(unittest.TestCase):
    def write_preview(self, rows):
        temp_dir = tempfile.TemporaryDirectory()
        path = Path(temp_dir.name) / "preview.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(
                output,
                fieldnames=["performance_id", "description", "product_name", "source", "confidence"],
            )
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(temp_dir.cleanup)
        return path

    def test_filters_only_low_confidence_llm_rows(self):
        path = self.write_preview(
            [
                {"performance_id": 1, "description": "芒果", "product_name": "水果", "source": "rule", "confidence": 1},
                {"performance_id": 2, "description": "金桔", "product_name": "水果", "source": "llm", "confidence": 0.9},
                {"performance_id": 3, "description": "糍粑", "product_name": "食品", "source": "llm", "confidence": 0.85},
            ]
        )

        rows = load_rows(path, 0.9)

        self.assertEqual([row.performance_id for row in rows], [1, 2])

    def test_generated_sql_validates_temporary_plan_before_persistent_backup(self):
        path = self.write_preview(
            [{"performance_id": 8, "description": "芒果", "product_name": "水果", "source": "rule", "confidence": 1}]
        )
        rows = load_rows(path, 0.9)

        sql = generate_apply_sql(rows, "20261026", "digest")

        self.assertLess(
            sql.index("CREATE TEMPORARY TABLE `tmp_product_name_20261026`"),
            sql.index("CREATE TABLE IF NOT EXISTS `z_plan_product_name_20261026`"),
        )
        self.assertIn("WHERE NULLIF(TRIM(performance.`product_name`), '') IS NULL", sql)
        self.assertIn("IF changed_rows <> 1", sql)


if __name__ == "__main__":
    unittest.main()
