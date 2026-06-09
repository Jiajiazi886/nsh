<template>
  <div id="tags-view-container" class="tags-view-container">
    <scroll-pane ref="scrollPaneRef" class="tags-view-wrapper" @scroll="handleScroll">
      <router-link
        v-for="tag in visitedViews"
        :key="tag.path"
        :data-path="tag.path"
        :class="{ 'active': isActive(tag), 'has-icon': tagsIcon }"
        :to="{ path: tag.path, query: tag.query, fullPath: tag.fullPath }"
        class="tags-view-item"
        :style="activeStyle(tag)"
        @click.middle="!isAffix(tag) ? closeSelectedTag(tag) : ''"
        @contextmenu.prevent="openMenu(tag, $event)"
      >
        <svg-icon v-if="tagsIcon && tag.meta && tag.meta.icon && tag.meta.icon !== '#'" :icon-class="tag.meta.icon" />
        {{ tag.title }}
        <span v-if="!isAffix(tag)" @click.prevent.stop="closeSelectedTag(tag)">
          <close class="el-icon-close" style="width: 1em; height: 1em;vertical-align: middle;" />
        </span>
      </router-link>
    </scroll-pane>
    <ul v-show="visible" :style="{ left: left + 'px', top: top + 'px' }" class="contextmenu">
      <li @click="refreshSelectedTag(selectedTag)">
        <refresh-right style="width: 1em; height: 1em;" /> 刷新页面
      </li>
      <li v-if="!isAffix(selectedTag)" @click="closeSelectedTag(selectedTag)">
        <close style="width: 1em; height: 1em;" /> 关闭当前
      </li>
      <li @click="closeOthersTags">
        <circle-close style="width: 1em; height: 1em;" /> 关闭其他
      </li>
      <li v-if="!isFirstView()" @click="closeLeftTags">
        <back style="width: 1em; height: 1em;" /> 关闭左侧
      </li>
      <li v-if="!isLastView()" @click="closeRightTags">
        <right style="width: 1em; height: 1em;" /> 关闭右侧
      </li>
      <li @click="closeAllTags(selectedTag)">
        <circle-close style="width: 1em; height: 1em;" /> 全部关闭
      </li>
    </ul>
  </div>
</template>

<script setup>
import ScrollPane from './ScrollPane'
import { getNormalPath } from '@/utils/ruoyi'
import useTagsViewStore from '@/store/modules/tagsView'
import useSettingsStore from '@/store/modules/settings'
import usePermissionStore from '@/store/modules/permission'

const visible = ref(false);
const top = ref(0);
const left = ref(0);
const selectedTag = ref({});
const affixTags = ref([]);
const scrollPaneRef = ref(null);

const { proxy } = getCurrentInstance();
const route = useRoute();
const router = useRouter();

const visitedViews = computed(() => useTagsViewStore().visitedViews);
const routes = computed(() => usePermissionStore().routes);
const theme = computed(() => useSettingsStore().theme);
const tagsIcon = computed(() => useSettingsStore().tagsIcon)

watch(route, () => {
  addTags()
  moveToCurrentTag()
})
watch(visible, (value) => {
  if (value) {
    document.body.addEventListener('click', closeMenu)
  } else {
    document.body.removeEventListener('click', closeMenu)
  }
})
onMounted(() => {
  initTags()
  addTags()
})

