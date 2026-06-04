<template>
  <ProfileEdit v-if="isProfileEditPage" />

  <div v-else class="app-container">
    <el-card shadow="never" class="placeholder-card">
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
        </div>
      </template>

      <el-result
        icon="info"
        :title="`${pageTitle} 正在建设中`"
        :sub-title="placeholderDescription"
      >
        <template #extra>
          <el-tag type="warning">当前菜单使用独立占位页，后续会在对应页面中补齐。</el-tag>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import ProfileEdit from '@/views/personal/profileEdit/index.vue'

const route = useRoute()

const pageTitle = computed(() => route.meta?.title || '个人管理')
const isProfileEditPage = computed(() => /(^|\/)profile-edit$/.test(route.path))

const placeholderDescription = computed(() => {
  return `${pageTitle.value} 暂未开放，后续会在独立页面中补齐。`
})
</script>

<style scoped>
.placeholder-card {
  min-height: calc(100vh - 180px);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
