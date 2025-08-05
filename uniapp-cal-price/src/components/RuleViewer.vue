<template>
  <view class="rule-viewer">
    <view v-for="(item, idx) in parsedRules" :key="idx" class="rule-item">
      <text v-if="item.prize">一口价【{{ item.range }}】：{{ item.prize }}元</text>
      <text v-else-if="item.base_fees && item.deduction_value">
        首重{{ item.deduction_value }}{{ item.prize_type || '' }}【{{ item.range }}】：{{ item.base_fees }}元，超出{{ item.unit_price }}元/{{ item.prize_type || '单位' }}
      </text>
      <text v-else>
        区间【{{ item.range }}】：{{ item.unit_price }}/{{ item.prize_type || '单位' }}
      </text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  rules: { type: [Array, String], required: true }
})
const parsedRules = computed(() => {
  if (!props.rules) return []
  try {
    return typeof props.rules === 'string' ? JSON.parse(props.rules) : props.rules
  } catch { return [] }
})
</script>

<style scoped>
.rule-viewer { font-size: 24rpx; color: #444; }
.rule-item + .rule-item { margin-top: 10rpx; }
</style>
