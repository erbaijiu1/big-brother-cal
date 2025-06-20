<template>
  <view class="container">
    <view class="form-item">
      <text class="label">分类</text>
      <picker :range="categories" range-key="main" @change="onCategoryChange">
        <view class="picker-box">
          <text class="main-category">{{ selectedCategoryMain || '请选择分类' }}</text>
        </view>
      </picker>
      <!-- 子类说明在框外、浅灰色显示 -->
      <view v-if="selectedCategorySub" class="sub-category-desc">{{ selectedCategorySub }}</view>
    </view>

    <view class="form-item">
      <text class="label">重量（kg）</text>
      <input type="number" v-model="weight" placeholder="请输入重量" class="input" />
    </view>

    <view class="form-item">
      <text class="label">体积（m³）</text>
      <input type="number" v-model="volume" placeholder="请输入体积" class="input" />
    </view>

    <view class="form-item address-row">
      <text class="label">地址</text>
      <view class="address-select-wrap">
        <!-- 大区选择 -->
        <picker :range="districts" range-key="district_cn" @change="onDistrictChange">
          <view class="select-box">
            {{ selectedDistrictName || '请选择大区' }}
          </view>
        </picker>
        <!-- 小区选择 -->
        <picker :range="subDistricts" range-key="sub_cn" @change="onSubDistrictChange" :disabled="!selectedDistrict">
          <view class="select-box">
            {{ selectedSubDistrictName || '请选择小区' }}
          </view>
        </picker>
      </view>
      <view v-if="isRemote !== null" class="remote-tip" :class="{ remote: isRemote }">
        {{ isRemote ? '该地区为偏远地区' : '该地区非偏远' }}
      </view>
    </view>

    <!-- <view class="form-item">
      <text class="label">地址</text>
      <input v-model="addressTo" placeholder="目的地" class="input" />
    </view> -->

    <!-- <view class="form-item">
      <text class="label">货物类型</text>
      <radio-group class="radio-group" v-model="packageType">
        <label class="radio-label"><radio value="袋装" class="mini-radio" /> 袋装</label>
        <label class="radio-label"><radio value="整托" class="mini-radio" /> 整托</label>
      </radio-group>
    </view> -->

    <view class="form-item">
      <text class="label">是否电梯</text>
      <radio-group class="radio-group" v-model="hasElevator">
        <label class="radio-label">
          <radio value="是" class="mini-radio" /> 有
        </label>
        <label class="radio-label">
          <radio value="否" class="mini-radio" /> 无
        </label>
      </radio-group>
    </view>

    <view class="form-item">
      <text class="label">是否搬楼</text>
      <radio-group class="radio-group" v-model="needStairs">
        <label class="radio-label">
          <radio value="是" class="mini-radio" /> 是
        </label>
        <label class="radio-label">
          <radio value="否" class="mini-radio" /> 否
        </label>
      </radio-group>
    </view>

    <button class="submit-button" @click="submit">我要报价</button>

    <uni-popup ref="resultPopup" type="dialog">
      <view class="popup">
        <text class="popup-title">报价结果</text>
        <view v-for="(item, index) in resultList" :key="index" class="quote-item">
          <text>
            方案{{ index + 1 }}：<text class="price">{{ item.total_price }}</text> 元，
            渠道：{{ item.channel }}，
            运输：{{ item.transport_method }}，
            仓库：{{ item.warehouse }}
          </text>
        </view>
        <button class="popup-button" @click="contactCustomer">联系客服领优惠</button>
      </view>
    </uni-popup>
  </view>
</template>

<script>
import { BASE_URL } from '@/common/config'
import hkDistricts from '@/common/hk_districts.json'

