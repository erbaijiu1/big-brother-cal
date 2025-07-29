<template>
  <view class="wx-fab" @click="openCorpWx">
    <image src="@/static/qywx_icon.png" mode="widthFix" class="wx-icon" />
    <uni-popup ref="qrPopup" type="center">
      <view class="qr-wrap">
        <!-- <image src="@/static/corp_wx_qr.png" mode="widthFix" class="qr-img" /> -->
        <image src="@/static/qywx_qr_code.png" wode="widthFix" class="qr-img" />
        <text class="qr-tip">长按识别，添加企业微信客服</text>
      </view>
    </uni-popup>
  </view>
</template>

<script>
import uniPopup from '@dcloudio/uni-ui/lib/uni-popup/uni-popup.vue'

export default {
  name: 'WechatFab',
  components: {
    uniPopup
  },
  methods: {
    openCorpWx () {
      const link = 'https://work.weixin.qq.com/ca/cawcdeae7f79de5a3d'

      /* #ifdef APP-PLUS */
      plus.runtime.openURL(link)
      /* #endif */

      /* #ifdef H5 */
      if (/micromessenger/i.test(navigator.userAgent)) {
        window.location.href = link
      } else {
        this.$refs.qrPopup.open()
      }
      /* #endif */

      /* #ifdef MP-WEIXIN */
      wx.openEmbeddedMiniProgram({
        appId: '',
        path: link
      })
      /* #endif */
    }
  }
}
</script>

<style scoped>
.wx-fab {
  position: fixed;
  right: 24rpx;
  bottom: 80rpx;
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: #07C160;
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.wx-icon {
  width: 60rpx;
  height: 60rpx;
}
.qr-wrap {
  padding: 40rpx 50rpx;
  background: #fff;
  border-radius: 24rpx;
}
.qr-img {
  width: 360rpx;
}
.qr-tip {
  display: block;
  text-align: center;
  font-size: 26rpx;
  color: #555;
  margin-top: 24rpx;
}
</style>
