<template>
  <div class="app-container ai-workbench">
    <header class="page-header">
      <div>
        <div class="eyebrow">MODEL CONFIGURATION</div>
        <h1>大模型配置</h1>
        <p>统一管理模型连接，并核对每位用户的真实 Token 消耗。</p>
      </div>
      <el-button v-if="activeTab === 'connections'" type="primary" icon="Plus" @click="startCreate">新建连接</el-button>
    </header>

    <el-tabs v-model="activeTab" class="main-tabs" @tab-change="handleTabChange">
      <el-tab-pane label="模型连接" name="connections">

    <section v-if="activeConnection" class="active-strip">
      <div class="active-mark"><span></span>当前系统 AI</div>
      <div class="active-main">
        <strong>{{ activeConnection.name }}</strong>
        <span>{{ activeConnection.provider }} · {{ activeConnection.model }}</span>
      </div>
      <code>{{ activeConnection.baseUrl }}</code>
      <el-tag effect="plain">{{ protocolLabel(activeConnection.protocol) }}</el-tag>
    </section>
    <el-alert v-else title="当前没有可用的系统 AI 连接，请先新建并配置 API Key。" type="warning" :closable="false" show-icon />

    <main class="workbench-grid">
      <section class="panel connections-panel">
        <div class="panel-title">
          <div><h2>连接列表</h2><span>{{ filteredConnections.length }} 个结果</span></div>
          <el-button circle icon="Refresh" :loading="loading" @click="loadConnections" />
        </div>
        <el-input v-model="keyword" clearable prefix-icon="Search" placeholder="搜索名称、供应商或模型" />
        <div v-loading="loading" class="connection-list">
          <button v-for="item in filteredConnections" :key="item.id" type="button" class="connection-card" :class="{ selected: selectedId === item.id, active: item.active }" @click="selectConnection(item)">
            <div class="connection-top">
              <span class="provider-avatar">{{ providerInitial(item.provider) }}</span>
              <span class="connection-name">{{ item.name }}</span>
              <span v-if="item.active" class="active-badge">当前</span>
            </div>
            <div class="connection-model">{{ item.model }}</div>
            <div class="connection-meta">
              <span>{{ item.provider }}</span>
              <span :class="item.apiKeyConfigured ? 'key-ready' : 'key-missing'">{{ item.apiKeyConfigured ? '密钥已配置' : '缺少密钥' }}</span>
            </div>
          </button>
          <div v-if="!loading && !filteredConnections.length" class="empty-list">
            <span>暂无匹配连接</span>
            <el-button link type="primary" @click="startCreate">创建第一个连接</el-button>
          </div>
        </div>
      </section>

      <section class="panel editor-panel">
        <div class="panel-title">
          <div>
            <h2>{{ selectedId ? '连接配置' : '新建连接' }}</h2>
            <span v-if="selectedConnection?.active" class="active-warning">保存后立即影响系统 AI</span>
            <span v-else>密钥只会加密保存在服务端</span>
          </div>
          <div v-if="selectedId" class="editor-actions">
            <el-button v-if="!selectedConnection?.active" type="success" plain @click="setActive">设为当前</el-button>
            <el-button type="danger" plain :disabled="selectedConnection?.active" @click="removeConnection">删除</el-button>
          </div>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
          <div class="form-row two">
            <el-form-item label="连接名称" prop="name"><el-input v-model.trim="form.name" maxlength="100" placeholder="例如：生产环境主模型" /></el-form-item>
            <el-form-item label="供应商" prop="provider"><el-input v-model.trim="form.provider" maxlength="50" placeholder="OpenAI / Mimo / 自定义" /></el-form-item>
          </div>
          <el-form-item label="Base URL" prop="baseUrl"><el-input v-model.trim="form.baseUrl" placeholder="https://api.example.com/v1" /></el-form-item>
          <el-form-item prop="apiKey">
            <template #label><span>API Key</span><span v-if="selectedConnection?.apiKeyConfigured" class="field-note">已配置，留空保留原密钥</span></template>
            <el-input v-model.trim="form.apiKey" type="password" show-password autocomplete="new-password" maxlength="512" :placeholder="selectedId ? '留空保留当前密钥' : '请输入 API Key'" />
          </el-form-item>
          <div class="form-row two">
            <el-form-item label="接口协议" prop="protocol">
              <el-select v-model="form.protocol" style="width: 100%"><el-option label="Chat Completions" value="chat_completions" /><el-option label="Responses API" value="responses" /></el-select>
            </el-form-item>
            <el-form-item label="模型" prop="model">
              <el-select v-model="form.model" filterable allow-create default-first-option style="width: 100%" placeholder="选择或输入模型 ID"><el-option v-for="model in discoveredModels" :key="model" :label="model" :value="model" /></el-select>
            </el-form-item>
          </div>
          <div class="model-discovery">
            <div><strong>上游模型发现</strong><span>使用当前 Base URL 和密钥读取模型列表，不会保存表单。</span></div>
            <el-button :loading="discovering" @click="discoverModels">读取模型</el-button>
          </div>
          <div class="form-row three">
            <el-form-item label="最大输出 Token" prop="maxTokens"><el-input-number v-model="form.maxTokens" :min="1" :max="128000" controls-position="right" style="width: 100%" /></el-form-item>
            <el-form-item label="温度（留空用默认）" prop="temperature"><el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" controls-position="right" style="width: 100%" /></el-form-item>
            <el-form-item label="图片输入"><el-switch v-model="form.supportImages" active-text="支持" inactive-text="不支持" /></el-form-item>
          </div>
          <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" maxlength="500" show-word-limit placeholder="说明用途、环境或使用范围" /></el-form-item>
          <div class="save-row">
            <el-button type="primary" icon="Check" :loading="saving" @click="saveConnection">保存连接</el-button>
            <span>测试聊天始终使用右侧当前表单，不会自动切换全局连接。</span>
          </div>
        </el-form>
      </section>

      <section class="panel chat-panel">
        <div class="panel-title">
          <div><h2>连接测试</h2><span>真实请求 · 不改变当前系统 AI</span></div>
          <el-button link type="primary" :disabled="!messages.length" @click="clearChat">清空</el-button>
        </div>
        <div ref="chatBodyRef" class="chat-body">
          <div v-if="!messages.length" class="chat-empty"><span class="chat-empty-icon">AI</span><strong>测试当前表单里的连接</strong><p>可连续对话；支持图片时可添加最多 4 张图片。</p></div>
          <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
            <div class="message-role">{{ message.role === 'user' ? '你' : 'AI' }}</div>
            <div class="message-content">
              <p>{{ message.content }}</p>
              <div v-if="message.images?.length" class="message-images"><img v-for="(image, imageIndex) in message.images" :key="imageIndex" :src="image" alt="测试图片" /></div>
            </div>
          </div>
        </div>
        <div class="composer">
          <div v-if="pendingImages.length" class="pending-images">
            <div v-for="(image, index) in pendingImages" :key="index"><img :src="image" alt="待发送图片" /><button type="button" aria-label="移除图片" @click="pendingImages.splice(index, 1)">×</button></div>
          </div>
          <el-input v-model="prompt" type="textarea" :rows="4" resize="none" maxlength="20000" placeholder="输入测试消息，Ctrl + Enter 发送" @keydown.ctrl.enter.prevent="sendMessage" />
          <div class="composer-actions">
            <div><input ref="imageInputRef" class="hidden-input" type="file" accept="image/png,image/jpeg,image/webp,image/gif" multiple @change="handleImages" /><el-button icon="Picture" :disabled="!form.supportImages || pendingImages.length >= 4" @click="imageInputRef?.click()">添加图片</el-button></div>
            <el-button type="primary" :loading="testing" :disabled="!prompt.trim() && !pendingImages.length" @click="sendMessage">发送测试</el-button>
          </div>
        </div>
      </section>
    </main>
      </el-tab-pane>
      <el-tab-pane label="Token请求记录" name="usage">
        <section class="panel usage-panel">
          <el-form :inline="true" :model="usageQuery" class="usage-filter">
            <el-form-item label="用户"><el-input v-model.trim="usageQuery.userKeyword" clearable placeholder="账号 / 昵称 / 用户ID" /></el-form-item>
            <el-form-item label="连接"><el-select v-model="usageQuery.connectionId" clearable placeholder="全部连接" style="width: 180px"><el-option v-for="item in connections" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
            <el-form-item label="模型"><el-input v-model.trim="usageQuery.model" clearable placeholder="模型名称" /></el-form-item>
            <el-form-item label="业务场景"><el-select v-model="usageQuery.scene" clearable placeholder="全部场景" style="width: 180px"><el-option v-for="item in sceneOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
            <el-form-item label="状态"><el-select v-model="usageQuery.status" clearable placeholder="全部状态" style="width: 120px"><el-option label="待处理" value="pending" /><el-option label="成功" value="success" /><el-option label="失败" value="failed" /></el-select></el-form-item>
            <el-form-item label="时间"><el-date-picker v-model="usageTimeRange" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" /></el-form-item>
            <el-form-item><el-button type="primary" icon="Search" @click="searchUsage">查询</el-button><el-button icon="Refresh" @click="resetUsage">重置</el-button></el-form-item>
          </el-form>

          <div class="usage-summary">
            <div><span>请求次数</span><strong>{{ usageSummary.requestCount.toLocaleString() }}</strong></div>
            <div><span>已上报 Usage</span><strong>{{ usageSummary.reportedCount.toLocaleString() }}</strong></div>
            <div><span>未上报 Usage</span><strong>{{ usageSummary.unreportedCount.toLocaleString() }}</strong></div>
            <div><span>总 Token</span><strong>{{ formatTokenCount(usageSummary.totalTokens) }}</strong></div>
          </div>

          <el-table v-loading="usageLoading" :data="usageRows" border>
            <el-table-column label="请求时间" prop="requestTime" width="170" />
            <el-table-column label="用户" min-width="160"><template #default="scope"><strong>{{ scope.row.nickName || scope.row.userName }}</strong><div class="cell-sub">{{ scope.row.userName }} · ID {{ scope.row.userId }}</div></template></el-table-column>
            <el-table-column label="连接 / 模型" min-width="210"><template #default="scope"><span>{{ scope.row.connectionName || '未保存连接' }}</span><div class="cell-sub">{{ scope.row.provider }} · {{ scope.row.model }}</div></template></el-table-column>
            <el-table-column label="协议" width="150"><template #default="scope">{{ protocolLabel(scope.row.protocol) }}</template></el-table-column>
            <el-table-column label="业务场景" width="150"><template #default="scope">{{ sceneLabel(scope.row.scene) }}</template></el-table-column>
            <el-table-column label="输入 Token" width="155"><template #default="scope">{{ formatTokenCount(scope.row.inputTokens) }}</template></el-table-column>
            <el-table-column label="输出 Token" width="155"><template #default="scope">{{ formatTokenCount(scope.row.outputTokens) }}</template></el-table-column>
            <el-table-column label="总 Token" width="165"><template #default="scope">{{ formatTokenCount(scope.row.totalTokens) }}</template></el-table-column>
            <el-table-column label="耗时" width="100"><template #default="scope">{{ scope.row.durationMs == null ? '-' : `${scope.row.durationMs} ms` }}</template></el-table-column>
            <el-table-column label="状态" width="90"><template #default="scope"><el-tag :type="scope.row.status === 'success' ? 'success' : scope.row.status === 'failed' ? 'danger' : 'warning'" effect="plain">{{ scope.row.status === 'success' ? '成功' : scope.row.status === 'failed' ? '失败' : '待处理' }}</el-tag></template></el-table-column>
            <el-table-column label="错误摘要" prop="errorMessage" min-width="220" show-overflow-tooltip />
          </el-table>
          <pagination v-show="usageTotal > 0" :total="usageTotal" v-model:page="usageQuery.pageNum" v-model:limit="usageQuery.pageSize" @pagination="loadUsage" />
        </section>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup name="SystemAiKey">
