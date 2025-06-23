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
      <view v-if="selectedCategorySub" class="sub-category-desc">{{ selectedCategorySub }}</view>
    </view>

    <!-- 重量 -->
    <view class="form-item">
      <text class="label">重量（kg）</text>
      <input type="number" v-model="weight" placeholder="请输入重量" class="input" />
    </view>
    <!-- 体积 -->
    <view class="form-item">
      <text class="label">体积（m³）</text>
      <input type="number" v-model="volume" placeholder="请输入体积" class="input" />
    </view>
    <!-- 地址（分区/小区） -->
    <view class="form-item address-row">
      <text class="label">地址</text>
      <view class="address-select-wrap">
        <picker :range="districts" range-key="district_cn" @change="onDistrictChange">
          <view class="select-box">{{ selectedDistrictName || '请选择大区' }}</view>
        </picker>
        <picker :range="subDistricts" range-key="sub_cn" @change="onSubDistrictChange" :disabled="!selectedDistrict">
          <view class="select-box">{{ selectedSubDistrictName || '请选择小区' }}</view>
        </picker>
      </view>
      <view v-if="isRemote !== null" class="remote-tip" :class="{ remote: isRemote }">
        {{ isRemote ? '该地区为偏远地区' : '该地区非偏远' }}
      </view>
    </view>

    <!-- 是否需要上楼 -->
    <view class="form-item">
      <text class="label">是否需要上楼</text>
      <radio-group class="radio-group" :value="needGoUpstairs" @change="onNeedGoUpstairsChange">
        <label class="radio-label">
          <radio :value="'1'" :checked="needGoUpstairs === '1'" class="mini-radio" /> 是
        </label>
        <label class="radio-label">
          <radio :value="'0'" :checked="needGoUpstairs === '0'" class="mini-radio" /> 否
        </label>
      </radio-group>
    </view>

    <!-- 仅当上楼显示 -->
    <view v-if="needGoUpstairs === '1'">
      <view class="form-item">
        <text class="label">是否电梯</text>
        <radio-group class="radio-group" :value="hasElevator" @change="e => hasElevator = e.detail.value">
          <label class="radio-label">
            <radio :value="'1'" :checked="hasElevator === '1'" class="mini-radio" /> 有
          </label>
          <label class="radio-label">
            <radio :value="'0'" :checked="hasElevator === '0'" class="mini-radio" /> 无
          </label>
        </radio-group>
      </view>
      <view class="form-item">
        <text class="label">是否搬阶梯</text>
        <radio-group class="radio-group" :value="needStairs" @change="e => needStairs = e.detail.value">
          <label class="radio-label">
            <radio :value="'1'" :checked="needStairs === '1'" class="mini-radio" /> 是
          </label>
          <label class="radio-label">
            <radio :value="'0'" :checked="needStairs === '0'" class="mini-radio" /> 否
          </label>
        </radio-group>
      </view>
    </view>

    <!-- 报价按钮 -->
    <button class="submit-button" @click="submit">我要报价</button>

    <!-- 报价结果弹窗 -->
    <uni-popup ref="resultPopup" type="dialog">
      <view class="popup">
        <text class="popup-title">报价结果</text>
        <view v-for="(item, index) in resultList" :key="index" class="quote-item">
          <view class="quote-row">
            <text>
              方案{{ index + 1 }}：
              <text class="price">{{ item.total_price }}</text> 元，
              渠道：{{ item.channel }}，
              运输：{{ item.transport_method }}，
              仓库：{{ item.warehouse }}
            </text>
            <button v-if="item.remark" class="remark-btn" @click="showRemark(item.remark)">备注</button>
          </view>
        </view>
        <button class="popup-button" @click="contactCustomer">联系客服领优惠</button>
      </view>
    </uni-popup>

    <!-- ✅ 弹窗结构建议 -->
    <uni-popup ref="remarkPopup" type="bottom">
      <view class="big-remark-popup">
        <view class="close-icon" @click="closeRemark">&#x2715;</view>
        <text class="popup-title">规则备注</text>
        <view class="remark-scroll-view">
          <view class="remark-content">{{ currentRemark }}</view>
        </view>
      </view>
    </uni-popup>

  </view>
</template>

<script>
import { BASE_URL } from '@/common/config'
import hkDistricts from '@/common/hk_districts.json'
import uniPopup from '@dcloudio/uni-ui/lib/uni-popup/uni-popup.vue'


