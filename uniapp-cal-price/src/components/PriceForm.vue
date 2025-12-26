<template>
  <view class="price-form">
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

    <!-- 重量和体积输入 -->
    <view class="form-row">
      <view class="form-item flex-1">
        <text class="label">重量（kg）</text>
        <input type="digit" v-model.number="weight" placeholder="请输入实重" class="input" />
        <view class="field-tip">称重所得的真实重量</view>
      </view>

      <view class="form-item flex-1">
        <text class="label">体积（m³）</text>
        <input type="digit" v-model.number="volume" placeholder="体积选填：如0.02" class="input" />
        <view class="field-tip">体积重公式：体积 × 200 ≈ kg</view>
      </view>
    </view>

    <!-- 计费重量提示 -->
    <view v-if="chargeWeightTip" class="charge-weight-tip">{{ chargeWeightTip }}</view>

    <!-- 件数输入 -->
    <view class="form-item">
      <text class="label">件数</text>
      <input type="digit" v-model.number="pieces" placeholder="默认1件" class="input pieces-input" />
      <view class="field-tip">多件商品的总件数（选填）</view>
    </view>

    <!-- 地址（分区/小区） -->
    <view class="form-item address-row">
      <text class="label">收货地区</text>
      <view class="address-select-wrap">
        <picker :range="districts" range-key="district_cn" @change="onDistrictChange">
          <view class="select-box">{{ selectedDistrictName || '请选择行政区' }}</view>
        </picker>
        <picker :range="subDistricts" range-key="sub_cn" @change="onSubDistrictChange" :disabled="!selectedDistrict">
          <view class="select-box">{{ selectedSubDistrictName || '请选择分区/地段' }}</view>
        </picker>
      </view>
      <view v-if="isRemote !== null" class="remote-tip" :class="{ remote: isRemote }"></view>
    </view>

    <!-- 是否需要上楼 -->
    <view class="form-item">
      <text class="label">是否需要上楼</text>
      <radio-group class="radio-group" :value="needGoUpstairs" @change="onNeedGoUpstairsChange">
        <label class="radio-label">
          <radio value="1" :checked="needGoUpstairs === '1'" class="mini-radio" /> 是
        </label>
        <label class="radio-label">
          <radio value="0" :checked="needGoUpstairs === '0'" class="mini-radio" /> 否
        </label>
      </radio-group>
    </view>

    <!-- 仅当上楼显示 -->
    <view v-if="needGoUpstairs === '1'">
      <view class="form-item">
        <text class="label">是否电梯</text>
        <radio-group class="radio-group" :value="hasElevator" @change="e => hasElevator = e.detail.value">
          <label class="radio-label">
            <radio value="1" :checked="hasElevator === '1'" class="mini-radio" /> 有
          </label>
          <label class="radio-label">
            <radio value="0" :checked="hasElevator === '0'" class="mini-radio" /> 无
          </label>
        </radio-group>
      </view>
      <view class="form-item">
        <text class="label">是否搬阶梯</text>
        <radio-group class="radio-group" :value="needStairs" @change="e => needStairs = e.detail.value">
          <label class="radio-label">
            <radio value="1" :checked="needStairs === '1'" class="mini-radio" /> 是
          </label>
          <label class="radio-label">
            <radio value="0" :checked="needStairs === '0'" class="mini-radio" /> 否
          </label>
        </radio-group>
      </view>
    </view>

    <!-- 提交按钮 -->
    <button class="submit-button" @click="handleSubmit">{{ submitText }}</button>
  </view>
</template>

<script lang="js">
import { calculateVolumetricWeight, calculateChargeWeight } from '@/common/utils/calculator'
import hkDistricts from '@/common/hk_districts.json'
import { request } from '@/common/utils/request'
import { BASE_URL } from '@/common/config'