import { activateAiConnection, createAiConnection, deleteAiConnection, discoverAiModels, getAiUsageSummary, listAiConnections, listAiUsageRecords, testAiConnection, updateAiConnection } from '@/api/system/aiKey'
import { buildProbePayload, buildTestPayload, connectionToForm, emptyConnectionForm, formatTokenCount, validateImageFile } from './workbench.js'

const { proxy } = getCurrentInstance()
const loading = ref(false)
const saving = ref(false)
const discovering = ref(false)
const testing = ref(false)
const connections = ref([])
const keyword = ref('')
const selectedId = ref(null)
const discoveredModels = ref([])
const formRef = ref()
const chatBodyRef = ref()
const imageInputRef = ref()
const form = reactive(emptyConnectionForm())
const messages = ref([])
const prompt = ref('')
const pendingImages = ref([])
const activeTab = ref('connections')
const usageLoading = ref(false)
const usageRows = ref([])
const usageTotal = ref(0)
const usageTimeRange = ref([])
const usageSummary = reactive({ requestCount: 0, reportedCount: 0, unreportedCount: 0, totalTokens: 0 })
const usageQuery = reactive({ userKeyword: '', connectionId: null, model: '', scene: '', status: '', pageNum: 1, pageSize: 20 })
const sceneOptions = [
  { value: 'connection_test', label: '连接测试' },
  { value: 'internal_power_image', label: '内功图片识别' },
  { value: 'player_panel', label: '玩家属性面板' },
  { value: 'defense_panel', label: '坦度面板' },
  { value: 'internal_power_defense_entries', label: '内功防御词条' }
]

