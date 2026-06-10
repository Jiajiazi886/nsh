<template>
  <div class="app-container">
    <el-card>
      <div class="card-header">
        <span>职业颜色设置</span>
        <div class="header-actions">
          <el-button @click="handleExport">导出配置</el-button>
          <el-button v-if="hasEditPermission" @click="triggerImport">导入配置</el-button>
          <el-button v-if="hasEditPermission" type="primary" @click="handleSave" :loading="saveLoading">保存设置</el-button>
          <input
            ref="fileInputRef"
            class="file-input"
            type="file"
            accept="application/json,.json"
            @change="handleImport"
          />
        </div>
      </div>
      <el-table :data="colorList" border stripe>
        <el-table-column prop="class_name" label="职业" width="120" />
        <el-table-column label="背景颜色" width="200">
          <template #default="{ row }">
            <el-color-picker v-model="row.bg_color" :disabled="!hasEditPermission" />
            <span style="margin-left:8px">{{ row.bg_color }}</span>
          </template>
        </el-table-column>
        <el-table-column label="文字颜色" width="200">
          <template #default="{ row }">
            <el-color-picker v-model="row.text_color" :disabled="!hasEditPermission" />
            <span style="margin-left:8px">{{ row.text_color }}</span>
          </template>
        </el-table-column>
        <el-table-column label="预览" width="200">
          <template #default="{ row }">
            <span
              class="preview-tag"
              :style="{ backgroundColor: row.bg_color, color: row.text_color }"
            >{{ row.class_name }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getClassColors, saveClassColors } from '@/api/guild/classColor'
import { checkPermi } from '@/utils/permission'
import { normalizeClassColorList, setGuildClassColors } from '@/utils/guildClassColor'

const colorList = ref([])
const saveLoading = ref(false)
const fileInputRef = ref(null)
const hasEditPermission = ref(checkPermi(['guild:class-color:edit']))

onMounted(async () => {
  try {
    const res = await getClassColors()
    const data = res.data || res
    colorList.value = normalizeClassColorList(data || [])
    setGuildClassColors(colorList.value)
  } catch {
    ElMessage.error('加载颜色配置失败')
  }
})

async function handleSave() {
  saveLoading.value = true
  try {
    await persistColors()
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saveLoading.value = false
  }
}

async function persistColors() {
  const payload = {
    colors: colorList.value.map(item => ({
      class_name: item.class_name,
      bg_color: item.bg_color,
      text_color: item.text_color
    }))
  }
  await saveClassColors(payload)
  setGuildClassColors(colorList.value)
}

function handleExport() {
  const content = JSON.stringify({
    version: 1,
    exported_at: new Date().toISOString(),
    colors: colorList.value.map(item => ({
      class_name: item.class_name,
      bg_color: item.bg_color,
      text_color: item.text_color
    }))
  }, null, 2)
  const blob = new Blob([content], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `guild-class-colors-${new Date().toISOString().slice(0, 10)}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('职业颜色配置已导出')
}

function triggerImport() {
  fileInputRef.value?.click()
}

async function handleImport(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  try {
    const text = await file.text()
    const json = JSON.parse(text)
    const importedRows = normalizeClassColorList(Array.isArray(json) ? json : json.colors || [])
    if (!importedRows.length) {
      ElMessage.warning('JSON 中没有可导入的职业颜色配置')
      return
    }

    const importedMap = new Map(importedRows.map(item => [item.class_name, item]))
    let updatedCount = 0
    colorList.value = colorList.value.map(item => {
      const imported = importedMap.get(item.class_name)
      if (!imported) return item
      updatedCount += 1
      return {
        ...item,
        bg_color: imported.bg_color,
        text_color: imported.text_color
      }
    })

    if (!updatedCount) {
      ElMessage.warning('没有匹配到当前职业列表中的职业')
      return
    }

    saveLoading.value = true
    await persistColors()
    ElMessage.success(`已导入并保存 ${updatedCount} 个职业颜色`)
  } catch {
    ElMessage.error('导入失败，请确认文件是正确的 JSON')
  } finally {
    saveLoading.value = false
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.card-header span {
  font-size: 16px;
  font-weight: bold;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.file-input {
  display: none;
}
.preview-tag {
  display: inline-block;
  padding: 4px 12px;
  border: 1px solid currentColor;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
}
</style>
