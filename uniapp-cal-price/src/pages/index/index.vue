<template>
  <view class="price-container">
    <!-- 使用公共价格表单组件 -->
    <PriceForm 
      submit-text="我要报价"
      :use-request-util="false"
      @form-change="onFormChange"
      @submit-success="onSubmitSuccess"
      @submit-error="onSubmitError"
    />

    <!-- 报价结果弹窗 -->
    <uni-popup ref="resultPopup" type="dialog" class="result-popup"
      custom-style="width:80%;max-width:700rpx;border-radius:20rpx;">
      <view class="price-result-popup">
        <text class="price-result-popup-title">报价结果</text>

        <!-- ✅ 如果无报价 -->
        <view v-if="resultList.length === 0" class="price-result-quote-empty">
          当前报价方案未匹配，找客服领解决方案
        </view>

        <!-- ✅ 如果有报价 -->
        <view v-else>
          <view v-for="(item, index) in resultList.slice(0, 2)" :key="index" class="price-result-quote-card">
            <view class="price-result-quote-head">
              <view>
                <text class="price-result-quote-plan">方案{{ index + 1 }}</text>
                <text class="price-result-channel-label">{{ item.channel }}</text>
                <text class="price-result-channel-label">{{ item.transport_method }}</text>
              </view>
              <text class="price-result-quote-price">{{ item.total_price }} 元</text>
            </view>

            <view class="price-result-fee-details">
              <view v-for="fee in item.fee_details" :key="fee.name" class="price-result-fee-item">
                {{ fee.cn_name }}：{{ fee.amount }}
              </view>
            </view>

            <view v-if="item.remark" class="price-result-quote-remark">
              备注：{{ item.remark }}
            </view>
          </view>
        </view>

        <!-- ✅ 添加"上楼费咨询客服"提示 -->
        <view v-if="needGoUpstairs === '1'" class="price-result-extra-fee-tip">
          上楼费请咨询客服
        </view>

        <!-- ✅ 添加按钮 -->
        <view class="price-result-quote-bottom">
          <button class="price-result-wechat-btn" @click="openWechatPopup">
            找客服领取新客优惠 🎁
          </button>
        </view>
      </view>
    </uni-popup>

    <WechatFab ref="fab" />
  </view>
</template>

<script>
import PriceForm from '@/components/PriceForm.vue'
import uniPopup from '@dcloudio/uni-ui/lib/uni-popup/uni-popup.vue'
import WechatFab from '@/components/WechatFab.vue'

export default {
  components: { PriceForm, uniPopup, WechatFab },
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
    },

    // 打开企业微信弹窗
    openWechatPopup() {
      console.log('尝试打开企业微信弹窗', this.$refs.fab)
      this.$refs.fab?.showPopup?.()
    }
  }
}
</script>

<style scoped>
/* 样式已经在 PriceForm 组件中定义 */

/* 弹窗样式 - 移除 :deep() 选择器 */
.price-result-popup {
  background: #fff;
  padding: 60rpx 40rpx 40rpx;
  border-radius: 20rpx;
  position: relative;
  max-height: 80vh;
  overflow-y: auto;
}

.price-result-popup-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 30rpx;
  text-align: center;
  display: block;
}

.price-result-quote-empty {
  text-align: center;
  color: #999;
  font-size: 28rpx;
  padding: 40rpx;
  display: block;
}

.price-result-quote-card {
  background: #f8f9fa;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  border: 2rpx solid #e9ecef;
}

.price-result-quote-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20rpx;
}

.price-result-quote-plan {
  font-weight: bold;
  color: #333;
  font-size: 30rpx;
  margin-right: 20rpx;
}

.price-result-channel-label {
  background: #e3f2fd;
  color: #1976d2;
  padding: 4rpx 16rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
  margin-right: 10rpx;
}

.price-result-quote-price {
  color: #ff5722;
  font-size: 36rpx;
  font-weight: bold;
}

.price-result-fee-details {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  margin-bottom: 20rpx;
}

.price-result-fee-item {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
}

.price-result-quote-remark {
  background: #fff3cd;
  border-left: 4rpx solid #ffc107;
  padding: 16rpx;
  margin-top: 20rpx;
  font-size: 26rpx;
  color: #856404;
}

.price-result-extra-fee-tip {
  background: #e8f5e8;
  border: 2rpx solid #4caf50;
  color: #2e7d32;
  padding: 20rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
  margin-top: 20rpx;
  margin-bottom: 20rpx;
  text-align: center;
}

.price-result-quote-bottom {
  margin-top: 40rpx;
}

.price-result-wechat-btn {
  width: 100%;
  background: #25c246;
  color: #fff;
  border: none;
  border-radius: 50rpx;
  font-size: 32rpx;
  font-weight: 500;
  padding: 28rpx;
  margin-top: 20rpx;
  transition: all 0.3s ease;
}

.price-result-wechat-btn:active {
  transform: scale(0.98);
  background: #1ea038;
}
</style>
