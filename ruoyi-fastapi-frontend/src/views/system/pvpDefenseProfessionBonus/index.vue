<template>
  <div class="app-container profession-bonus-page">
    <div class="page-heading">
      <div>
        <h2>职业加成设置</h2>
        <p>设置坦度计算器中各职业对内功新增防御与气血的默认加成，用户可在个人设置中覆盖。</p>
      </div>
      <el-button :icon="Refresh" @click="loadRows">刷新</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" row-key="professionId">
      <el-table-column prop="professionName" label="职业" min-width="160" />
      <el-table-column label="内功防御加成" min-width="220">
        <template #default="{ row }">
          <el-input-number v-model="row.defenseBonusPct" :min="0" :max="1000" :step="1" :precision="2" controls-position="right">
            <template #suffix>%</template>
          </el-input-number>
        </template>
      </el-table-column>
      <el-table-column label="内功气血加成" min-width="220">
        <template #default="{ row }">
          <el-input-number v-model="row.hpBonusPct" :min="0" :max="1000" :step="1" :precision="2" controls-position="right">
            <template #suffix>%</template>
          </el-input-number>
        </template>
      </el-table-column>
      <el-table-column prop="updateBy" label="最后修改人" width="150" />
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button
            v-hasPermi="['system:pvp-defense-profession-bonus:edit']"
            link
            type="primary"
            :loading="savingId === row.professionId"
            @click="saveRow(row)"
          >保存</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup name="SystemPvpDefenseProfessionBonus">
import { Refresh } from '@element-plus/icons-vue'
import {
  listPvpDefenseProfessionBonuses,
  updatePvpDefenseProfessionBonus
} from '@/api/system/pvpDefenseProfessionBonus'

const { proxy } = getCurrentInstance()
const loading = ref(false)
const savingId = ref(0)
const rows = ref([])

onMounted(loadRows)

async function loadRows() {
  loading.value = true
  try {
    const response = await listPvpDefenseProfessionBonuses()
    rows.value = response.data || []
  } finally {
    loading.value = false
  }
}

async function saveRow(row) {
  savingId.value = row.professionId
  try {
    await updatePvpDefenseProfessionBonus(row.professionId, {
      defenseBonusPct: Number(row.defenseBonusPct || 0),
      hpBonusPct: Number(row.hpBonusPct || 0)
    })
    proxy.$modal.msgSuccess(`${row.professionName}职业加成已保存`)
    await loadRows()
  } finally {
    savingId.value = 0
  }
}
</script>

<style scoped>
.profession-bonus-page { display: grid; gap: 16px; }
.page-heading { display: flex; align-items: end; justify-content: space-between; gap: 20px; }
.page-heading h2 { margin: 0; letter-spacing: 0; }
.page-heading p { margin: 8px 0 0; color: #69788b; }
@media (max-width: 640px) { .page-heading { align-items: stretch; flex-direction: column; } }
</style>
