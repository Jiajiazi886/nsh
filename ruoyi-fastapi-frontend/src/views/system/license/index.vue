<template>
  <div class="app-container license-page">
    <el-card shadow="never">
      <template #header>
        <div class="page-heading">
          <div>
            <h2>账号授权管理</h2>
            <p>为正常帮会成员账号发放使用期限。这里不生成卡密字符串，也不绑定设备。</p>
          </div>
          <div class="header-actions">
            <el-button v-hasPermi="['system:license:audit']" @click="openAudit">授权流水</el-button>
            <el-button type="primary" @click="loadAccounts">刷新</el-button>
          </div>
        </div>
      </template>
      <el-form :inline="true" :model="query" @submit.prevent>
        <el-form-item label="账号"><el-input v-model="query.keyword" clearable placeholder="登录账号或昵称" @keyup.enter="search" /></el-form-item>
        <el-form-item label="账号状态"><el-select v-model="query.accountStatus" clearable placeholder="全部" style="width: 120px"><el-option label="正常" value="normal" /><el-option label="停用" value="disabled" /></el-select></el-form-item>
        <el-form-item label="授权状态"><el-select v-model="query.authorizationStatus" clearable placeholder="全部" style="width: 120px"><el-option label="有效" value="active" /><el-option label="已过期" value="expired" /><el-option label="已撤销" value="revoked" /><el-option label="未授权" value="none" /></el-select></el-form-item>
        <el-form-item label="套餐"><el-select v-model="query.planType" clearable placeholder="全部" style="width: 120px"><el-option label="天卡" value="daily" /><el-option label="周卡" value="weekly" /><el-option label="月卡" value="monthly" /><el-option label="永久" value="permanent" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="search">搜索</el-button></el-form-item>
        <el-form-item><el-button @click="resetQuery">重置</el-button></el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" border @selection-change="selected = $event">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="userId" label="用户 ID" width="110" />
        <el-table-column prop="userName" label="登录账号" min-width="150" />
        <el-table-column prop="nickName" label="昵称" min-width="130" />
        <el-table-column label="账号状态" width="100"><template #default="{ row }"><el-tag :type="row.accountStatus === 'normal' ? 'success' : 'danger'">{{ row.accountStatus === 'normal' ? '正常' : '停用' }}</el-tag></template></el-table-column>
        <el-table-column label="成员资格" width="100"><template #default="{ row }"><el-tag :type="row.eligibleRole ? 'success' : 'warning'">{{ row.eligibleRole ? '帮会成员' : '不符合' }}</el-tag></template></el-table-column>
        <el-table-column label="授权状态" width="110"><template #default="{ row }"><el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="planType" label="套餐" width="100" />
        <el-table-column prop="validFrom" label="生效时间" width="190"><template #default="{ row }">{{ row.validFrom ? formatDate(row.validFrom) : '-' }}</template></el-table-column>
        <el-table-column prop="expiresAt" label="到期时间" width="190"><template #default="{ row }">{{ row.expiresAt ? formatDate(row.expiresAt) : (row.authorized ? '永久' : '-') }}</template></el-table-column>
        <el-table-column label="剩余时间" width="110"><template #default="{ row }">{{ remainingText(row) }}</template></el-table-column>
        <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
        <el-table-column prop="lastOperator" label="最后操作人" width="130" />
        <el-table-column label="操作" width="240" fixed="right"><template #default="{ row }">
          <el-button v-hasPermi="['system:license:grant']" link type="primary" @click="openGrant(row)">授权</el-button>
          <el-button v-hasPermi="['system:license:revoke']" link type="warning" :disabled="!row.authorized" @click="revoke(row)">撤销</el-button>
          <el-button v-hasPermi="['system:license:remark']" link @click="editRemark(row)">备注</el-button>
        </template></el-table-column>
      </el-table>
      <div class="table-footer">
        <div><el-button v-hasPermi="['system:license:grant']" type="primary" :disabled="!selected.length" @click="openGrant()">批量授权</el-button><el-button v-hasPermi="['system:license:revoke']" type="warning" :disabled="!selected.length" @click="revokeSelected">批量撤销</el-button></div>
        <el-pagination v-model:current-page="query.pageNum" v-model:page-size="query.pageSize" layout="total, sizes, prev, pager, next" :total="total" @current-change="loadAccounts" @size-change="loadAccounts" />
      </div>
    </el-card>

    <el-dialog v-model="grantVisible" title="发放账号授权" width="430px">
      <el-form label-width="90px">
        <el-form-item label="账号数量">{{ grantUsers.length }} 个</el-form-item>
        <el-form-item label="授权套餐"><el-select v-model="grantForm.planType" style="width: 100%"><el-option label="天卡（1天）" value="daily" /><el-option label="周卡（7天）" value="weekly" /><el-option label="月卡（30天）" value="monthly" /><el-option label="永久" value="permanent" /></el-select></el-form-item>
        <el-form-item label="备注"><el-input v-model="grantForm.remark" type="textarea" maxlength="500" show-word-limit /></el-form-item>
      </el-form>
      <template #footer><el-button @click="grantVisible = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submitGrant">确认授权</el-button></template>
    </el-dialog>

    <el-dialog v-model="remarkVisible" title="修改授权备注" width="430px">
      <el-input v-model="remarkForm.remark" type="textarea" maxlength="500" show-word-limit />
      <template #footer><el-button @click="remarkVisible = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submitRemark">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="auditVisible" title="账号授权流水" width="min(980px, 92vw)">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="用户 ID"><el-input v-model="auditQuery.userId" clearable placeholder="可选" style="width: 120px" @keyup.enter="loadAudit" /></el-form-item>
        <el-form-item label="账号"><el-input v-model="auditQuery.accountKeyword" clearable placeholder="账号或昵称" style="width: 150px" /></el-form-item>
        <el-form-item label="操作者"><el-input v-model="auditQuery.operatorKeyword" clearable placeholder="账号或昵称" style="width: 150px" /></el-form-item>
        <el-form-item label="动作"><el-select v-model="auditQuery.action" clearable placeholder="全部" style="width: 130px"><el-option label="发放" value="grant" /><el-option label="续期" value="extend" /><el-option label="撤销" value="revoke" /><el-option label="改备注" value="remark_update" /></el-select></el-form-item>
        <el-form-item label="批次"><el-input v-model="auditQuery.batchId" clearable placeholder="可选" style="width: 170px" /></el-form-item>
        <el-form-item label="开始时间"><el-date-picker v-model="auditQuery.startTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" clearable placeholder="可选" style="width: 190px" /></el-form-item>
        <el-form-item label="结束时间"><el-date-picker v-model="auditQuery.endTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" clearable placeholder="可选" style="width: 190px" /></el-form-item>
        <el-form-item><el-button type="primary" @click="loadAudit">查询</el-button></el-form-item>
      </el-form>
      <el-table v-loading="auditLoading" :data="auditRows" border>
        <el-table-column prop="createdAt" label="时间" width="180"><template #default="{ row }">{{ formatDate(row.createdAt) }}</template></el-table-column>
        <el-table-column prop="userId" label="用户 ID" width="100" />
        <el-table-column prop="userName" label="目标账号" width="130" />
        <el-table-column prop="operatorUserName" label="操作者" width="130" />
        <el-table-column prop="action" label="操作" width="105"><template #default="{ row }">{{ actionText(row.action) }}</template></el-table-column>
        <el-table-column label="状态变化" min-width="180"><template #default="{ row }">{{ stateSummary(row) }}</template></el-table-column>
        <el-table-column prop="remark" label="原因／备注" min-width="180" show-overflow-tooltip />
        <el-table-column prop="requestId" label="请求 ID" min-width="210" show-overflow-tooltip />
      </el-table>
      <div class="audit-footer"><el-pagination v-model:current-page="auditQuery.pageNum" v-model:page-size="auditQuery.pageSize" layout="total, sizes, prev, pager, next" :total="auditTotal" @current-change="loadAudit" @size-change="loadAudit" /></div>
    </el-dialog>
  </div>