function isActive(r) {
  return r.path === route.path
}
function activeStyle(tag) {
  if (!isActive(tag)) return {};
  return {
    "background": "linear-gradient(92deg, var(--app-charcoal), var(--app-primary))",
    "border-color": "rgba(255, 255, 255, 0.22)",
    "box-shadow": "0 14px 30px rgba(17, 24, 39, 0.18)"
  };
}
function isAffix(tag) {
  return tag.meta && tag.meta.affix
}
function isFirstView() {
  try {
    return selectedTag.value.fullPath === '/index' || selectedTag.value.fullPath === visitedViews.value[1].fullPath
  } catch (err) {
    return false
  }
}
function isLastView() {
  try {
    return selectedTag.value.fullPath === visitedViews.value[visitedViews.value.length - 1].fullPath
  } catch (err) {
    return false
  }
}
function filterAffixTags(routes, basePath = '') {
  let tags = []
  routes.forEach(route => {
    if (route.meta && route.meta.affix) {
      const tagPath = getNormalPath(basePath + '/' + route.path)
      tags.push({
        fullPath: tagPath,
        path: tagPath,
        name: route.name,
        meta: { ...route.meta }
      })
    }
    if (route.children) {
      const tempTags = filterAffixTags(route.children, route.path)
      if (tempTags.length >= 1) {
        tags = [...tags, ...tempTags]
      }
    }
  })
  return tags
}
function initTags() {
  const res = filterAffixTags(routes.value);
  affixTags.value = res;
  for (const tag of res) {
    // Must have tag name
    if (tag.name) {
       useTagsViewStore().addVisitedView(tag)
    }
  }
}
function addTags() {
  const { name } = route
  if (name) {
    useTagsViewStore().addView(route)
  }
}
function moveToCurrentTag() {
  nextTick(() => {
    for (const r of visitedViews.value) {
      if (r.path === route.path) {
        scrollPaneRef.value.moveToTarget(r);
        // when query is different then update
        if (r.fullPath !== route.fullPath) {
          useTagsViewStore().updateVisitedView(route)
        }
      }
    }
  })
}
function refreshSelectedTag(view) {
  proxy.$tab.refreshPage(view);
  if (route.meta.link) {
    useTagsViewStore().delIframeView(route);
  }
}
function closeSelectedTag(view) {
  proxy.$tab.closePage(view).then(({ visitedViews }) => {
    if (isActive(view)) {
      toLastView(visitedViews, view)
    }
  })
}
function closeRightTags() {
  proxy.$tab.closeRightPage(selectedTag.value).then(visitedViews => {
    if (!visitedViews.find(i => i.fullPath === route.fullPath)) {
      toLastView(visitedViews)
    }
  })
}
function closeLeftTags() {
  proxy.$tab.closeLeftPage(selectedTag.value).then(visitedViews => {
    if (!visitedViews.find(i => i.fullPath === route.fullPath)) {
      toLastView(visitedViews)
    }
  })
}
function closeOthersTags() {
  router.push(selectedTag.value).catch(() => { });
  proxy.$tab.closeOtherPage(selectedTag.value).then(() => {
    moveToCurrentTag()
  })
}
function closeAllTags(view) {
  proxy.$tab.closeAllPage().then(({ visitedViews }) => {
    if (affixTags.value.some(tag => tag.path === route.path)) {
      return
    }
    toLastView(visitedViews, view)
  })
}
function toLastView(visitedViews, view) {
  const latestView = visitedViews.slice(-1)[0]
  if (latestView) {
    router.push(latestView.fullPath)
  } else {
    // now the default is to redirect to the home page if there is no tags-view,
    // you can adjust it according to your needs.
    if (view.name === 'Dashboard') {
      // to reload home page
      router.replace({ path: '/redirect' + view.fullPath })
    } else {
      router.push('/')
    }
  }
}
function openMenu(tag, e) {
  const menuMinWidth = 105
  const offsetLeft = proxy.$el.getBoundingClientRect().left // container margin left
  const offsetWidth = proxy.$el.offsetWidth // container width
  const maxLeft = offsetWidth - menuMinWidth // left boundary
  const l = e.clientX - offsetLeft + 15 // 15: margin right

  if (l > maxLeft) {
    left.value = maxLeft
  } else {
    left.value = l
  }

  top.value = e.clientY
  visible.value = true
  selectedTag.value = tag
}
function closeMenu() {
  visible.value = false
}
function handleScroll() {
  closeMenu()
}
</script>

