<template>
  <view class="container">
    <!-- 分类 -->
    <view class="form-item">
      <text class="label">分类</text>
      <picker :range="categories" range-key="main" @change="onCategoryChange">
        <view class="picker-box">
          <text class="main-category">{{ selectedCategoryMain || '请选择分类' }}</text>
        </view>
      </picker>
      <view v-if="selectedCategorySub" class="sub-category-desc">举例：{{ selectedCategorySub }}</view>
    </view>

    <!-- 重量 -->
    <view class="form-item">
      <text class="label">重量（kg）</text>
      <input type="number"
             v-model.number="weight"
             placeholder="请输入实重"
             class="input" />
      <view class="field-tip">称重所得的真实重量</view>
    </view>

    <!-- 体积 -->
    <view class="form-item">
      <text class="label">体积（m³）</text>
      <input type="number"
             v-model.number="volume"
             placeholder="请输入体积（如 0.02）"
             class="input" />
      <view class="field-tip">体积重公式：体积 × 143 ≈ kg</view>
    </view>

    <!-- 计费重量提示 -->
    <view v-if="chargeWeightTip" class="charge-weight-tip">{{ chargeWeightTip }}</view>

    <!-- 地址（分区/小区） -->
    <view class="form-item address-row">
      <text class="label">收貨地區</text>
      <view class="address-select-wrap">
        <picker :range="districts" range-key="district_cn" @change="onDistrictChange">
          <view class="select-box">{{ selectedDistrictName || '請選擇行政區' }}</view>
        </picker>
        <picker :range="subDistricts"
                range-key="sub_cn"
                @change="onSubDistrictChange"
                :disabled="!selectedDistrict">
          <view class="select-box">{{ selectedSubDistrictName || '請選擇分區／地段' }}</view>
        </picker>
      </view>
      <view v-if="isRemote !== null"
            class="remote-tip"
            :class="{ remote: isRemote }">
        <!-- {{ isRemote ? '该地区为偏远地区 (派送 +¥30)' : '该地区非偏远' }} -->
      </view>
    </view>

    <!-- 是否需要上楼 -->
    <view class="form-item">
      <text class="label">是否需要上楼</text>
      <radio-group class="radio-group"
                   :value="needGoUpstairs"
                   @change="onNeedGoUpstairsChange">
        <label class="radio-label">
          <radio value="1"
                 :checked="needGoUpstairs === '1'"
                 class="mini-radio" /> 是
        </label>
        <label class="radio-label">
          <radio value="0"
                 :checked="needGoUpstairs === '0'"
                 class="mini-radio" /> 否
        </label>
      </radio-group>
    </view>

    <!-- 仅当上楼显示 -->
    <view v-if="needGoUpstairs === '1'">
      <view class="form-item">
        <text class="label">是否电梯</text>
        <radio-group class="radio-group"
                     :value="hasElevator"
                     @change="e => hasElevator = e.detail.value">
          <label class="radio-label">
            <radio value="1"
                   :checked="hasElevator === '1'"
                   class="mini-radio" /> 有
          </label>
          <label class="radio-label">
            <radio value="0"
                   :checked="hasElevator === '0'"
                   class="mini-radio" /> 无
          </label>
        </radio-group>
      </view>
      <view class="form-item">
        <text class="label">是否搬阶梯</text>
        <radio-group class="radio-group"
                     :value="needStairs"
                     @change="e => needStairs = e.detail.value">
          <label class="radio-label">
            <radio value="1"
                   :checked="needStairs === '1'"
                   class="mini-radio" /> 是
          </label>
          <label class="radio-label">
            <radio value="0"
                   :checked="needStairs === '0'"
                   class="mini-radio" /> 否
          </label>
        </radio-group>
      </view>
    </view>

    <!-- 报价按钮 -->
    <button class="submit-button" @click="submit">我要报价</button>

    <!-- 报价结果弹窗 -->
    <uni-popup ref="resultPopup" type="dialog" class="result-popup">
      <view class="popup">
        <text class="popup-title">报价结果</text>

        <view v-for="(item, index) in resultList.slice(0, 2)"
              :key="index"
              class="quote-card">

          <!-- 顶部行：方案 + 总价 -->
          <view class="quote-head">
            <text class="plan">方案{{ index + 1 }}</text>
            <text class="price">{{ item.total_price }} 元</text>
          </view>

          <!-- 基本信息 -->
          <!-- <view class="quote-base">
            <text>渠道：{{ item.channel }}</text>
            <text>运输：{{ item.transport_method }}</text>
            <text>仓库：{{ item.warehouse }}</text>
          </view> -->

          <!-- 费用拆分 -->
          <view class="fee-details">
            <view v-for="fee in item.fee_details"
                  :key="fee.name"
                  class="fee-item">
              {{ fee.cn_name }}：{{ fee.amount }}
            </view>
          </view>

          <!-- 计费重量 -->
          <!-- <view class="charge-weight-row">
            <text>计量：{{ calcChargeWeight(item) }} kg</text>
          </view> -->

          <!-- 备注直接展示，低调样式 -->
          <view v-if="item.remark" class="quote-remark">
            备注：{{ item.remark }}
          </view>
        </view>
      </view>
    </uni-popup>


    <WechatFab />

  </view>
