<template>
  <div class="workbook-preview">
    <div v-if="loading" class="preview-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在生成表格图片...</span>
    </div>

    <button
      v-else-if="imageUrl"
      type="button"
      class="preview-image-button"
      @click="$emit('preview-click', imageUrl)"
    >
      <img :src="imageUrl" alt="历史排表预览图" />
      <span>点击放大查看</span>
    </button>

    <el-empty v-else description="暂无可预览的自由表格" />

    <div ref="captureRef" class="preview-capture" aria-hidden="true">
      <table v-if="previewModel" class="preview-table">
        <colgroup>
          <col
            v-for="column in previewModel.columns"
            :key="column.key"
            :style="{ width: column.width }"
          />
        </colgroup>
        <tbody>
          <tr
            v-for="row in previewModel.rows"
            :key="row.key"
            :style="{ height: row.height }"
          >
            <td
              v-for="cell in row.cells"
              :key="cell.key"
              :rowspan="cell.rowspan"
              :colspan="cell.colspan"
              :style="cell.style"
            >
              {{ cell.value }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import html2canvas from 'html2canvas'
import { computed, nextTick, ref, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { buildWorkbookPreviewModel } from '../utils/scheduleWorkbook'

const props = defineProps({
  workbook: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['preview-ready', 'preview-click'])

const captureRef = ref(null)
const imageUrl = ref('')
const loading = ref(false)

const previewModel = computed(() => props.workbook ? buildWorkbookPreviewModel(props.workbook) : null)

watch(
  () => props.workbook,
  () => refreshPreview(),
  { deep: true, immediate: true }
)

defineExpose({
  refreshPreview
})

async function refreshPreview() {
  imageUrl.value = ''
  emit('preview-ready', '')
  if (!props.workbook || !previewModel.value) return
  loading.value = true
  try {
    await nextTick()
    if (!captureRef.value) return
    const canvas = await html2canvas(captureRef.value, {
      backgroundColor: '#ffffff',
      scale: Math.min(2, window.devicePixelRatio || 1),
      logging: false
    })
    imageUrl.value = canvas.toDataURL('image/png')
    emit('preview-ready', imageUrl.value)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.workbook-preview {
  position: relative;
  min-height: 260px;
}

.preview-state {
  min-height: 260px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  color: #475569;
  font-size: 13px;
  font-weight: 700;
}

.preview-image-button {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.34);
  border-radius: 10px;
  padding: 8px;
  background: #f8fafc;
  cursor: zoom-in;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.preview-image-button:hover {
  border-color: rgba(14, 165, 233, 0.48);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.12);
  transform: translateY(-1px);
}

.preview-image-button img {
  width: 100%;
  max-height: 430px;
  object-fit: contain;
  background: #ffffff;
  border-radius: 6px;
}

.preview-image-button span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.preview-capture {
  position: fixed;
  left: -20000px;
  top: 0;
  z-index: -1;
  width: max-content;
  max-width: none;
  background: #ffffff;
  padding: 10px;
  pointer-events: none;
}

.preview-table {
  border-collapse: collapse;
  table-layout: fixed;
  font-family: "Microsoft YaHei", "SimSun", sans-serif;
  font-size: 12px;
  color: #111827;
}

.preview-table td {
  min-width: 56px;
  border: 1px solid #d6dce8;
  padding: 4px 8px;
  line-height: 1.35;
}
</style>
