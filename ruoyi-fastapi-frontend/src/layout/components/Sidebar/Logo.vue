<template>
  <div class="sidebar-logo-container" :class="{ 'collapse': collapse }">
    <transition name="sidebarLogoFade">
      <router-link v-if="collapse" key="collapse" class="sidebar-logo-link" to="/">
        <img v-if="logo" :src="logo" class="sidebar-logo" />
        <h1 v-else class="sidebar-title">{{ title }}</h1>
      </router-link>
      <router-link v-else key="expand" class="sidebar-logo-link" to="/">
        <img v-if="logo" :src="logo" class="sidebar-logo" />
        <h1 class="sidebar-title">{{ title }}</h1>
      </router-link>
    </transition>
  </div>
</template>

<script setup>
import logo from '@/assets/logo/logo.png'

defineProps({
  collapse: {
    type: Boolean,
    required: true
  }
})

const title = import.meta.env.VITE_APP_TITLE;

// 获取Logo背景色
const getLogoBackground = computed(() => {
  return 'transparent';
});

// 获取Logo文字颜色
const getLogoTextColor = computed(() => {
  return 'var(--sidebar-text)';
});
</script>

<style lang="scss" scoped>
.sidebarLogoFade-enter-active {
  transition: opacity 1.5s;
}

.sidebarLogoFade-enter,
.sidebarLogoFade-leave-to {
  opacity: 0;
}

.sidebar-logo-container {
  position: relative;
  height: 82px;
  line-height: 82px;
  background:
    radial-gradient(circle at 22% 10%, var(--app-yellow-soft), transparent 34%),
    linear-gradient(90deg, rgba(255, 255, 255, 0.12), transparent 72%),
    v-bind(getLogoBackground);
  text-align: center;
  overflow: hidden;
  border-bottom: 1px solid var(--app-sidebar-line);

  &::after {
    content: "";
    position: absolute;
    left: 28px;
    right: 28px;
    bottom: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(232, 215, 84, 0.6), transparent);
  }

  & .sidebar-logo-link {
    height: 100%;
    width: 100%;
    display: inline-flex;
    align-items: center;
    justify-content: center;

    & .sidebar-logo {
      width: 36px;
      height: 36px;
      vertical-align: middle;
      margin-right: 12px;
      filter: drop-shadow(0 10px 14px rgba(17, 24, 39, 0.24));
    }

    & .sidebar-title {
      display: inline-block;
      margin: 0;
      color: v-bind(getLogoTextColor);
      font-weight: 900;
      line-height: 82px;
      font-size: 14px;
      letter-spacing: 0;
      font-family: "HarmonyOS Sans SC", "MiSans", "PingFang SC", sans-serif;
      vertical-align: middle;
    }
  }

  &.collapse {
    .sidebar-logo {
      margin-right: 0px;
    }
  }
}
</style>
