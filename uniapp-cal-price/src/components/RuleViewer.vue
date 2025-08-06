<template>
  <view class="rule-viewer">
    <view class="viewer-table-head">
      <text class="col-range">区间</text>
      <text class="col-price">单价</text>
      <text class="col-type">单位</text>
      <text class="col-base">基础费</text>
      <text class="col-deduct">扣减</text>
      <text class="col-prize">一口价</text>
    </view>
    <view v-for="(rule, idx) in rules" :key="idx" class="viewer-row">
      <text class="col-range">{{ rule.range }}</text>
      <text class="col-price">{{ rule.unit_price || '-' }}</text>
      <text class="col-type">{{ rule.prize_type }}</text>
      <text class="col-base">{{ rule.base_fees || '-' }}</text>
      <text class="col-deduct">{{ rule.deduction_value || '-' }}</text>
      <text class="col-prize">{{ rule.prize || '-' }}</text>
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  rules: { type: Array, default: () => [] }
})
</script>

<style scoped>
.viewer-table-head,
.viewer-row {
  display: flex;
  align-items: center;
  font-size: 26rpx;
  margin-bottom: 8rpx;
}
.viewer-table-head { font-weight: bold; background: #f6f8fa; }
.col-range  { flex: 1 1 160rpx; }
.col-price  { flex: 1 1 120rpx; text-align: center; }
.col-type   { flex: 0 0 70rpx; text-align: center; }
.col-base   { flex: 1 1 100rpx; text-align: center; }
.col-deduct { flex: 1 1 100rpx; text-align: center; }
.col-prize  { flex: 1 1 100rpx; text-align: center; }
</style>
