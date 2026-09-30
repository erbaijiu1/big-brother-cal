import base64
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


TOOL_PATH = Path(__file__).resolve().parents[1] / "tool" / "get_all_trade_info.py"


def load_tool(dataset_type="consignment"):
    with patch.dict(os.environ, {"DATASET_TYPE": dataset_type}, clear=False):
        spec = importlib.util.spec_from_file_location("get_all_trade_info_tool", TOOL_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def encoded_response(payload):
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    return f"JsonStr:{encoded}"


class ImportTradeDataToolTest(unittest.TestCase):
    def test_request_matches_current_legacy_system_contract(self):
        tool = load_tool()
        response = SimpleNamespace(status_code=200, text="ok")

        with (
            patch.object(tool, "PHPSESSID", "test-session"),
            patch.object(tool.requests, "post", return_value=response) as post_request,
        ):
            self.assertEqual(tool.fetch_page(page_num=6), "ok")

        request_url = post_request.call_args.args[0]
        request_options = post_request.call_args.kwargs
        request_data = json.loads(
            base64.b64decode(request_options["data"]).decode("utf-8")
        )

        self.assertEqual(
            request_url,
            "https://gzjsjy.s1.office7x.cn/SOA/WorkSpace.phtml",
        )
        self.assertEqual(
            request_options["headers"]["Origin"],
            "https://gzjsjy.s1.office7x.cn",
        )
        self.assertEqual(
            request_options["headers"]["Referer"],
            "https://gzjsjy.s1.office7x.cn/Apps/Custom_logisticsAccountingPublicitySystem/ConsignmentBooking_index.phtml",
        )
        self.assertEqual(request_options["cookies"], {"PHPSESSID": "test-session"})
        self.assertTrue(request_options["verify"])
        self.assertEqual(request_data["dsCode"], "T0020142")
        self.assertEqual(request_data["Serch"], {})
        self.assertNotIn("Search", request_data)
        self.assertEqual(request_data["PageRows"], 50)
        self.assertEqual(request_data["PageNo"], 6)

    def test_request_retries_after_timeout(self):
        tool = load_tool(dataset_type="performance")
        response = SimpleNamespace(status_code=200, text="ok")

        with (
            patch.object(tool, "PHPSESSID", "test-session"),
            patch.object(tool, "REQUEST_MAX_RETRIES", 2),
            patch.object(tool, "REQUEST_RETRY_INTERVAL_SECONDS", 0),
            patch.object(
                tool.requests,
                "post",
                side_effect=[tool.requests.Timeout("slow response"), response],
            ) as post_request,
        ):
            self.assertEqual(tool.fetch_page(page_num=135), "ok")

        self.assertEqual(post_request.call_count, 2)

    def test_performance_request_uses_its_own_data_source_and_group(self):
        tool = load_tool(dataset_type="performance")
        response = SimpleNamespace(status_code=200, text="ok")

        with (
            patch.object(tool, "PHPSESSID", "test-session"),
            patch.object(tool.requests, "post", return_value=response) as post_request,
        ):
            self.assertEqual(tool.fetch_page(page_num=2), "ok")

        request_options = post_request.call_args.kwargs
        request_data = json.loads(
            base64.b64decode(request_options["data"]).decode("utf-8")
        )
        self.assertEqual(
            request_options["headers"]["Referer"],
            "https://gzjsjy.s1.office7x.cn/Apps/Custom_logisticsAccountingPublicitySystem/PerformanceStatement_index.phtml",
        )
        self.assertEqual(
            request_data["DataFile"],
            "Apps/Custom_logisticsAccountingPublicitySystem/PerformanceStatement",
        )
        self.assertEqual(request_data["dsCode"], "T00200DE")
        self.assertEqual(request_data["GroupID"], "-1:0")
        self.assertEqual(request_data["PageNo"], 2)

    def test_dry_run_exports_without_writing_database(self):
        tool = load_tool()
        payload = {
            "PageNo": 1,
            "Pages": 1,
            "TableTitle": [{"colID": 0, "FieldName": "排单编号"}],
            "DataList": [["row-1", None, ["D001"], {"Text": "D001"}]],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            with (
                patch.object(tool, "DRY_RUN", True),
                patch.object(tool, "OUTPUT_DIR", output_dir),
                patch.object(tool, "CHECKPOINT_FILE", output_dir / "checkpoint.json"),
                patch.object(tool, "fetch_page", return_value=encoded_response(payload)),
                patch.object(tool, "save_records_to_db") as save_records,
                patch.object(tool, "save_checkpoint") as save_checkpoint,
            ):
                tool.run_paginated_ingest(start_page=1, max_pages=1, resume=False)

            save_records.assert_not_called()
            save_checkpoint.assert_not_called()
            csv_path = output_dir / "consignment_page_1.csv"
            self.assertTrue(csv_path.exists())
            self.assertIn("D001", csv_path.read_text(encoding="utf-8-sig"))

    def test_database_ingest_does_not_export_csv_by_default(self):
        tool = load_tool()
        payload = {
            "PageNo": 1,
            "Pages": 1,
            "TableTitle": [{"colID": 0, "FieldName": "排单编号"}],
            "DataList": [["row-1", None, ["D001"], {"Text": "D001"}]],
        }

        with (
            patch.object(tool, "DRY_RUN", False),
            patch.object(tool, "EXPORT_CSV", False),
            patch.object(tool, "fetch_page", return_value=encoded_response(payload)),
            patch.object(tool, "export_page_csv") as export_page_csv,
            patch.object(tool, "save_records_to_db", return_value=1) as save_records,
            patch.object(tool, "save_checkpoint"),
            patch.object(tool, "clear_checkpoint"),
        ):
            tool.run_paginated_ingest(start_page=1, max_pages=0, resume=False)

        export_page_csv.assert_not_called()
        save_records.assert_called_once()