export default {
  props: {
    submitText: {
      type: String,
      default: '我要报价'
    },
    apiEndpoint: {
      type: String,
      default: '/cal_price/pricing_rule/min_pricing'
    },
    useRequestUtil: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      /********* 表单 *********/
      categories: [],
      selectedCategory: null,
      selectedCategoryMain: '',
      selectedCategorySub: '',

      weight: null,
      volume: null,
      pieces: 1, // 默认1件

      districts: hkDistricts,
      subDistricts: [],
      selectedDistrict: null,
      selectedDistrictName: '',
      selectedSubDistrict: null,
      selectedSubDistrictName: '',
      isRemote: null,

      needGoUpstairs: '0',
      hasElevator: '0',
      needStairs: '0'
    }
  },

  computed: {
    volumetricWeight() {
      if (!this.volume && this.volume !== 0) return null
      return calculateVolumetricWeight(this.volume)
    },
    chargeWeight() {
      if (this.volumetricWeight === null || this.weight === null) return null
      return calculateChargeWeight(this.weight, this.volumetricWeight)
    },
    chargeWeightTip() {
      if (this.chargeWeight === null) return ''
      return `计费重量：${this.chargeWeight} kg（体积重 ${this.volumetricWeight} kg / 实重 ${this.weight} kg，取其大）`
    }
  },

  watch: {
    weight(val) { if (val === '') this.weight = null },
    volume(val) { if (val === '') this.volume = null },
    pieces(val) { if (val === '' || val === null || val < 1) this.pieces = 1 }
  },

  mounted() {
    this.loadCategories()
    
    // 小程序环境检测
    // #ifdef MP-WEIXIN
    console.log('微信小程序环境')
    // #endif
    
    // #ifdef MP-ALIPAY  
    console.log('支付宝小程序环境')
    // #endif
    
    // #ifdef H5
    console.log('H5环境')
    // #endif
  },

  methods: {
    // 加载分类
    async loadCategories() {
      const requestFn = this.useRequestUtil ? request : uni.request
      const url = this.useRequestUtil ? '/cal_price/classify/classify_list' : `${BASE_URL}/cal_price/classify/classify_list`

      try {
        const res = await requestFn({
          url,
          method: 'POST',
          data: {}
        })
        
        const data = this.useRequestUtil ? res : res.data
        if (data.code === 200) {
          this.categories = data.data.map(item => ({
            id: item.category_id,
            main: item.main_category,
            sub: item.sub_examples
          }))
        }
      } catch (e) {
        console.error('分类加载失败:', e)
      }
    },

    // 分类变更
    onCategoryChange(e) {
      const index = e.detail.value
      const selected = this.categories[index]
      this.selectedCategory = selected.id
      this.selectedCategoryMain = selected.main
      this.selectedCategorySub = selected.sub
      this.emitFormChange()
    },



    // 地址变更
    onDistrictChange(e) {
      const idx = e.detail.value
      const district = this.districts[idx]
      this.selectedDistrict = district.district_cn
      this.selectedDistrictName = district.district_cn
      this.subDistricts = district.sub_districts
      this.selectedSubDistrict = null
      this.selectedSubDistrictName = ''
      this.isRemote = null
      this.emitFormChange()
    },

    onSubDistrictChange(e) {
      const idx = e.detail.value
      const sub = this.subDistricts[idx]
      this.selectedSubDistrict = sub.sub_cn
      this.selectedSubDistrictName = sub.sub_cn
      this.isRemote = sub.remote
      this.emitFormChange()
    },

    // 上楼相关变更
    onNeedGoUpstairsChange(e) {
      this.needGoUpstairs = (e.detail && e.detail.value) ? e.detail.value : e.target.value
      if (this.needGoUpstairs === '0') {
        this.hasElevator = '0'
        this.needStairs = '0'
      }
      this.emitFormChange()
    },

    // 提交
    async handleSubmit() {
      // 1. 基础验证
      if (!this.selectedCategory) {
        uni.showToast({ title: '请选择分类', icon: 'none' })
        return
      }

      if (this.weight === null && this.volume === null) {
        uni.showToast({ title: '请填写重量或体积', icon: 'none' })
        return
      }

      if (!this.selectedDistrict) {
        uni.showToast({ title: '请选择收货地区', icon: 'none' })
        return
      }

      // 2. 构建请求数据
      const requestData = this.buildRequestData()

      // 3. 发送请求
      try {
        const requestFn = this.useRequestUtil ? request : uni.request
        const url = this.useRequestUtil ? this.apiEndpoint : `${BASE_URL}${this.apiEndpoint}`
        
        const res = await requestFn({
          url,
          method: 'POST',
          data: requestData
        })

        const data = this.useRequestUtil ? res : res.data
        this.$emit('submit-success', { data, requestData })
        this.$emit('form-change', { type: 'submit', data: requestData })

      } catch (error) {
        console.error('请求失败:', error)
        
        // 小程序网络错误处理
        const errorMsg = (error && error.errMsg) ? error.errMsg : '网络请求失败，请重试'
        
        uni.showToast({
          title: errorMsg,
          icon: 'none',
          duration: 2000
        })
        
        this.$emit('submit-error', error)
      }
    },

    // 构建请求数据
    buildRequestData() {
      const extra = {
        type: '袋装',
        need_go_upstairs: this.needGoUpstairs,
        district: this.selectedDistrict,
        sub_district: this.selectedSubDistrict,
        is_remote: this.isRemote,
        has_elevator: this.hasElevator,
        need_stairs: this.needStairs
      }

      let baseData = {
        category_id: Number(this.selectedCategory),
        extra_fee_data: extra
      }

      // 重量：必填，没有填写传0
      if (this.weight !== null) {
        baseData.weight = Math.max(0, Number(this.weight))
      } else {
        baseData.weight = 0
      }

      // 体积：必填，没有填写传0
      if (this.volume !== null) {
        baseData.volume = Math.max(0, Number(this.volume))
      } else {
        baseData.volume = 0
      }

      // 件数：可选，大于1件时才传递
      if (this.pieces >= 1) {
        baseData.quantity = Math.max(1, Number(this.pieces))
      }

      return baseData
    },

    // 发出表单变更事件
    emitFormChange() {
      this.$emit('form-change', {
        type: 'form-data-change',
        data: {
          category_id: this.selectedCategory,
          weight: this.weight,
          volume: this.volume,
          pieces: this.pieces,
          district: this.selectedDistrict,
          sub_district: this.selectedSubDistrict,
          need_go_upstairs: this.needGoUpstairs,
          has_elevator: this.hasElevator,
          need_stairs: this.needStairs
        }
      })
    }
  }
}
</script>