const activeConnection = computed(() => connections.value.find(item => item.active))
const selectedConnection = computed(() => connections.value.find(item => item.id === selectedId.value))
const filteredConnections = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return query ? connections.value.filter(item => [item.name, item.provider, item.model].some(value => String(value || '').toLowerCase().includes(query))) : connections.value
})

const rules = {
  name: [{ required: true, message: '请输入连接名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请输入供应商', trigger: 'blur' }],
  baseUrl: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }, { pattern: /^https?:\/\/[^\s]+$/i, message: '请输入完整的 http/https 地址', trigger: 'blur' }],
  apiKey: [{ validator: (_rule, value, callback) => (!selectedId.value && !String(value || '').trim() ? callback(new Error('新建连接必须填写 API Key')) : callback()), trigger: 'blur' }],
  model: [{ required: true, message: '请选择或输入模型 ID', trigger: 'change' }]
}

onMounted(loadConnections)

async function loadConnections(preferredId) {
  loading.value = true
  try {
    const res = await listAiConnections()
    connections.value = res.data || []
    const target = connections.value.find(item => item.id === (preferredId || selectedId.value)) || activeConnection.value || connections.value[0]
    target ? selectConnection(target) : startCreate()
  } finally { loading.value = false }
}

function selectConnection(connection) {
  selectedId.value = connection.id
  Object.assign(form, connectionToForm(connection))
  discoveredModels.value = connection.model ? [connection.model] : []
  formRef.value?.clearValidate()
}

