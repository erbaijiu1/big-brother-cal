<template>
  <view class="rule-editor">
    <view v-for="(item, idx) in localRules" :key="idx" class="rule-edit-row">
      <uni-easyinput v-model="item.range" placeholder="区间 例:0-50" style="width:80px;" />
      <uni-easyinput v-model="item.unit_price" placeholder="单价" style="width:60px;" />
      <uni-easyinput v-model="item.base_fees" placeholder="首重价" style="width:60px;" />
      <uni-easyinput v-model="item.deduction_value" placeholder="首重值" style="width:60px;" />
      <uni-easyinput v-model="item.prize" placeholder="一口价" style="width:60px;" />
      <uni-easyinput v-model="item.prize_type" placeholder="单位" style="width:45px;" />
      <button @click="remove(idx)" size="mini" type="warn">删</button>
    </view>
    <button class="mini-btn success" style="margin-top:8px;" @click="add">新增区间</button>
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({
  modelValue: { type: Array, default: () => [] }
})
const emits = defineEmits(['update:modelValue'])
const localRules = ref(JSON.parse(JSON.stringify(props.modelValue || [])))
watch(
  () => props.modelValue,
  val => { localRules.value = JSON.parse(JSON.stringify(val || [])) }
)
watch(
  localRules,
  val => emits('update:modelValue', val),
  { deep: true }
)
function add() {
  localRules.value.push({
    range: "",
    unit_price: "",
    prize_type: "KG",
    base_fees: "",
    deduction_value: "",
    prize: ""
  })
}
function remove(idx) {
  localRules.value.splice(idx, 1)
}
</script>

<style scoped>
.rule-editor { font-size: 24rpx; color: #333; }
.rule-edit-row { display: flex; gap: 8rpx; align-items: center; margin-bottom: 8rpx; }
</style>
