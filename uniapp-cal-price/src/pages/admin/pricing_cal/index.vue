<template>
  <view class="price-container">
    <!-- 使用公共价格表单组件 -->
    <PriceForm 
      submit-text="我要查价"
      api-endpoint="/cal_price/inner_query/min_pricing"
      :use-request-util="true"
      @form-change="onFormChange"
      @submit-success="onSubmitSuccess"
      @submit-error="onSubmitError"
    />

    <!-- 报价结果弹窗 -->
    <PriceResult 
      ref="resultPopup" 
      :result-list="resultList" 
      :need-go-upstairs="needGoUpstairs" 
    />

    <WechatFab ref="fab" />
  </view>
</template>

<script>
import PriceForm from '@/components/PriceForm.vue'
import PriceResult from '@/components/PriceResult.vue'
import WechatFab from '@/components/WechatFab.vue'

export default {
  components: { PriceForm, PriceResult, WechatFab },
  data() {
    return {
      // 只保留结果相关的数据
      resultList: [],
      needGoUpstairs: '0' // 保留这个用于显示提示
    }
  },

  methods: {
    // 表单数据变化时的处理
    onFormChange(formData) {
      console.log('表单数据变化:', formData)
      // 更新页面状态
      if (formData.type === 'form-data-change') {
        this.needGoUpstairs = formData.data.need_go_upstairs
      }
    },

    // 提交成功的处理
    onSubmitSuccess({ data }) {
      this.resultList = (data && data.data) ? data.data : []
      this.$refs.resultPopup.open()
    },

    // 提交失败的处理
    onSubmitError(error) {
      uni.showToast({ title: '请求失败，请稍后再试', icon: 'none' })
      console.error('页面层错误处理:', error)
    },

    // 计算计费重量
    calcChargeWeight(item) {
      if (item.charge_weight) return item.charge_weight
      const unitLine = item.fee_details?.find(f => f.name === 'unit_price')
      return unitLine ? unitLine.applied_value : '--'
    }
  }
}
</script>

<style scoped>
/* 样式已经在 PriceForm 和 PriceResult 组件中定义 */
</style>