function startCreate() {
  selectedId.value = null
  Object.assign(form, emptyConnectionForm())
  discoveredModels.value = []
  messages.value = []
  pendingImages.value = []
  formRef.value?.clearValidate()
}

async function saveConnection() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = { ...form, apiKey: form.apiKey || undefined }
    const wasEditing = Boolean(selectedId.value)
    if (wasEditing) await updateAiConnection(selectedId.value, payload)
    else await createAiConnection(payload)
    proxy.$modal.msgSuccess(wasEditing ? '连接已保存' : '连接已创建')
    const currentName = form.name
    const res = await listAiConnections()
    connections.value = res.data || []
    const target = wasEditing ? connections.value.find(item => item.id === selectedId.value) : connections.value.find(item => item.name === currentName)
    if (target) selectConnection(target)
  } finally { saving.value = false }
}

async function setActive() {
  if (!selectedId.value) return
  await proxy.$modal.confirm(`确定将“${selectedConnection.value?.name}”设为全系统当前 AI？下一次 AI 请求会立即使用它。`)
  await activateAiConnection(selectedId.value)
  proxy.$modal.msgSuccess('系统 AI 已切换')
  await loadConnections(selectedId.value)
}

async function removeConnection() {
  if (!selectedId.value || selectedConnection.value?.active) return
  await proxy.$modal.confirm(`确定删除“${selectedConnection.value?.name}”？此操作无法撤销。`)
  await deleteAiConnection(selectedId.value)
  proxy.$modal.msgSuccess('连接已删除')
  selectedId.value = null
  await loadConnections()
}