<style lang="scss" scoped>
.tags-view-container {
  height: 48px;
  width: 100%;
  background:
    radial-gradient(circle at 12% -10%, var(--app-yellow-soft), transparent 36%),
    linear-gradient(90deg, var(--app-primary-soft), transparent 38%),
    var(--tags-bg, #fff);
  border-top: 1px solid var(--app-border);
  border-bottom: 1px solid var(--tags-item-border, #d8dce5);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.38);
  backdrop-filter: blur(18px);
  .tags-view-wrapper {
    .tags-view-item {
      display: inline-block;
      position: relative;
      cursor: pointer;
      height: 30px;
      line-height: 30px;
      border: 1px solid var(--tags-item-border, #d8dce5);
      color: var(--tags-item-text, #495060);
      background: var(--tags-item-bg, #fff);
      padding: 0 12px;
      font-size: 12px;
      font-weight: 800;
      margin-left: 8px;
      margin-top: 9px;
      border-radius: 999px;
      transition: all 0.18s ease;

      &:hover {
        background: var(--tags-item-hover, #eee);
        color: var(--app-ink);
        transform: translateY(-1px);
      }

      &:first-of-type {
        margin-left: 15px;
      }

      &:last-of-type {
        margin-right: 15px;
      }

      &.active {
        color: #fff;

        &::before {
          content: '';
          background: #E8D754;
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          position: relative;
          margin-right: 5px;
        }
      }
    }
  }

  .tags-view-item.active.has-icon::before {
    content: none !important;
  }

  .contextmenu {
    margin: 0;
    background: var(--el-bg-color-overlay, #fff);
    z-index: 3000;
    position: absolute;
    list-style-type: none;
    padding: 5px 0;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 800;
    color: var(--tags-item-text, #333);
    box-shadow: 0 16px 34px rgba(17, 24, 39, 0.2);
    border: 1px solid var(--el-border-color-light, #e4e7ed);

    li {
      margin: 0;
      padding: 7px 16px;
      cursor: pointer;

      &:hover {
        background: var(--tags-item-hover, #eee);
        color: var(--app-ink);
      }
    }
  }
}

:global(.themeLight) .tags-view-container {
  height: 52px;
  background:
    linear-gradient(90deg, rgba(105, 71, 242, 0.07), transparent 42%),
    rgba(255, 255, 255, 0.7);
  border-color: rgba(38, 50, 69, 0.1);

  .tags-view-wrapper .tags-view-item {
    height: 32px;
    line-height: 32px;
    margin-top: 10px;
    color: #334155;
    background: rgba(255, 255, 255, 0.84);
    border-color: rgba(38, 50, 69, 0.12);

    &:hover {
      color: #111827;
      background: rgba(105, 71, 242, 0.08);
    }

    &.active {
      color: #ffffff;
    }
  }
}

:global(.themeDark) .tags-view-container {
  height: 42px;
  background:
    linear-gradient(90deg, rgba(155, 121, 255, 0.12), transparent 42%),
    rgba(7, 12, 22, 0.64);
  border-color: rgba(255, 255, 255, 0.1);

  .tags-view-wrapper .tags-view-item {
    height: 26px;
    line-height: 26px;
    margin-top: 8px;
    color: #d8e0ec;
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.12);

    &:hover {
      color: #ffffff;
      background: rgba(255, 255, 255, 0.1);
    }

    &.active {
      color: #ffffff;
    }
  }
}

html.dark {
  .tags-view-container .tags-view-wrapper .tags-view-item:hover,
  .tags-view-container .contextmenu li:hover {
    color: var(--app-ink);
  }
}
</style>

<style lang="scss">
//reset element css of el-icon-close
.tags-view-wrapper {
  .tags-view-item {
    .el-icon-close {
      width: 16px;
      height: 16px;
      vertical-align: 2px;
      border-radius: 50%;
      text-align: center;
      transition: all .3s cubic-bezier(.645, .045, .355, 1);
      transform-origin: 100% 50%;

      &:before {
        transform: scale(.6);
        display: inline-block;
        vertical-align: -3px;
      }

      &:hover {
        background-color: var(--tags-close-hover, #b4bccc);
        color: #fff;
        width: 12px !important;
        height: 12px !important;
      }
    }
  }
}
</style>
