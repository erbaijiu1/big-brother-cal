<template>
  <view class="rule-editor">
    <view class="editor-table-head">
      <text class="col-range">区间</text>
      <text class="col-price">单价</text>
      <text class="col-type">单位</text>
      <text class="col-base">基础费</text>
      <text class="col-deduct">扣减</text>
      <text class="col-prize">一口价</text>
      <text class="col-action"></text>
    </view>
    <view v-for="(rule, idx) in localRules" :key="idx" class="editor-row">
      <input class="col-range" v-model="rule.range" placeholder="如0-50" />
      <input class="col-price" v-model="rule.unit_price" type="number" placeholder="单价" />
      <picker
        class="col-type"
        :range="['KG', 'CBM']"
        :value="['KG', 'CBM'].indexOf(rule.prize_type)"
        @change="e => rule.prize_type = ['KG', 'CBM'][e.detail.value]"
      >
        <view>{{ rule.prize_type || '单位' }}</view>
      </picker>
      <input class="col-base" v-model="rule.base_fees" type="number" placeholder="基础费" />
      <input class="col-deduct" v-model="rule.deduction_value" type="number" placeholder="扣减" />
      <input class="col-prize" v-model="rule.prize" type="number" placeholder="一口价" />
      <view class="col-action">
        <button size="mini" type="warn" plain @click="removeRule(idx)">删</button>
      </view>
    </view>

    <view class="rule-add-row">
      <button size="mini" type="primary" plain @click="addRule">添加一条规则</button>
    </view>
    <view class="rule-save-row">
      <button size="default" type="success" @click="saveRules">保存规则</button>
    </view>
  </view>
</template>

<script setup>
import { reactive, watch, toRefs } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] }
})
const emits = defineEmits(['update:modelValue', 'save'])

const localRules = reactive(
  (Array.isArray(props.modelValue) ? JSON.parse(JSON.stringify(props.modelValue)) : [])
)

watch(
  () => props.modelValue,
  (val) => {
    // 保持与外部同步
    if (JSON.stringify(val) !== JSON.stringify(localRules)) {
      localRules.splice(0, localRules.length, ...(val || []))
    }
  }
)

function addRule() {
  localRules.push({
    range: '',
    unit_price: '',
    prize_type: 'KG',
    base_fees: '',
    deduction_value: '',
    prize: ''
  })
}
function removeRule(idx) {
  localRules.splice(idx, 1)
}
function saveRules() {
  // 简单校验
  for (let r of localRules) {
    if (!r.range || !r.prize_type) {
      uni.showToast({ title: '请填写完整区间和单位', icon: 'none' })
      return
    }
  }
  emits('update:modelValue', JSON.parse(JSON.stringify(localRules)))
  emits('save', JSON.parse(JSON.stringify(localRules)))
  uni.showToast({ title: '规则已保存', icon: 'success' })
}
</script>

<style scoped>
.editor-table-head,
.editor-row {
  display: flex;
  align-items: center;
  font-size: 26rpx;
  margin-bottom: 8rpx;
}
.editor-table-head { font-weight: bold; background: #f6f8fa; }
.col-range  { flex: 1 1 160rpx; }
.col-price  { flex: 1 1 120rpx; text-align: center; }
.col-type   { flex: 0 0 70rpx; text-align: center; }
.col-base   { flex: 1 1 100rpx; text-align: center; }
.col-deduct { flex: 1 1 100rpx; text-align: center; }
.col-prize  { flex: 1 1 100rpx; text-align: center; }
.col-action { flex: 0 0 56rpx; text-align: right; }
.rule-add-row { text-align: left; margin: 16rpx 0 8rpx 0; }
.rule-save-row { text-align: right; margin: 16rpx 0 8rpx 0; }
input { border: 1px solid #eee; border-radius: 6rpx; padding: 4rpx 10rpx; font-size: 26rpx; background: #fff; width: 90%; }
.picker { border: 1px solid #eee; border-radius: 6rpx; background: #fafbfc; padding: 4rpx 0; text-align: center; }
button { margin-left: 4rpx; }
</style>