async function discoverModels() {
  if (!form.baseUrl || (!selectedId.value && !form.apiKey)) return proxy.$modal.msgWarning('请先填写 Base URL 和 API Key')
  discovering.value = true
  try {
    const res = await discoverAiModels(buildProbePayload(selectedId.value, form))
    discoveredModels.value = res.data?.models || []
    if (!form.model && discoveredModels.value.length) form.model = discoveredModels.value[0]
    proxy.$modal.msgSuccess(`已读取 ${discoveredModels.value.length} 个模型`)
  } finally { discovering.value = false }
}

async function sendMessage() {
  const content = prompt.value.trim()
  if ((!content && !pendingImages.value.length) || testing.value) return
  if (!form.model || !form.baseUrl || (!selectedId.value && !form.apiKey)) return proxy.$modal.msgWarning('请先完成连接、模型和密钥配置')
  const userMessage = { role: 'user', content, images: [...pendingImages.value] }
  const requestMessages = [...messages.value, userMessage].map(item => ({ role: item.role, content: item.content, images: item.images || [] }))
  messages.value.push(userMessage)
  prompt.value = ''
  pendingImages.value = []
  testing.value = true
  scrollChat()
  try {
    const res = await testAiConnection(buildTestPayload(selectedId.value, form, requestMessages))
    messages.value.push({ role: 'assistant', content: res.data?.text || '上游未返回文本', images: [] })
  } catch (error) {
    messages.value.pop()
    prompt.value = content
    pendingImages.value = userMessage.images
  } finally {
    testing.value = false
    scrollChat()
  }
}

function handleImages(event) {
  for (const file of Array.from(event.target.files || []).slice(0, 4 - pendingImages.value.length)) {
    const error = validateImageFile(file)
    if (error) { proxy.$modal.msgWarning(error); continue }
    const reader = new FileReader()
    reader.onload = () => pendingImages.value.push(reader.result)
    reader.readAsDataURL(file)
  }
  event.target.value = ''
}

function clearChat() { messages.value = []; prompt.value = ''; pendingImages.value = [] }
function scrollChat() { nextTick(() => { if (chatBodyRef.value) chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight }) }
function providerInitial(provider) { return String(provider || 'AI').slice(0, 2).toUpperCase() }
function protocolLabel(protocol) { return protocol === 'responses' ? 'Responses API' : 'Chat Completions' }
function sceneLabel(scene) { return sceneOptions.find(item => item.value === scene)?.label || scene || '-' }
function usageParams() { return { ...usageQuery, beginTime: usageTimeRange.value?.[0], endTime: usageTimeRange.value?.[1] } }
async function loadUsage() {
  usageLoading.value = true
  try {
    const params = usageParams()
    const [records, summary] = await Promise.all([listAiUsageRecords(params), getAiUsageSummary(params)])
    usageRows.value = records.rows || []
    usageTotal.value = records.total || 0
    Object.assign(usageSummary, summary.data || {})
  } finally { usageLoading.value = false }
}
function searchUsage() { usageQuery.pageNum = 1; loadUsage() }
function resetUsage() { Object.assign(usageQuery, { userKeyword: '', connectionId: null, model: '', scene: '', status: '', pageNum: 1, pageSize: 20 }); usageTimeRange.value = []; loadUsage() }
function handleTabChange(name) { if (name === 'usage') loadUsage() }
</script>

