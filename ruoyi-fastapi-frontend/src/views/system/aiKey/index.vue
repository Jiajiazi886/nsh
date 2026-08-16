<template>
  <div class="app-container ai-key-page">
    <section class="setting-panel">
      <div class="panel-heading">
        <div>
          <h2>AI 图片识别 API Key</h2>
          <p>项目中的内功图片、玩家面板和内功词条截图识别统一使用此密钥。</p>
        </div>
        <el-tag :type="status.apiKeyConfigured ? 'success' : 'info'" effect="plain">
          {{ status.apiKeyConfigured ? '已配置' : '未配置' }}
        </el-tag>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px" class="setting-form" @submit.prevent>
        <el-form-item label="API Key" prop="apiKey">
          <el-input
            v-model.trim="form.apiKey"
            type="password"
            show-password
            autocomplete="new-password"
            maxlength="128"
            :disabled="form.clearApiKey"
            :placeholder="status.apiKeyConfigured ? '输入新密钥即可替换当前密钥' : '请输入项目 AI 图片识别所需的 API Key'"
          />
        </el-form-item>
        <el-form-item v-if="status.apiKeyConfigured" label="密钥操作">
          <el-checkbox v-model="form.clearApiKey" :disabled="Boolean(form.apiKey)">清除当前 API Key</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Check" :loading="saving" @click="submitForm">保存设置</el-button>
          <span v-if="status.updateTime" class="update-time">最后修改：{{ parseTime(status.updateTime) }}{{ status.updateBy ? `（${status.updateBy}）` : '' }}</span>
        </el-form-item>
      </el-form>
    </section>
  </div>
</template>

<script setup name="SystemAiKey">
import { getInternalPowerAiKeyStatus, updateInternalPowerAiKey } from '@/api/system/aiKey'

const { proxy } = getCurrentInstance()
const formRef = ref()
const saving = ref(false)
const status = reactive({
  apiKeyConfigured: false,
  updateBy: '',
  updateTime: null
})
const form = reactive({
  apiKey: '',
  clearApiKey: false
})

const rules = {
  apiKey: [{
    validator: (_rule, value, callback) => {
      if (!form.clearApiKey && !String(value || '').trim()) callback(new Error('请输入 API Key'))
      else callback()
    },
    trigger: 'blur'
  }]
}

onMounted(loadStatus)

async function loadStatus() {
  const res = await getInternalPowerAiKeyStatus()
  Object.assign(status, res.data || {})
}

function submitForm() {
  formRef.value?.validate(async valid => {
    if (!valid) return
    saving.value = true
    try {
      await updateInternalPowerAiKey({ ...form })
      proxy.$modal.msgSuccess(form.clearApiKey ? 'AI 图片识别 API Key 已清除' : 'AI 图片识别 API Key 已保存')
      form.apiKey = ''
      form.clearApiKey = false
      await loadStatus()
      formRef.value?.clearValidate()
    } finally {
      saving.value = false
    }
  })
}
</script>

<style scoped>
.ai-key-page {
  max-width: 760px;
}

.setting-panel {
  padding: 24px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
}

.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 26px;
}

.panel-heading h2 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--el-text-color-primary);
}

.panel-heading p {
  margin: 0;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.setting-form {
  max-width: 620px;
}

.update-time {
  margin-left: 14px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

@media (max-width: 768px) {
  .setting-panel {
    padding: 18px;
  }

  .panel-heading {
    flex-direction: column;
  }

  .update-time {
    display: block;
    margin: 10px 0 0;
  }
}
</style>