</template>

<script setup name="SystemLicense">
import { listLicenseAccounts, grantLicense, revokeLicense, updateLicenseRemark, listLicenseAudit } from '@/api/system/license'

const { proxy } = getCurrentInstance()
const loading = ref(false)
const submitting = ref(false)
const rows = ref([])
const selected = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, keyword: '', accountStatus: '', authorizationStatus: '', planType: '' })
const grantVisible = ref(false)
const grantUsers = ref([])
const grantForm = reactive({ planType: 'monthly', remark: '' })
const remarkVisible = ref(false)
const remarkUser = ref(null)
const remarkForm = reactive({ remark: '' })
const auditVisible = ref(false)
const auditLoading = ref(false)
const auditRows = ref([])
const auditTotal = ref(0)
const auditQuery = reactive({ pageNum: 1, pageSize: 50, userId: '', accountKeyword: '', operatorKeyword: '', action: '', batchId: '', startTime: '', endTime: '' })

onMounted(loadAccounts)

async function loadAccounts() {
  loading.value = true
  try {
    const res = await listLicenseAccounts(query)
    rows.value = res.data?.rows || []
    total.value = res.data?.total || 0
  } finally { loading.value = false }
}
function search() { query.pageNum = 1; loadAccounts() }
function resetQuery() {
  Object.assign(query, { pageNum: 1, pageSize: 20, keyword: '', accountStatus: '', authorizationStatus: '', planType: '' })
  loadAccounts()
}
function requestId(prefix) { return prefix + '_' + Date.now() + '_' + Math.random().toString(36).slice(2, 10) }
function openGrant(row) {
  grantUsers.value = row ? [row] : selected.value.slice()
  if (!grantUsers.value.length) return proxy.$modal.msgWarning('请选择至少一个账号')
  grantForm.planType = 'monthly'; grantForm.remark = ''; grantVisible.value = true
}
async function submitGrant() {
  submitting.value = true
  try {
    await grantLicense({ requestId: requestId('grant'), userIds: grantUsers.value.map(item => String(item.userId)), planType: grantForm.planType, remark: grantForm.remark })
    proxy.$modal.msgSuccess('账号授权成功'); grantVisible.value = false; selected.value = []; await loadAccounts()
  } finally { submitting.value = false }
}
async function revoke(row) {
  await proxy.$modal.confirm('确定撤销账号“' + row.userName + '”的授权吗？')
  await revokeLicense({ requestId: requestId('revoke'), userIds: [String(row.userId)], reason: '管理员撤销' })
  proxy.$modal.msgSuccess('授权已撤销'); await loadAccounts()
}
async function revokeSelected() {
  await proxy.$modal.confirm('确定撤销选中的 ' + selected.value.length + ' 个账号吗？')
  await revokeLicense({ requestId: requestId('revoke'), userIds: selected.value.map(item => String(item.userId)), reason: '管理员批量撤销' })
  proxy.$modal.msgSuccess('授权已撤销'); selected.value = []; await loadAccounts()
}
function editRemark(row) { remarkUser.value = row; remarkForm.remark = row.remark || ''; remarkVisible.value = true }
async function submitRemark() {
  submitting.value = true
  try { await updateLicenseRemark(remarkUser.value.userId, { remark: remarkForm.remark }); proxy.$modal.msgSuccess('备注已更新'); remarkVisible.value = false; await loadAccounts() } finally { submitting.value = false }
}
async function openAudit() {
  auditVisible.value = true
  auditQuery.pageNum = 1
  await loadAudit()
}
async function loadAudit() {
  auditLoading.value = true
  try {
    const params = { pageNum: auditQuery.pageNum, pageSize: auditQuery.pageSize, accountKeyword: auditQuery.accountKeyword, operatorKeyword: auditQuery.operatorKeyword, action: auditQuery.action, batchId: auditQuery.batchId, startTime: auditQuery.startTime, endTime: auditQuery.endTime }
    if (/^[1-9]\d*$/.test(auditQuery.userId)) params.userId = auditQuery.userId
    const res = await listLicenseAudit(params)
    auditRows.value = res.data?.rows || []
    auditTotal.value = res.data?.total || 0
  } finally { auditLoading.value = false }
}
function actionText(action) { return ({ grant: '发放', extend: '续期', revoke: '撤销', remark_update: '修改备注' })[action] || action }
function stateSummary(row) {
  const before = row.previousState?.status || 'none'
  const after = row.newState?.status || 'none'
  const plan = row.newState?.planType ? ` · ${row.newState.planType}` : ''
  return `${statusText(before)} → ${statusText(after)}${plan}`
}
function statusText(status) { return ({ active: '有效', expired: '已过期', revoked: '已撤销', none: '未授权' })[status] || '未授权' }
function statusType(status) { return ({ active: 'success', expired: 'warning', revoked: 'danger', none: 'info' })[status] || 'info' }
function remainingText(row) {
  if (!row.authorized) return '-'
  if (!row.expiresAt) return '永久'
  const seconds = Number(row.remainingSeconds || 0)
  if (seconds <= 0) return '已过期'
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  return days ? `${days}天${hours}小时` : `${hours}小时`
}
function formatDate(value) { return String(value).replace('T', ' ').slice(0, 19) }
</script>

<style scoped>
.license-page { max-width: 1440px; }
.page-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.page-heading h2 { margin: 0 0 8px; font-size: 18px; }
.page-heading p { margin: 0; color: var(--el-text-color-secondary); }
.header-actions { display: flex; gap: 8px; }
.table-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 16px; }
.audit-footer { display: flex; justify-content: flex-end; margin-top: 16px; }
@media (max-width: 700px) { .table-footer { align-items: flex-start; flex-direction: column; } }
</style>
