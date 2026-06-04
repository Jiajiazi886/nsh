<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <span>约战数据导入</span>
      </template>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>
              <div class="step-header">
                <el-tag type="primary" size="small">步骤1</el-tag>
                <span class="step-title">上传 CSV 文件</span>
              </div>
            </template>
            <el-upload
              class="upload-area"
              drag
              :auto-upload="false"
              :limit="1"
              :on-change="handleFile"
              :on-exceed="handleExceed"
              :file-list="fileList"
              accept=".csv"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将 CSV 文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  仅支持 .csv 格式文件，单次只能上传一个文件
                </div>
              </template>
            </el-upload>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card shadow="never">
            <template #header>
              <div class="step-header">
                <el-tag type="primary" size="small">步骤2</el-tag>
                <span class="step-title">数据预览</span>
                <span v-if="form.records.length > 0" class="record-count">
                  共 {{ form.records.length }} 条记录
                </span>
              </div>
            </template>
            <div v-if="form.records.length === 0" class="preview-empty">
              <el-empty description="请先上传 CSV 文件" :image-size="80" />
            </div>
            <el-table
              v-else
              :data="form.records"
              border
              stripe
              max-height="400"
              size="small"
            >
              <el-table-column prop="guild_name" label="帮会" width="70" fixed />
              <el-table-column prop="player_name" label="玩家" width="90" fixed />
              <el-table-column prop="player_class" label="职业" width="70" />
              <el-table-column label="击败/清泉" width="90">
                <template #default="scope">
                  {{ scope.row.kills }}/{{ scope.row.qingquan_kills }}
                </template>
              </el-table-column>
              <el-table-column prop="assists" label="助攻" width="60" />
              <el-table-column prop="dmg_to_players" label="对玩家伤害" width="110" />
              <el-table-column prop="dmg_to_buildings" label="对建筑伤害" width="110" />
              <el-table-column prop="healing" label="治疗" width="80" />
              <el-table-column prop="dmg_taken" label="承受伤害" width="100" />
              <el-table-column prop="deaths" label="重伤" width="70" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" style="margin-top: 20px;">
        <template #header>
          <div class="step-header">
            <el-tag type="primary" size="small">步骤3</el-tag>
            <span class="step-title">填写战斗信息并提交</span>
          </div>
        </template>
        <el-form :model="form" label-width="100px" class="battle-form">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="战斗日期">
                <el-input
                  v-model="form.battle_date"
                  placeholder="请输入战斗日期，如：20260510"
                  clearable
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="战斗类型">
                <el-select v-model="form.battle_type" placeholder="请选择战斗类型" style="width: 100%;">
                  <el-option label="约战" value="约战" />
                  <el-option label="帮战" value="帮战" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="战斗结果">
                <el-select v-model="form.battle_result" placeholder="请选择战斗结果" clearable style="width: 100%;">
                  <el-option label="胜利" value="胜利" />
                  <el-option label="失败" value="失败" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="对手帮会">
                <el-input
                  v-model="form.opponent_name"
                  placeholder="请输入对手帮会名称"
                  clearable
                />
              </el-form-item>
            </el-col>
            <el-col :span="16">
              <el-form-item label="备注">
                <el-input
                  v-model="form.remark"
                  type="textarea"
                  :rows="2"
                  placeholder="请输入备注信息（例如对面多少橙武）"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row>
            <el-col :span="24" style="text-align: center;">
              <el-button
                type="primary"
                :disabled="form.records.length === 0"
                :loading="submitLoading"
                @click="handleSubmit"
              >
                提交导入
              </el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-col>
          </el-row>
        </el-form>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { importBattle, checkFilename } from '@/api/guild/battle'

const fileList = ref([])
const submitLoading = ref(false)

const form = reactive({
  battle_date: '',
  battle_type: '约战',
  battle_result: '',
  my_guild_name: '',
  opponent_name: '',
  remark: '',
  csv_filename: '',
  records: []
})

function parseCsvLine(line) {
  const result = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (ch === '"') {
      inQuotes = !inQuotes
    } else if (ch === ',' && !inQuotes) {
      result.push(current)
      current = ''
    } else {
      current += ch
    }
  }
  result.push(current)
  return result
}

