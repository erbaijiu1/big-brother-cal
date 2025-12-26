<template>
  <uni-popup ref="resultPopup" type="dialog" class="result-popup"
    custom-style="width:80%;max-width:700rpx;border-radius:20rpx;">
    <view class="price-popup">
      <text class="price-popup-title">报价结果</text>

      <view v-if="localResultList.length === 0" class="price-quote-empty">
        当前报价方案未匹配，找客服领解决方案
      </view>

      <view v-else>
        <view v-for="(item, index) in localResultList" :key="index" class="price-quote-card">
          <view class="price-quote-head">
            <view>
              <text class="price-quote-plan">方案{{ index + 1 }}</text>
              <text class="price-channel-label">{{ item.channel }}</text>
              <text class="price-channel-label">{{ item.transport_method }}</text>
            </view>
            <text class="price-quote-price">{{ item.total_price }} 元</text>
          </view>

          <view class="price-fee-details">
            <view v-for="fee in item.fee_details" :key="fee.name" class="price-fee-item">
              {{ fee.cn_name }}：{{ fee.amount }}
            </view>
          </view>

          <view v-if="item.remark" class="price-quote-remark">
            备注：{{ item.remark }}
          </view>
        </view>
      </view>

      <view v-if="needGoUpstairs === '1'" class="price-extra-fee-tip">
        上楼费请咨询行政
      </view>
    </view>
  </uni-popup>
</template>

<script>
import uniPopup from '@dcloudio/uni-ui/lib/uni-popup/uni-popup.vue'

export default {
  name: 'PriceResult',
  components: { uniPopup },
  props: {
    resultList: {
      type: Array,
      default: () => []
    },
    needGoUpstairs: {
      type: String,
      default: '0'
    }
  },
  data() {
    return {
      localResultList: []
    }
  },
  watch: {
    resultList: {
      handler(val) {
        this.localResultList = val
      },
      immediate: true
    }
  },
  methods: {
    open() {
      this.$refs.resultPopup.open()
    },
    close() {
      this.$refs.resultPopup.close()
    }
  }
}
</script>

<style scoped>
/* 弹窗样式 */
.price-popup {
  padding: 5px; 
  background: #fff; 
  border-radius: 20rpx;
  max-height: 80vh; 
  overflow-y: auto; 
  box-sizing: border-box; 
  margin: 5px;
}

.price-popup-title {
  font-size: 32rpx; 
  font-weight: bold; 
  text-align: center;
  margin-bottom: 20rpx; 
  color: #222;
}

/* 报价卡片 */
.price-quote-card {
  border: 1px solid #e5e5e5; 
  border-radius: 16rpx;
  padding: 24rpx; 
  margin-bottom: 24rpx;
}

.price-quote-head {
  display: flex; 
  justify-content: space-between; 
  align-items: baseline; 
  margin-bottom: 12rpx;
}

.price-quote-plan { 
  font-size: 30rpx; 
  font-weight: 600; 
  color: #333; 
}

.price-quote-price { 
  font-size: 32rpx; 
  font-weight: 700; 
  color: #e64340; 
}

.price-channel-label {
  font-size: 26rpx; 
  color: #888; 
  margin-left: 10rpx; 
}

/* 费用详情 */
.price-fee-details {
  display: flex; 
  flex-wrap: wrap; 
  gap: 16rpx;
  font-size: 26rpx; 
  color: #888; 
  margin-bottom: 10rpx;
}

.price-fee-item { 
  white-space: nowrap; 
}

/* 备注 */
.price-quote-remark {
  margin-top: 6rpx;
  color: #888;
  font-size: 22rpx;
  background: #f6f6f6;
  border-radius: 8rpx;
  padding: 10rpx 14rpx;
  line-height: 1.5;
  word-break: break-all;
}

/* 空状态 */
.price-quote-empty {
  text-align: center;
  font-size: 26rpx;
  color: #888;
  padding: 40rpx 20rpx;
}

/* 上楼费提示 */
.price-extra-fee-tip {
  margin-top: 20rpx;
  padding: 16rpx;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8rpx;
  font-size: 26rpx;
  color: #856404;
  text-align: center;
}

.uni-popup { 
  position: relative; 
}
</style>