export default {
  components: { uniPopup },
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
      hasElevator: '0',
      needStairs: '0',
      resultList: [],
      districts: hkDistricts,
      subDistricts: [],
      selectedDistrict: null,
      selectedDistrictName: '',
      selectedSubDistrict: null,
      selectedSubDistrictName: '',
      isRemote: null,
      needGoUpstairs: '0',
      currentRemark: ''
    }
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
      if (!this.selectedCategory) {
        uni.showToast({ title: '请选择分类', icon: 'none' }); return;
      }
      if (!this.weight || !this.volume) {
        uni.showToast({ title: '请填写重量和体积', icon: 'none' }); return;
      }
      let extra = {
        to_address: this.addressTo,
        type: this.packageType,
        need_go_upstairs: this.needGoUpstairs,
        district: this.selectedDistrict,
        sub_district: this.selectedSubDistrict,
        is_remote: this.isRemote,
        has_elevator: this.hasElevator,
        need_stairs: this.needStairs
      };
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
          console.log('popup ref is:', this.$refs.resultPopup)

          this.resultList = (res.data && res.data.data) ? res.data.data : [];
          this.$refs.resultPopup.open();
        }
      });
    },
    contactCustomer() {
      uni.navigateTo({ url: '/pages/contact/index' });
    },
    onDistrictChange(e) {
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
    showRemark(remark) {
      this.currentRemark = remark;
      this.$refs.remarkPopup.open();
    },
    closeRemark() {
      this.$refs.remarkPopup.close();
    },
    // 兼容所有端的 onChange
    onNeedGoUpstairsChange(e) {
      this.needGoUpstairs = (e.detail && e.detail.value) ? e.detail.value : e.target.value;
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
  display: flex !important;
  flex-direction: row !important;
  gap: 40rpx;
  margin-top: 20rpx;
}
.radio-label {
  display: flex;
  align-items: center;
  font-size: 28rpx;
  color: #333;
  margin-right: 24rpx;
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
  max-height: 80vh; /* 限制最大高度为屏幕的80% */
  overflow-y: auto; /* 内容超出时显示滚动条 */
  box-sizing: border-box; /* 确保内边距不影响总高度 */
}
.popup-title {
  font-size: 32rpx;
  font-weight: bold;
  text-align: center;
  margin-bottom: 20rpx;
  color: #222;
}
.quote-item {
  padding: 20rpx 0;
  border-bottom: 1px solid #eee;
  font-size: 30rpx;
  display: flex;
  align-items: center;
}
.price {
  font-weight: bold;
  color: #e64340;
}
.remark-btn {
  margin-left: 18rpx;
  padding: 8rpx 24rpx;
  font-size: 24rpx;
  background: #f4f6f9;
  color: #007aff;
  border: 1px solid #007aff;
  border-radius: 8rpx;
}
.remark-content {
  font-size: 28rpx;
  color: #333;
  line-height: 1.8;
  text-align: justify;
  white-space: pre-wrap;
  word-break: break-word;
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
.quote-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
.remark-btn {
  margin-left: 10rpx;
  padding: 8rpx 24rpx;
  font-size: 24rpx;
  background: #f4f6f9;
  color: #007aff;
  border: 1px solid #007aff;
  border-radius: 8rpx;
}
.big-remark-popup {
  position: relative;
  width: 92vw;
  min-height: 40vh;
  max-height: 75vh;
  border-top-left-radius: 28rpx;
  border-top-right-radius: 28rpx;
  background: #fff;
  padding: 32rpx 24rpx;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  box-shadow: 0 -10rpx 32rpx rgba(0, 0, 0, 0.15);
  margin: 0 auto;
  animation: fadeInUp 0.3s ease;
}

.remark-content-scroll {
  width: 100%;
  flex: 1 1 0;
  max-height: 450rpx;
  overflow-y: auto;
  margin: 16rpx 0 24rpx 0;
  background: #fafafa;
  border-radius: 12rpx;
  padding: 16rpx;
}

.remark-content {
  color: #333;
  font-size: 28rpx;
  white-space: pre-wrap;
  word-break: break-all;
}
.close-icon {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
  font-size: 36rpx;
  color: #aaa;
  z-index: 10;
  background: #f0f0f0;
  border-radius: 50%;
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.08);
}
.close-icon:hover {
  background: #e0e0e0;

}

.remark-scroll-view {
  flex: 1;
  overflow-y: auto;
  max-height: 60vh;
  background: #f9f9f9;
  border-radius: 20rpx;
  padding: 24rpx;
  box-sizing: border-box;
}


/* 弹入过渡动画（可选） */
@keyframes fadeInUp {
  0% {
    transform: translateY(100rpx);
    opacity: 0;
  }
  100% {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