</template>

<script>
import { BASE_URL } from '@/common/config'
import hkDistricts from '@/common/hk_districts.json'
import uniPopup from '@dcloudio/uni-ui/lib/uni-popup/uni-popup.vue'
import WechatFab from '@/components/WechatFab.vue'

export default {
  components: { uniPopup, WechatFab },
  data () {
    return {
      /********* 表单 *********/
      categories: [],
      selectedCategory: null,
      selectedCategoryMain: '',
      selectedCategorySub: '',

      weight: null,
      volume: null,

      districts: hkDistricts,
      subDistricts: [],
      selectedDistrict: null,
      selectedDistrictName: '',
      selectedSubDistrict: null,
      selectedSubDistrictName: '',
      isRemote: null,

      needGoUpstairs: '0',
      hasElevator: '0',
      needStairs: '0',

      /********* 结果 *********/
      resultList: []
    }
  },

  computed: {
    /* 体积重 ≈ 体积 × 143 */
    volumetricWeight () {
      if (!this.volume && this.volume !== 0) return null
      const v = parseFloat(this.volume)
      return isNaN(v) ? null : +(v * 143).toFixed(2)
    },
    chargeWeight () {
      if (this.volumetricWeight === null || this.weight === null) return null
      const w = parseFloat(this.weight)
      if (isNaN(w)) return null
      return Math.max(w, this.volumetricWeight).toFixed(2)
    },
    chargeWeightTip () {
      if (this.chargeWeight === null) return ''
      return `计费重量：${this.chargeWeight} kg（体积重 ${this.volumetricWeight} kg / 实重 ${this.weight} kg，取其大）`
    }
  },

  watch: {
    /* 连续输入时保持 number 类型 */
    weight (val) { if (val === '') this.weight = null },
    volume (val) { if (val === '') this.volume = null }
  },

  onLoad () {
    this.loadCategories()
  },

  methods: {
    /**************** 数据加载 ****************/
    loadCategories () {
      uni.request({
        url: `${BASE_URL}/cal_price/classify/classify_list`,
        method: 'POST',
        data: {},
        success: (res) => {
          if (res.data.code === 200) {
            this.categories = res.data.data.map(item => ({
              id: item.category_id,
              main: item.main_category,
              sub: item.sub_examples
            }))
          }
        }
      })
    },

    /**************** 交互 ****************/
    onCategoryChange (e) {
      const index = e.detail.value
      const selected = this.categories[index]
      this.selectedCategory = selected.id
      this.selectedCategoryMain = selected.main
      this.selectedCategorySub = selected.sub
    },

    onDistrictChange (e) {
      const idx = e.detail.value
      const district = this.districts[idx]
      this.selectedDistrict = district.district_cn
      this.selectedDistrictName = district.district_cn
      this.subDistricts = district.sub_districts
      this.selectedSubDistrict = null
      this.selectedSubDistrictName = ''
      this.isRemote = null
    },

    onSubDistrictChange (e) {
      const idx = e.detail.value
      const sub = this.subDistricts[idx]
      this.selectedSubDistrict = sub.sub_cn
      this.selectedSubDistrictName = sub.sub_cn
      this.isRemote = sub.remote
    },

    onNeedGoUpstairsChange (e) {
      this.needGoUpstairs = (e.detail && e.detail.value)
        ? e.detail.value
        : e.target.value
      /* 如果选“否”，把后面两个置回默认 */
      if (this.needGoUpstairs === '0') {
        this.hasElevator = '0'
        this.needStairs = '0'
      }
    },

    /**************** 提交 ****************/
    submit () {
      if (!this.selectedCategory) {
        uni.showToast({ title: '请选择分类', icon: 'none' }); return
      }
      if (this.weight === null || this.volume === null) {
        uni.showToast({ title: '请填写重量和体积', icon: 'none' }); return
      }

      const extra = {
        type: '袋装',
        need_go_upstairs: this.needGoUpstairs,
        district: this.selectedDistrict,
        sub_district: this.selectedSubDistrict,
        is_remote: this.isRemote,
        has_elevator: this.hasElevator,
        need_stairs: this.needStairs
      }

      uni.request({
        url: `${BASE_URL}/cal_price/pricing_rule/min_pricing`,
        method: 'POST',
        data: {
          category_id: Number(this.selectedCategory),
          weight: Number(this.weight),
          volume: Number(this.volume),
          extra_fee_data: extra
        },
        success: (res) => {
          this.resultList = (res.data && res.data.data) ? res.data.data : []
          this.$refs.resultPopup.open()
        }
      })
    },

    /**************** 结果处理 ****************/
    calcChargeWeight (item) {
      /* 如果后台已算好，可直接取；此处 fallback 为 体积重 vs 实重 */
      if (item.charge_weight) return item.charge_weight
      /* demo：使用 fee_details 里 unit_price 的 applied_value 估算 */
      const unitLine = item.fee_details.find(f => f.name === 'unit_price')
      return unitLine ? unitLine.applied_value : '--'
    }
  }
}
</script>

