<template>
  <section class="app-main">
    <router-view v-slot="{ Component, route }">
      <transition name="fade-transform">
        <keep-alive :include="tagsViewStore.cachedViews">
          <component v-if="!route.meta.link" :is="Component" :key="route.path"/>
        </keep-alive>
      </transition>
    </router-view>
    <iframe-toggle />
    <copyright />
  </section>
</template>

<script setup>
import copyright from "./Copyright/index"
import iframeToggle from "./IframeToggle/index"
import useTagsViewStore from '@/store/modules/tagsView'

const route = useRoute()
const tagsViewStore = useTagsViewStore()

onMounted(() => {
  addIframe()
})

watchEffect(() => {
  addIframe()
})

function addIframe() {
  if (route.meta.link) {
    useTagsViewStore().addIframeView(route)
  }
}
</script>

<style lang="scss" scoped>
.app-main {
  min-height: calc(100vh - 66px);
  width: 100%;
  position: relative;
  overflow: hidden;
}

.fixed-header + .app-main {
  margin-top: 66px;
  height: calc(100vh - 66px);
  min-height: 0;
  overflow-y: auto;
  scrollbar-gutter: auto;
}

.app-main:has(.copyright) {
  padding-bottom: 36px;
}

.hasTagsView {
  .app-main {
    min-height: calc(100vh - 108px);
  }

  .fixed-header + .app-main {
    margin-top: 108px;
    height: calc(100vh - 108px);
    min-height: 0;
  }
}

:global(.themeDark) .app-main {
  min-height: calc(100vh - 62px);
}

:global(.themeDark) .fixed-header + .app-main {
  margin-top: 62px;
  height: calc(100vh - 62px);
}

:global(.themeDark) :global(.hasTagsView) .fixed-header + .app-main {
  margin-top: 98px;
  height: calc(100vh - 98px);
}

.app-main > :deep(.app-container),
.app-main > :deep(.home),
.app-main > :deep(.dashboard-editor-container) {
  min-height: 100%;
  position: relative;
}

:global(.themeLight) .app-main > :deep(.app-container),
:global(.themeLight) .app-main > :deep(.home),
:global(.themeLight) .app-main > :deep(.dashboard-editor-container) {
  background:
    radial-gradient(circle at 86% 8%, rgba(232, 215, 84, 0.18), transparent 28%),
    radial-gradient(circle at 10% 10%, rgba(105, 71, 242, 0.1), transparent 28%);
}

:global(.themeDark) .app-main > :deep(.app-container),
:global(.themeDark) .app-main > :deep(.home),
:global(.themeDark) .app-main > :deep(.dashboard-editor-container) {
  background:
    radial-gradient(circle at 86% 8%, rgba(240, 223, 97, 0.08), transparent 28%),
    radial-gradient(circle at 10% 10%, rgba(155, 121, 255, 0.12), transparent 28%);
}

@media screen and (max-width: 991px) {
  .fixed-header + .app-main,
  .hasTagsView .fixed-header + .app-main {
    padding-bottom: max(60px, calc(constant(safe-area-inset-bottom) + 40px));
    padding-bottom: max(60px, calc(env(safe-area-inset-bottom) + 40px));
    overscroll-behavior-y: none;
  }
}

@supports (-webkit-touch-callout: none) {
  @media screen and (max-width: 991px) {
    .fixed-header + .app-main {
      padding-bottom: max(17px, calc(constant(safe-area-inset-bottom) + 10px));
      padding-bottom: max(17px, calc(env(safe-area-inset-bottom) + 10px));
      height: calc(100svh - 66px);
      height: calc(100dvh - 66px);
    }

    .hasTagsView .fixed-header + .app-main {
      padding-bottom: max(17px, calc(constant(safe-area-inset-bottom) + 10px));
      padding-bottom: max(17px, calc(env(safe-area-inset-bottom) + 10px));
      height: calc(100svh - 108px);
      height: calc(100dvh - 108px);
    }
  }
}
</style>

<style lang="scss">
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background-color: rgba(17, 24, 39, 0.08);
}

::-webkit-scrollbar-thumb {
  background-color: rgba(105, 71, 242, 0.32);
  border-radius: 3px;
}
</style>
