<template>
  <div :class="classObj" class="app-wrapper" :style="{ '--current-color': theme }">
    <div v-if="device === 'mobile' && sidebar.opened" class="drawer-bg" @click="handleClickOutside"/>
    <sidebar v-if="!sidebar.hide" class="sidebar-container" />
    <div :class="{ hasTagsView: needTagsView, sidebarHide: sidebar.hide }" class="main-container">
      <div :class="{ 'fixed-header': fixedHeader }">
        <navbar @setLayout="setLayout" />
        <tags-view v-if="needTagsView" />
      </div>
      <app-main />
      <settings ref="settingRef" />
    </div>
    <el-dialog v-model="noticeVisible" title="系统公告" width="600px" :close-on-click-modal="false" destroy-on-close>
      <div v-for="item in noticeList" :key="item.noticeId" class="notice-item">
        <h3 class="notice-title">{{ item.noticeTitle }}</h3>
        <div class="notice-content" v-html="item.noticeContent"></div>
        <div class="notice-time">{{ item.createTime }}</div>
      </div>
      <div v-if="noticeList.length === 0" class="notice-empty">暂无公告</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useWindowSize } from '@vueuse/core'
import Sidebar from './components/Sidebar/index.vue'
import { AppMain, Navbar, Settings, TagsView } from './components'
import useAppStore from '@/store/modules/app'
import useSettingsStore from '@/store/modules/settings'
import useUserStore from '@/store/modules/user'
import { checkPermi } from '@/utils/permission'
import { listNotice } from '@/api/system/notice'

const settingsStore = useSettingsStore()
const theme = computed(() => settingsStore.theme);
const sideTheme = computed(() => settingsStore.sideTheme);
const sidebar = computed(() => useAppStore().sidebar);
const device = computed(() => useAppStore().device);
const needTagsView = computed(() => settingsStore.tagsView);
const fixedHeader = computed(() => settingsStore.fixedHeader);

const classObj = computed(() => ({
  hideSidebar: !sidebar.value.opened,
  openSidebar: sidebar.value.opened,
  withoutAnimation: sidebar.value.withoutAnimation,
  mobile: device.value === 'mobile'
}))

const { width, height } = useWindowSize();
const WIDTH = 992; // refer to Bootstrap's responsive design

watch(() => device.value, () => {
  if (device.value === 'mobile' && sidebar.value.opened) {
    useAppStore().closeSideBar({ withoutAnimation: false })
  }
})

watchEffect(() => {
  if (width.value - 1 < WIDTH) {
    useAppStore().toggleDevice('mobile')
    useAppStore().closeSideBar({ withoutAnimation: true })
  } else {
    useAppStore().toggleDevice('desktop')
  }
})

function handleClickOutside() {
  useAppStore().closeSideBar({ withoutAnimation: false })
}

const settingRef = ref(null);
function setLayout() {
  settingRef.value.openSetting();
}

const noticeVisible = ref(false)
const noticeList = ref([])

onMounted(async () => {
  if (!checkPermi(['system:notice:query'])) return
  try {
    const res = await listNotice({ pageNum: 1, pageSize: 100, noticeType: '2', status: '0' })
    const data = res.data || res
    const rows = data.rows || []
    if (rows.length > 0) {
      noticeList.value = rows
      noticeVisible.value = true
    }
  } catch {
    // 静默处理
  }
})
</script>

<style lang="scss" scoped>
@use "@/assets/styles/mixin.scss" as mix;
@use "@/assets/styles/variables.module.scss" as vars;

.app-wrapper {
  @include mix.clearfix;
  position: relative;
  height: 100%;
  width: 100%;

  &.mobile.openSidebar {
    position: fixed;
    top: 0;
  }
}

.main-container:has(.fixed-header) {
  height: 100vh;
  overflow: hidden;
}

.drawer-bg {
  background: #000;
  opacity: 0.3;
  width: 100%;
  top: 0;
  height: 100%;
  position: absolute;
  z-index: 999;
}

.fixed-header {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 9;
  width: calc(100% - #{vars.$base-sidebar-width});
  transition: width 0.28s;
}

.hideSidebar .fixed-header {
  width: calc(100% - 54px);
}

.sidebarHide .fixed-header {
  width: 100%;
}

.mobile .fixed-header {
  width: 100%;
}
.notice-item {
  border-bottom: 1px solid #ebeef5;
  padding: 12px 0;
}
.notice-item:last-child {
  border-bottom: none;
}
.notice-title {
  font-size: 16px;
  color: #303133;
  margin: 0 0 8px;
}
.notice-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  word-break: break-all;
}
.notice-time {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
.notice-empty {
  text-align: center;
  color: #909399;
  padding: 20px 0;
}
</style>