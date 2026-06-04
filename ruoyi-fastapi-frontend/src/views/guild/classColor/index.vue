<template>
  <div class="app-container">
    <el-card>
      <div class="card-header">
        <span>职业颜色设置</span>
        <el-button v-if="hasEditPermission" type="primary" @click="handleSave" :loading="saveLoading">保存设置</el-button>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getClassColors, saveClassColors } from '@/api/guild/classColor'
import { checkPermi } from '@/utils/permission'

const colorList = ref([])
const saveLoading = ref(false)
const hasEditPermission = ref(checkPermi(['guild:class-color:edit']))

onMounted(async () => {
  try {
    const res = await getClassColors()
    const data = res.data || res
    colorList.value = (data || []).map(item => ({
      class_name: item.class_name,
      bg_color: item.bg_color || '#FFFFFF',
      text_color: item.text_color || '#000000'
    }))
  } catch {
    ElMessage.error('加载颜色配置失败')
  }
})

async function handleSave() {
  saveLoading.value = true
  try {
    const payload = { colors: colorList.value.map(item => ({
      class_name: item.class_name,
      bg_color: item.bg_color,
      text_color: item.text_color
    })) }
    await saveClassColors(payload)
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
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
.preview-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
}
</style>