<style scoped>
.ai-workbench{--ink:#17221d;--muted:#6a7770;--line:#dfe8e2;--soft:#f5f8f6;--green:#287a55;min-height:calc(100vh - 84px);color:var(--ink);background:#f3f6f4}.page-header,.active-strip,.panel-title,.connection-top,.connection-meta,.model-discovery,.save-row,.composer-actions{display:flex;align-items:center}.page-header{justify-content:space-between;gap:24px;margin-bottom:16px}.eyebrow{margin-bottom:5px;color:var(--green);font-size:11px;font-weight:700;letter-spacing:1.6px}.page-header h1{margin:0;font-size:25px;line-height:1.3}.page-header p{margin:7px 0 0;color:var(--muted);font-size:13px}.active-strip{gap:18px;min-height:64px;margin-bottom:16px;padding:12px 16px;border:1px solid #bedcca;border-radius:9px;background:#edf8f1}.active-mark{min-width:116px;color:var(--green);font-size:12px;font-weight:700}.active-mark span{display:inline-block;width:8px;height:8px;margin-right:7px;border-radius:50%;background:#28a468;box-shadow:0 0 0 4px rgb(40 164 104/12%)}.active-main{display:flex;min-width:200px;flex-direction:column;gap:3px}.active-main span,.panel-title span,.model-discovery span,.save-row span{color:var(--muted);font-size:12px}.active-strip code{min-width:0;overflow:hidden;flex:1;color:#496158;font-size:12px;text-overflow:ellipsis;white-space:nowrap}.workbench-grid{display:grid;grid-template-columns:minmax(220px,.72fr) minmax(420px,1.35fr) minmax(340px,1fr);gap:14px;align-items:stretch}.panel{min-width:0;padding:17px;border:1px solid var(--line);border-radius:10px;background:#fff;box-shadow:0 3px 13px rgb(28 62 45/4%)}.panel-title{justify-content:space-between;gap:12px;min-height:35px;margin-bottom:14px}.panel-title h2{margin:0 0 3px;font-size:16px}.connection-list{min-height:300px;max-height:calc(100vh - 285px);margin-top:12px;overflow:auto}.connection-card{display:block;width:100%;margin-bottom:8px;padding:12px;border:1px solid var(--line);border-radius:8px;color:inherit;text-align:left;background:#fff;cursor:pointer;transition:.16s}.connection-card:hover,.connection-card.selected{border-color:#78b493;background:#f6fbf8}.connection-card.active{box-shadow:inset 3px 0 #2d9366}.connection-top{gap:8px}.provider-avatar{display:grid;width:30px;height:30px;place-items:center;border-radius:7px;color:#246345;font-size:10px;font-weight:800;background:#e3f2e9}.connection-name{min-width:0;overflow:hidden;flex:1;font-weight:700;text-overflow:ellipsis;white-space:nowrap}.active-badge{padding:2px 6px;border-radius:9px;color:#237a50;font-size:11px;background:#dcf4e6}.connection-model{margin:9px 0 7px 38px;overflow:hidden;color:#42534a;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px;text-overflow:ellipsis;white-space:nowrap}.connection-meta{justify-content:space-between;margin-left:38px;color:var(--muted);font-size:11px}.key-ready{color:#27805a}.key-missing{color:#b36d26}.empty-list,.chat-empty{display:flex;min-height:220px;align-items:center;justify-content:center;flex-direction:column;gap:8px;color:var(--muted)}.editor-actions{display:flex;gap:6px}.active-warning{color:#b26422!important;font-weight:600}.field-note{margin-left:8px;color:#829087;font-size:12px;font-weight:400}.form-row{display:grid;gap:12px}.form-row.two{grid-template-columns:repeat(2,minmax(0,1fr))}.form-row.three{grid-template-columns:1fr 1fr .8fr}.model-discovery{justify-content:space-between;gap:12px;margin:-2px 0 15px;padding:10px 12px;border:1px dashed #c9d8cf;border-radius:7px;background:var(--soft)}.model-discovery strong,.model-discovery span{display:block}.model-discovery strong{margin-bottom:3px;font-size:13px}.save-row{gap:12px;padding-top:3px}.chat-panel{display:flex;min-height:620px;flex-direction:column}.chat-body{min-height:300px;overflow:auto;flex:1;margin:0 -4px 12px;padding:4px}.chat-empty-icon{display:grid;width:44px;height:44px;place-items:center;border-radius:12px;color:#2a7653;font-weight:800;background:#e5f3ea}.chat-empty p{margin:0;font-size:12px;text-align:center}.message{display:flex;gap:8px;margin-bottom:13px}.message.user{flex-direction:row-reverse}.message-role{display:grid;width:28px;height:28px;flex:0 0 28px;place-items:center;border-radius:7px;color:#2d7252;font-size:11px;font-weight:700;background:#e5f3ea}.message.user .message-role{color:#536178;background:#e9edf3}.message-content{max-width:calc(100% - 44px);padding:9px 11px;border:1px solid var(--line);border-radius:3px 10px 10px 10px;background:#f8faf9}.message.user .message-content{border-radius:10px 3px 10px 10px;background:#edf5f0}.message-content p{margin:0;white-space:pre-wrap;word-break:break-word;line-height:1.55}.message-images,.pending-images{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}.message-images img,.pending-images img{width:54px;height:54px;border-radius:5px;object-fit:cover}.composer{padding-top:12px;border-top:1px solid var(--line)}.pending-images>div{position:relative}.pending-images button{position:absolute;top:-6px;right:-5px;width:18px;height:18px;padding:0;border:0;border-radius:50%;color:#fff;line-height:18px;background:#59665f;cursor:pointer}.composer-actions{justify-content:space-between;margin-top:9px}.hidden-input{display:none}:deep(.el-form-item){margin-bottom:15px}:deep(.el-form-item__label){color:#35423b;font-weight:600}:deep(.el-button--primary){--el-button-bg-color:#2e805a;--el-button-border-color:#2e805a;--el-button-hover-bg-color:#276e4e;--el-button-hover-border-color:#276e4e}
.main-tabs{margin-top:-4px}.usage-panel{padding:18px}.usage-filter{margin-bottom:6px}.usage-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:16px}.usage-summary>div{padding:14px;border:1px solid var(--line);border-radius:8px;background:var(--soft)}.usage-summary span,.usage-summary strong{display:block}.usage-summary span{margin-bottom:7px;color:var(--muted);font-size:12px}.usage-summary strong{font-size:19px}.cell-sub{margin-top:4px;color:var(--muted);font-size:11px}
@media(max-width:1500px){.workbench-grid{grid-template-columns:240px minmax(420px,1fr)}.chat-panel{grid-column:1/-1;min-height:500px}.chat-body{max-height:420px}}@media(max-width:900px){.workbench-grid{grid-template-columns:1fr}.chat-panel{grid-column:auto}.connection-list{max-height:360px}}@media(max-width:640px){.page-header,.active-strip,.panel-title,.save-row{align-items:flex-start;flex-direction:column}.form-row.two,.form-row.three{grid-template-columns:1fr}.active-strip code{width:100%}.panel{padding:14px}}
</style>