<style>
/* ================== 价格计算器样式 ================== */

/* 表单样式 */
.price-form {
  padding: 20rpx;
  background-color: #f4f6f9;
  font-size: 28rpx;
}

.label          { font-weight: bold; color: #333; margin-bottom: 12rpx; display: block; }
.form-item      { margin-bottom: 40rpx; }

/* 表单行布局 */
.form-row {
  display: flex;
  gap: 20rpx;
  /* margin-bottom: 40rpx; */
}

.flex-1 {
  flex: 1;
  margin-bottom: 10rpx;
}

/* 件数输入框特殊样式 */
.pieces-input {
  max-width: 200rpx;
}

/* 小程序特定样式 */
/* #ifdef MP-WEIXIN */
.input {
  /* 微信小程序中数字键盘优化 */
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif;
}
/* #endif */

/* #ifdef MP-ALIPAY */
.input {
  /* 支付宝小程序兼容 */
  box-sizing: border-box;
}
/* #endif */

.input, .picker-box {
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 12rpx;
  padding: 0rpx 20rpx;
  font-size: 28rpx;
  min-height: 64rpx;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  line-height: 64rpx;
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

/* 通用容器样式 */
.price-container {
  padding: 20rpx;
  background-color: #f4f6f9;
  font-size: 28rpx;
  min-height: 100vh;
  overflow-y: auto;
  position: relative;
}
</style>