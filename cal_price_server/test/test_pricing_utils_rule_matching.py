
import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
import types

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock external dependencies that might be missing
mock_fastapi = types.ModuleType("fastapi")
mock_fastapi.HTTPException = Exception
sys.modules["fastapi"] = mock_fastapi

mock_pydantic = types.ModuleType("pydantic")
class MockBaseModel:
    pass
mock_pydantic.BaseModel = MockBaseModel
mock_pydantic.Field = lambda *args, **kwargs: None
sys.modules["pydantic"] = mock_pydantic

# Mock config if needed (assuming it might be missing or rely on env vars)
# sys.modules["config"] = MagicMock() 

from server_mgr import pricing_utils

class TestRegionRuleMatching(unittest.TestCase):
    
    def setUp(self):
        # Mock the DB functions used in match_area_category
        self.patcher1 = patch('server_mgr.pricing_utils.get_sub_districts_by_category_id')
        self.mock_get_subs = self.patcher1.start()
        
        # Setup common mock data
        self.mock_get_subs.return_value = [{'sub_district_id': "SUB_001"}, {'sub_district_id': "SUB_002"}]

    def tearDown(self):
        self.patcher1.stop()

    def test_old_format_district_match(self):
        """Test matching with the old flat structure (district match)"""
        rule = {
            "regionType": "district",
            "regionIds": ["100", "101"],
            "unit_price_rules": [{"test": "old_match"}]
        }
        rules_json = json.dumps([rule])
        
        extra_data = {"district": "100"}
        u_rules, d_rules = pricing_utils.get_region_rules(rules_json, extra_data)
        
        self.assertEqual(u_rules, [{"test": "old_match"}])

    def test_old_format_sub_district_match(self):
        """Test matching with the old flat structure (sub_district match)"""
        rule = {
            "regionType": "sub_district",
            "regionIds": ["SUB_A", "SUB_B"],
            "unit_price_rules": [{"test": "old_sub_match"}]
        }
        rules_json = json.dumps([rule])
        
        extra_data = {"sub_district": "SUB_B"}
        u_rules, d_rules = pricing_utils.get_region_rules(rules_json, extra_data)
        
        self.assertEqual(u_rules, [{"test": "old_sub_match"}])

    def test_new_format_single_conf_match(self):
        """Test matching with new region_conf structure (single valid config)"""
        rule = {
            "region_conf": [
                {
                    "regionType": "district",
                    "regionIds": ["200"]
                }
            ],
            "unit_price_rules": [{"test": "new_match"}]
        }
        rules_json = json.dumps([rule])
        
        extra_data = {"district": "200"}
        u_rules, d_rules = pricing_utils.get_region_rules(rules_json, extra_data)
        
        self.assertEqual(u_rules, [{"test": "new_match"}])

    def test_new_format_multi_conf_any_match(self):
        """Test matching with new region_conf structure (multiple configs, OR logic)"""
        rule = {
            "region_conf": [
                {
                    "regionType": "district",
                    "regionIds": ["300"] # No match
                },
                {
                    "regionType": "sub_district",
                    "regionIds": ["SUB_X", "SUB_Y"] # Match here
                }
            ],
            "unit_price_rules": [{"test": "multi_match"}]
        }
        rules_json = json.dumps([rule])
        
        extra_data = {"district": "999", "sub_district": "SUB_Y"}
        u_rules, d_rules = pricing_utils.get_region_rules(rules_json, extra_data)
        
        self.assertEqual(u_rules, [{"test": "multi_match"}])

    def test_new_format_area_category_match(self):
        """Test matching with area_category in new structure"""
        # Mock setup handles get_sub_districts_by_category_id -> returns SUB_001, SUB_002
        rule = {
            "region_conf": [
                 {
                    "regionType": "area_category",
                    "regionIds": ["50"]
                }
            ],
            "unit_price_rules": [{"test": "cat_match"}]
        }
        rules_json = json.dumps([rule])
        
        extra_data = {"sub_district": "SUB_001"}
        u_rules, d_rules = pricing_utils.get_region_rules(rules_json, extra_data)
        
        self.assertEqual(u_rules, [{"test": "cat_match"}])

    def test_no_match(self):
        """Test when no rules match"""
        rule = {
            "region_conf": [
                {
                    "regionType": "district",
                    "regionIds": ["999"]
                }
            ],
            "unit_price_rules": [{"test": "fail"}]
        }
        rules_json = json.dumps([rule])
        
        extra_data = {"district": "100"}
        u_rules, d_rules = pricing_utils.get_region_rules(rules_json, extra_data)
        
        self.assertEqual(u_rules, [])

if __name__ == '__main__':
    unittest.main()
