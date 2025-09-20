<template>
    <view class="page">
        <!-- 顶部标签切换 -->
        <uni-segmented-control :current="current" :values="tabs" styleType="text" @clickItem="onTabChange" />

        <!-- 区域管理 -->
        <view v-show="current === 0" class="panel">
            <district-manager />
        </view>

        <!-- 类别管理 -->
        <view v-show="current === 1" class="panel">
            <area-category-manager />
        </view>
    </view>
</template>

<script setup>
    import { ref } from 'vue'
    import DistrictManager from '@/components/DistrictManager.vue'
    import AreaCategoryManager from '@/components/AreaCategoryManager.vue'

    const tabs = ['行政区维护', '自定义区域类别维护']
    const current = ref(0)
    function onTabChange(e) { current.value = e.currentIndex }
</script>

<style scoped>
.page {
    padding: 24rpx;
}

.panel {
    margin-top: 24rpx;
}
</style>
