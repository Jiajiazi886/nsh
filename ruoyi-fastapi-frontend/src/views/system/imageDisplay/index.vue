<template>
  <div class="app-container image-display-admin">
    <section class="switch-panel" :class="{ disabled: !enabled }">
      <div class="switch-copy">
        <span class="eyebrow">全局版权风控</span>
        <h2>内功图片显示管理</h2>
        <p>
          关闭后，所有用户页面都不会渲染内功图片；系统仍保留图片地址和上传能力，方便后续重新开启。
        </p>
      </div>

      <div class="switch-control">
        <el-switch
          v-model="enabled"
          :loading="loading || saving"
          size="large"
          inline-prompt
          active-text="显示"
          inactive-text="隐藏"
          v-hasPermi="['system:internal-power-image-display:edit']"
          @change="handleToggle"
        />
        <strong>{{ enabled ? '网页正在显示内功图片' : '网页已隐藏内功图片' }}</strong>
        <span>{{ enabled ? '图片区域会正常加载内功图标。' : '图片区域只显示占位，不加载原图。' }}</span>
      </div>
    </section>
  </div>
</template>

<script setup name="SystemImageDisplay">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getInternalPowerImageDisplayStatus,
  updateInternalPowerImageDisplayStatus
} from '@/api/system/internalPowerImageDisplay'

const enabled = ref(true)
const loading = ref(false)
const saving = ref(false)

onMounted(loadStatus)

async function loadStatus() {
  loading.value = true
  try {
    const response = await getInternalPowerImageDisplayStatus()
    enabled.value = Boolean(response.data?.enabled)
  } catch {
    ElMessage.error('图片显示状态加载失败')
  } finally {
    loading.value = false
  }
}

async function handleToggle(value) {
  saving.value = true
  try {
    await updateInternalPowerImageDisplayStatus(Boolean(value))
    ElMessage.success(value ? '已开启内功图片显示' : '已隐藏所有内功图片')
  } catch {
    enabled.value = !value
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.image-display-admin {
  min-height: calc(100vh - 120px);
  display: grid;
  place-items: start center;
  padding-top: 32px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}

.switch-panel {
  width: min(760px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 28px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 8px;
  padding: 28px;
  background: #ffffff;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
}

.switch-panel.disabled {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 58%, #fff7ed 100%);
}

.switch-copy {
  display: grid;
  gap: 10px;
}

.eyebrow {
  width: fit-content;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 999px;
  padding: 4px 10px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 900;
}

.switch-copy h2 {
  margin: 0;
  color: #111827;
  font-size: 28px;
  font-weight: 950;
}

.switch-copy p {
  max-width: 520px;
  margin: 0;
  color: #64748b;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.8;
}

.switch-control {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  border-left: 1px solid rgba(15, 23, 42, 0.08);
  padding-left: 28px;
  text-align: center;
}

.switch-control strong {
  color: #111827;
  font-size: 15px;
  font-weight: 950;
}

.switch-control span {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

@media (max-width: 720px) {
  .switch-panel {
    grid-template-columns: 1fr;
  }

  .switch-control {
    border-left: 0;
    border-top: 1px solid rgba(15, 23, 42, 0.08);
    padding: 22px 0 0;
  }
}
</style>