<style scoped>
/* =============== 通用容器 =============== */
.container {
  padding: 20rpx;
  background-color: #f4f6f9;
  font-size: 28rpx;
  min-height: 100vh;
  overflow-y: auto;
  position: relative;
}

/* =============== 表单标签与行 =============== */
.label          { font-weight: bold; color: #333; margin-bottom: 12rpx; display: block; }
.form-item      { margin-bottom: 40rpx; }

.input, .picker-box {
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 12rpx;
  padding: 18rpx 20rpx;
  font-size: 28rpx;
  min-height: 64rpx;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
}
.picker-box .main-category { font-weight: bold; color: #333; }

.field-tip        { font-size: 24rpx; color: #999; margin-top: 6rpx; }
.charge-weight-tip{ font-size: 26rpx; color: #007aff; margin: -24rpx 0 24rpx 0; font-weight: 500; }

.sub-category-desc{
  color: #999; font-size: 24rpx; margin: 8rpx 0 0 6rpx;
}

.address-select-wrap{
  display: flex; flex-direction: row; gap: 18rpx; margin-top: 8rpx;
}
.select-box{
  flex: 1 1 0;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 12rpx;
  padding: 16rpx;
  min-height: 56rpx;
  font-size: 28rpx;
  display: flex; align-items: center;
  overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
}

.remote-tip         { margin-top: 6rpx; font-size: 24rpx; color: #999; }
.remote-tip.remote  { color: #ff9800; font-weight: bold; }

.radio-group{
  display: flex !important; flex-direction: row !important;
  gap: 40rpx; margin-top: 20rpx;
}
.radio-label{
  display: flex; align-items: center; font-size: 28rpx; color: #333; margin-right: 24rpx;
}
.mini-radio >>> .uni-radio-input,
.mini-radio >>> .uni-radio-input-checked,
.mini-radio /deep/ .uni-radio-input,
.mini-radio /deep/ .uni-radio-input-checked{
  transform: scale(0.75); margin-right: 10rpx;
}

.submit-button{
  background: #007aff; color: #fff; padding: 2rpx;
  border-radius: 14rpx; font-size: 32rpx; text-align: center;
  margin-top: 20rpx; width: 100%; box-sizing: border-box;
}

.popup{
  padding: 5px; background: #fff; border-radius: 20rpx;
  max-height: 80vh; overflow-y: auto; box-sizing: border-box; margin: 5px;
}
.popup-title{
  font-size: 32rpx; font-weight: bold; text-align: center;
  margin-bottom: 20rpx; color: #222;
}

.quote-card{
  border: 1px solid #e5e5e5; border-radius: 16rpx;
  padding: 24rpx; margin-bottom: 24rpx;
}
.quote-head{
  display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12rpx;
}
.quote-head .plan  { font-size: 30rpx; font-weight: 600; color: #333; }
.quote-head .price { font-size: 32rpx; font-weight: 700; color: #e64340; }
.quote-base{
  display: flex; flex-wrap: wrap; gap: 24rpx;
  font-size: 26rpx; color: #555; margin-bottom: 12rpx;
}
.fee-details{
  display: flex; flex-wrap: wrap; gap: 16rpx;
  font-size: 26rpx; color: #888; margin-bottom: 10rpx;
}
.fee-item           { white-space: nowrap; }
.charge-weight-row  { font-size: 26rpx; color: #666; margin-bottom: 10rpx; }

/* 备注样式：低调浅灰 */
.quote-remark {
  margin-top: 6rpx;
  color: #888;
  font-size: 22rpx;
  background: #f6f6f6;
  border-radius: 8rpx;
  padding: 10rpx 14rpx;
  line-height: 1.5;
  word-break: break-all;
}

html, body { overflow: auto !important; }
.uni-popup    { position: relative; }
</style>
