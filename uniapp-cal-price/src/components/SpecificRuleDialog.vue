<template>
  <uni-popup ref="popupRef" type="center" :mask-click="false">
    <view class="popup-card popup-lg">
      <view class="popup-head">
        <text class="popup-title">{{ isEdit ? '编辑区域规则' : '新增区域规则' }}</text>
        <uni-icons type="closeempty" size="20" @click="close" color="#666"></uni-icons>
      </view>

      <view class="popup-body">
        <!-- 1. 区域选择 -->
        <view class="section">
          <view class="section-title">选择适用区域</view>
          <view class="region-selector-wrapper">
             <RegionSelector
               v-model="selectedRegions"
               :exclusiveType="false"
             />
          </view>
        </view>

        <!-- 2. 费用规则 -->
        <view class="section">
          <view class="section-title">费用配置</view>
          
          <view class="editor-block">
            <view class="block-title">运费规则</view>
            <RuleFeeEditor
              ref="unitPriceRef"
              v-model="unitPriceRules"
              dense
            />
          </view>

          <view class="editor-block">
            <view class="block-title">派送费规则</view>
            <RuleFeeEditor
              ref="deliveryFeeRef"
              v-model="deliveryFeeRules"
              dense
            />
          </view>
        </view>
        
        <view class="popup-actions">
           <button size="mini" @click="close">取消</button>
           <button size="mini" type="primary" @click="confirm">确定</button>
        </view>
      </view>
    </view>
  </uni-popup>
</template>

<script setup>
import { ref, reactive, nextTick } from 'vue'
import RegionSelector from '@/components/RegionSelector.vue'
import RuleFeeEditor from '@/components/RuleFeeEditor.vue'

const popupRef = ref(null)
const unitPriceRef = ref(null)
const deliveryFeeRef = ref(null)

const isEdit = ref(false)
const selectedRegions = ref([])
const unitPriceRules = ref([])
const deliveryFeeRules = ref([])

// 供父组件调用打开
function open(ruleData = null) {
  if (ruleData) {
    isEdit.value = true
    // 解析 ruleData
    // ruleData 结构预期：
    // {
    //   region_conf: [ { regionType: '...', regionIds: [...] }, ... ],
    //   unit_price_rules: [...],
    //   delivery_fee_rules: [...]
    // }
    
    // 还原 Regions
    const flatRegions = []
    if (Array.isArray(ruleData.region_conf)) {
      ruleData.region_conf.forEach(conf => {
        const type = conf.regionType
        if (Array.isArray(conf.regionIds)) {
            conf.regionIds.forEach(id => {
               flatRegions.push({ id, type })
            })
        }
      })
    }
    selectedRegions.value = flatRegions
    
    // 还原 Rules
    unitPriceRules.value = JSON.parse(JSON.stringify(ruleData.unit_price_rules || []))
    deliveryFeeRules.value = JSON.parse(JSON.stringify(ruleData.delivery_fee_rules || []))
    
  } else {
    isEdit.value = false
    selectedRegions.value = []
    unitPriceRules.value = []
    deliveryFeeRules.value = []
  }

  popupRef.value.open()
}

function close() {
  popupRef.value.close()
}

const emit = defineEmits(['confirm'])

async function confirm() {
  // 1. 校验区域
  if (selectedRegions.value.length === 0) {
    uni.showToast({ title: '请至少选择一个区域', icon: 'none' })
    return
  }

  // 2. 校验并获取 RuleFeeEditor 的数据
  // save(true) 表示 silent save: 如果为空(empty=true)则不弹提示; 如果校验不通过则仍弹提示
  const uRes = unitPriceRef.value ? unitPriceRef.value.save(true) : { ok: true, data: [] }
  const dRes = deliveryFeeRef.value ? deliveryFeeRef.value.save(true) : { ok: true, data: [] }

  // 2.1 检查是否存在校验错误 (有数据但不合法)
  // 如果 result.ok=false 且 result.empty=false/undefined，说明是数据校验未通过(child已弹窗)
  if ((!uRes.ok && !uRes.empty) || (!dRes.ok && !dRes.empty)) {
      return
  }
  
  // 2.2 检查是否两者都为空
  const uEmpty = !uRes.ok && uRes.empty
  const dEmpty = !dRes.ok && dRes.empty
  
  if (uEmpty && dEmpty) {
      uni.showToast({ title: '请至少配置运费或派送费规则', icon: 'none' })
      return
  }
  
  // 3. 构造数据
  const finalRegions = selectedRegions.value
  const finalUnitRules = uRes.ok ? uRes.data : []
  const finalDeliveryRules = dRes.ok ? dRes.data : []

  // 4. Transform regions to region_conf structure
  // groupBy regionType
  const confMap = {}
  finalRegions.forEach(item => {
      if (!confMap[item.type]) {
          confMap[item.type] = []
      }
      confMap[item.type].push(item.id)
  })
  
  const region_conf = Object.keys(confMap).map(type => ({
      regionType: type,
      regionIds: confMap[type]
  }))

  const payload = {
    region_conf,
    unit_price_rules: finalUnitRules,
    delivery_fee_rules: finalDeliveryRules,
    surcharge_fee_rules: [] // 暂不处理
  }

  emit('confirm', payload)
  close()
}

defineExpose({ open, close })
</script>

<style scoped>
.popup-card {
  background: #fff;
  border-radius: 12rpx;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}
.popup-lg {
  width: 90vw;
  /* max-width: 800px; */
}
.popup-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx;
  border-bottom: 1px solid #eee;
}
.popup-title {
  font-size: 32rpx;
  font-weight: bold;
}
.popup-body {
  padding: 20rpx;
  overflow-y: auto;
  flex: 1;
}
.section {
  margin-bottom: 30rpx;
}
.section-title {
  font-weight: bold;
  font-size: 28rpx;
  margin-bottom: 16rpx;
  padding-left: 10rpx;
  border-left: 4px solid #007aff;
}
.region-selector-wrapper {
  border: 1px solid #f0f0f0;
  padding: 10rpx;
  border-radius: 8rpx;
}
.editor-block {
  margin-bottom: 20rpx;
  padding: 16rpx;
  background: #f9f9f9;
  border-radius: 8rpx;
}
.block-title {
  font-weight: 600;
  margin-bottom: 10rpx;
  color: #666;
}
.popup-actions {
  display: flex;
  justify-content: flex-end;
  gap: 20rpx;
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1px solid #eee;
}
</style>
