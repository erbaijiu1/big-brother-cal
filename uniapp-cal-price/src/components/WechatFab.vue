<template>
  <view class="wx-fab" @click="openCorpWx">
    <view class="fab-inner">
      <image src="@/static/qywx_icon.png" mode="widthFix" class="wx-icon" />
      <text class="fab-label">领新客优惠</text>
    </view>
    <uni-popup ref="qrPopup" type="center">
      <view class="qr-wrap">
        <image src="@/static/qywx_qr_code.png" mode="widthFix" class="qr-img" />
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
    /**
 * 给外部调用用的：弹出二维码弹窗
 */
    showPopup() {
      console.log('[WechatFab] showPopup 被调用')
      this.$refs.qrPopup?.open?.()
    },

    openCorpWx() {
      const link = 'https://work.weixin.qq.com/ca/cawcdeae7f79de5a3d'

      /* #ifdef APP-PLUS */
      plus.runtime.openURL(link)
      /* #endif */

      /* #ifdef H5 */
      if (/micromessenger/i.test(navigator.userAgent)) {
        window.location.href = link
      } else {
        this.showPopup()
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
  width: 138rpx;
  height: 138rpx;
  border-radius: 50%;
  /* background: #91bcf0; */
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.68);
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

.fab-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.fab-label {
  font-size: 20rpx;
  color: #000;
  margin-top: 16rpx;
}

</style>