export default {
  data() {
    return {
      categories: [],
      selectedCategory: null,
      selectedCategoryMain: '',
      selectedCategorySub: '',
      weight: '',
      volume: '',
      addressFrom: '',
      addressTo: '',
      packageType: '袋装',
      hasElevator: '是',
      needStairs: '否',
      resultList: []
      , districts: hkDistricts,        // 大区json
      subDistricts: [],     // 当前选中的大区下的小区列表
      selectedDistrict: null,
      selectedDistrictName: '',
      selectedSubDistrict: null,
      selectedSubDistrictName: '',
      isRemote: null,       // 是否偏远
    };
  },
  onLoad() {
    this.loadCategories();
  },
  methods: {
    loadCategories() {
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
            }));
          }
        }
      });
    },
    onCategoryChange(e) {
      const index = e.detail.value;
      const selected = this.categories[index];
      this.selectedCategory = selected.id;
      this.selectedCategoryMain = selected.main;
      this.selectedCategorySub = selected.sub;
    },
    submit() {
      // 校验
      if (!this.selectedCategory) {
        uni.showToast({ title: '请选择分类', icon: 'none' });
        return;
      }
      if (!this.weight || !this.volume) {
        uni.showToast({ title: '请填写重量和体积', icon: 'none' });
        return;
      }
      uni.request({
        url: `${BASE_URL}/cal_price/pricing_rule/min_pricing`,
        method: 'POST',
        data: {
          category_id: Number(this.selectedCategory), // 保证数字类型
          weight: Number(this.weight),
          volume: Number(this.volume),
          extra_fee_data: {
            to_address: this.addressTo,
            type: this.packageType,
            has_elevator: this.hasElevator,
            need_stairs: this.needStairs,
            district: this.selectedDistrict,
            sub_district: this.selectedSubDistrict,
            is_remote: this.isRemote,
          }
        },
        success: (res) => {
          this.resultList = (res.data && res.data.data) ? res.data.data : [];
          this.$refs.resultPopup.open();
        }
      });
    },
    contactCustomer() {
      uni.navigateTo({
        url: '/pages/contact/index'
      });
    }
    , onDistrictChange(e) {
      const idx = e.detail.value;
      const district = this.districts[idx];
      this.selectedDistrict = district.district_cn;
      this.selectedDistrictName = district.district_cn;
      this.subDistricts = district.sub_districts;
      this.selectedSubDistrict = null;
      this.selectedSubDistrictName = '';
      this.isRemote = null;
    },
    onSubDistrictChange(e) {
      const idx = e.detail.value;
      const sub = this.subDistricts[idx];
      this.selectedSubDistrict = sub.sub_cn;
      this.selectedSubDistrictName = sub.sub_cn;
      this.isRemote = sub.remote;
    },
  }
};
</script>

<style scoped>
.container {
  padding: 40rpx;
  background-color: #f4f6f9;
  font-size: 28rpx;
}
.label {
  font-weight: bold;
  margin-bottom: 12rpx;
  display: block;
  color: #333;
}
.form-item {
  margin-bottom: 40rpx;
}
.input, .picker-box {
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 12rpx;
  padding: 18rpx 20rpx;
  font-size: 28rpx;
  width: 100%;
  min-height: 64rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
}
.picker-box .main-category {
  font-weight: bold;
  color: #333;
}
.sub-category-desc {
  color: #999;
  font-size: 24rpx;
  margin-top: 8rpx;
  margin-left: 6rpx;
}
.radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 40rpx;
  margin-top: 20rpx;
}
.radio-label {
  display: flex;
  align-items: center;
  font-size: 28rpx;
  color: #333;
}
.mini-radio >>> .uni-radio-input,
.mini-radio >>> .uni-radio-input-checked {
  transform: scale(0.75);
  margin-right: 10rpx;
}
/* uni-app H5 兼容 */
.mini-radio /deep/ .uni-radio-input,
.mini-radio /deep/ .uni-radio-input-checked {
  transform: scale(0.75);
  margin-right: 10rpx;
}
.submit-button {
  background-color: #007aff;
  color: #fff;
  padding: 28rpx;
  border-radius: 14rpx;
  font-size: 32rpx;
  text-align: center;
  margin-top: 20rpx;
  width: 100%;
  box-sizing: border-box;
}
.popup {
  padding: 40rpx;
  background: #fff;
  border-radius: 20rpx;
}
.popup-title {
  font-size: 36rpx;
  font-weight: bold;
  margin-bottom: 30rpx;
}
.quote-item {
  padding: 20rpx 0;
  border-bottom: 1px solid #eee;
  font-size: 30rpx;
}
.price {
  font-weight: bold;
  color: #e64340;
}
.popup-button {
  margin-top: 40rpx;
  background-color: #ff9800;
  color: white;
  padding: 20rpx;
  border-radius: 10rpx;
  font-size: 30rpx;
  width: 100%;
  box-sizing: border-box;
}

.address-row .address-select-wrap {
  display: flex;
  flex-direction: row;
  gap: 18rpx;
  margin-top: 8rpx;
}
.address-row .select-box {
  flex: 1 1 0;
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 12rpx;
  padding: 16rpx 16rpx;
  min-height: 56rpx;
  font-size: 28rpx;
  text-align: left;
  display: flex;
  align-items: center;
}
.remote-tip {
  margin-top: 6rpx;
  color: #999;
  font-size: 24rpx;
}
.remote-tip.remote {
  color: #ff9800;
  font-weight: bold;
}

</style>
