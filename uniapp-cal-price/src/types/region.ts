export interface Region {
  id: string;
  name: string;
  type: RegionType;
  children?: Region[];
}

export type RegionType = 'category' | 'district' | 'sub_district';

export interface RegionRule {
  regionType: RegionType;
  regionIds: string[];
  unit_price_rules: FeeRuleRow[];
  surcharge_fee_rules: FeeRuleRow[];
  delivery_fee_rules: FeeRuleRow[];
  isDefault: boolean;
}

export interface FeeRuleRow {
  range?: string;
  _min?: string;
  _max?: string;
  unit_price?: string;
  _prize?: string;
  base_fees?: string;
  deduction_value?: string;
  _minimum_unit?: string;
  prize_type?: 'KG' | 'CBM' | 'PCS';
}