function parseCSV(text) {
  const rawLines = text.split('\n')
  const lines = []
  for (const line of rawLines) {
    if (line.trim()) lines.push(line.trim())
  }

  const records = []
  let currentGuild = ''

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    const cols = parseCsvLine(line)

    if (cols.length === 0) continue

    if (cols.length === 2 && /^\d+$/.test(cols[1])) {
      currentGuild = cols[0]
      continue
    }

    if (cols[0] === '玩家名字') {
      continue
    }

    if (cols.length >= 14 && currentGuild) {
      const kqRaw = cols[2].trim()
      let kills = 0, qingquanKills = 0
      if (kqRaw.includes('/')) {
        const parts = kqRaw.split('/')
        kills = parseInt(parts[0]) || 0
        qingquanKills = parseInt(parts[1]) || 0
      }

      records.push({
        guild_name: currentGuild,
        player_name: cols[0],
        player_class: cols[1],
        kills,
        qingquan_kills: qingquanKills,
        assists: parseInt(cols[3]) || 0,
        resources: parseInt(cols[4]) || 0,
        dmg_to_players: parseInt(cols[5]) || 0,
        armor_break_players: parseInt(cols[6]) || 0,
        dmg_to_buildings: parseInt(cols[7]) || 0,
        armor_break_buildings: parseInt(cols[8]) || 0,
        healing: parseInt(cols[9]) || 0,
        dmg_taken: parseInt(cols[10]) || 0,
        deaths: parseInt(cols[11]) || 0,
        revives: parseInt(cols[12]) || 0,
        burn_bones: parseInt(cols[13]) || 0,
      })
    }
  }

  return records
}

function parseFilename(filename) {
  const name = filename.replace(/\.csv$/i, '')
  const parts = name.split('_')

  let myGuild = ''
  let opponent = ''
  if (parts.length > 3) {
    myGuild = parts[parts.length - 2]
    opponent = parts[parts.length - 1]
  } else if (parts.length === 3) {
    myGuild = parts[1]
    opponent = parts[2]
  } else if (parts.length >= 2) {
    opponent = parts[parts.length - 1]
  }

  const date = parts[0] || ''

  return { date, myGuild, opponent }
}

async function handleFile(file) {
  const filename = file.name || ''
  const res = await checkFilename(filename)
  if (res.data.exists) {
    ElMessage.warning('系统已有数据，请勿重复导入')
    fileList.value = []
    handleReset()
    return false
  }

  const reader = new FileReader()

  form.csv_filename = filename

  reader.onload = (e) => {
    const text = e.target.result
    const records = parseCSV(text)
    form.records = records

    const { date, myGuild, opponent } = parseFilename(filename)
    if (date && !form.battle_date) {
      form.battle_date = date
    }
    if (myGuild && !form.my_guild_name) {
      form.my_guild_name = myGuild
    }
    if (opponent && !form.opponent_name) {
      form.opponent_name = opponent
    }

    if (records.length > 0) {
      ElMessage.success(`成功解析 ${records.length} 条记录`)
    } else {
      ElMessage.warning('未解析到有效数据，请检查 CSV 文件格式')
    }
  }
  reader.readAsText(file.raw || file)
  return false
}

function handleExceed() {
  ElMessage.warning('每次只能上传一个文件，请先移除已有文件')
}

function handleSubmit() {
  if (form.records.length === 0) {
    ElMessage.warning('请先上传 CSV 文件')
    return
  }
  submitLoading.value = true
  const payload = {
    battle_date: form.battle_date,
    battle_type: form.battle_type,
    battle_result: form.battle_result,
    my_guild_name: form.my_guild_name,
    opponent_name: form.opponent_name,
    remark: form.remark,
    csv_filename: form.csv_filename,
    records: form.records
  }
  importBattle(payload).then(() => {
    ElMessage.success('导入成功')
    handleReset()
  }).catch((err) => {
    ElMessage.error(err.message || '导入失败，请稍后重试')
  }).finally(() => {
    submitLoading.value = false
  })
}

function handleReset() {
  form.battle_date = ''
  form.battle_type = '约战'
  form.battle_result = ''
  form.my_guild_name = ''
  form.opponent_name = ''
  form.csv_filename = ''
  form.remark = ''
  form.records = []
  fileList.value = []
}
</script>

<style scoped>
.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-title {
  font-weight: 500;
  font-size: 14px;
}

.record-count {
  margin-left: auto;
  font-size: 13px;
  color: #909399;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
}

.preview-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.battle-form {
  max-width: 100%;
}
</style>