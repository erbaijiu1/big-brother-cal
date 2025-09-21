<template>
    <view class="rule-viewer">
        <view class="viewer-table-head">
            <text class="col-unit">计价方式</text>
            <!-- <text class="col-type">计价方式</text> -->
            <text class="col-range">区间范围</text>
            <text class="col-desc">价格说明</text>
        </view>
        <view v-for="(rule, idx) in ruleArr" :key="idx" class="viewer-row">
            <text class="col-unit">{{ rule.prize_type || '-' }}</text>
            <!-- <text class="col-type">{{ rule.prize ? '一口价' : '按区间' }}</text> -->
            <text class="col-range">{{ rule.range || '-' }}</text>
            <text class="col-desc">{{ getPriceDesc(rule) }}</text>
        </view>
    </view>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
    rules: { type: [Array, String], default: () => [] }
})

// 兼容数组/字符串
const ruleArr = computed(() => {
    if (Array.isArray(props.rules)) return props.rules
    if (typeof props.rules === 'string') {
        try {
            const arr = JSON.parse(props.rules)
            return Array.isArray(arr) ? arr : []
        } catch { return [] }
    }
    return []
})

function getPriceDesc(rule) {
    if (rule.prize) {
        return `一口价 ${rule.prize} 元`
    }
    let desc = []
    if (rule.unit_price !== undefined) desc.push(`单价 ${rule.unit_price} 元/${rule.prize_type || ''}`)
    //   if (rule.base_fees !== undefined) desc.push(`基础费 ${rule.base_fees} 元`)
    if (rule.deduction_value !== undefined && rule.base_fees !== undefined) 
        desc.push(`${rule.base_fees} 元 含 ${rule.deduction_value}${rule.prize_type || ''}`)
    return desc.length ? desc.join('，') : '-'
}
</script>

<style scoped>
.viewer-table-head,
.viewer-row {
    display: flex;
    align-items: center;
    font-size: 26rpx;
    margin-bottom: 8rpx;
}

.viewer-table-head {
    font-weight: bold;
    background: #f6f8fa;
}

.viewer-table-head text, .viewer-row text {
  padding: 0 6rpx;
}

.col-unit {
    flex: 0 0 120rpx;
}

.col-type {
    flex: 0 0 120rpx;
}

.col-range {
    flex: 1 1 250rpx;
}

.col-desc {
    flex: 3 3 800rpx;
    color: #34495e;
}
</style>
