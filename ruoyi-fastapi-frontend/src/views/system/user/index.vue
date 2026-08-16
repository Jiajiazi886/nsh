<template>
  <div class="app-container">
    <el-row :gutter="20">
      <el-col>
        <el-form
          :model="queryParams"
          ref="queryRef"
          :inline="true"
          v-show="showSearch"
          label-width="68px"
        >
          <el-form-item label="用户名称" prop="userName">
            <el-input
              v-model="queryParams.userName"
              placeholder="请输入用户名称"
              clearable
              style="width: 240px"
              @keyup.enter="handleQuery"
            />
          </el-form-item>
          <el-form-item label="角色" prop="roleId">
            <el-select
              v-model="queryParams.roleId"
              placeholder="请选择角色"
              clearable
              filterable
              style="width: 240px"
            >
              <el-option
                v-for="item in roleOptions"
                :key="item.roleId"
                :label="`${item.roleName}（${item.roleKey}）`"
                :value="item.roleId"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态" prop="status">
            <el-select
              v-model="queryParams.status"
              placeholder="用户状态"
              clearable
              style="width: 240px"
            >
              <el-option
                v-for="dict in sys_normal_disable"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="创建时间" style="width: 308px">
            <el-date-picker
              v-model="dateRange"
              value-format="YYYY-MM-DD"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            ></el-date-picker>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Search" @click="handleQuery"
              >搜索</el-button
            >
            <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          </el-form-item>
        </el-form>

        <el-row :gutter="10" class="mb8">
          <el-col :span="1.5">
            <el-button
              type="primary"
              plain
              icon="Plus"
              @click="handleAdd"
              v-hasPermi="['system:user:add']"
              >新增</el-button
            >
          </el-col>
          <el-col :span="1.5">
            <el-button
              type="success"
              plain
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['system:user:edit']"
              >修改</el-button
            >
          </el-col>
          <el-col :span="1.5">
            <el-button
              type="danger"
              plain
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['system:user:remove']"
              >删除</el-button
            >
          </el-col>
          <el-col :span="1.5">
            <el-button
              type="info"
              plain
              icon="Upload"
              @click="handleImport"
              v-hasPermi="['system:user:import']"
              >导入</el-button
            >
          </el-col>
          <el-col :span="1.5">
            <el-button
              type="warning"
              plain
              icon="Download"
              @click="handleExport"
              v-hasPermi="['system:user:export']"
              >导出</el-button
            >
          </el-col>
          <el-col :span="1.5">
            <div class="cleanup-rule-toggle" v-hasPermi="['system:user:edit']">
              <span>清理未登录注册用户</span>
              <el-switch
                v-model="registerCleanupEnabled"
                :loading="registerCleanupLoading"
                active-text="开"
                inactive-text="关"
                @change="handleRegisterCleanupChange"
              />
            </div>
          </el-col>
          <el-col v-if="canManageVip" :span="1.5">
            <el-button
              type="primary"
              plain
              icon="Setting"
              @click="openDefaultAiDialog"
              v-hasPermi="['system:user:ai:edit']"
            >新用户设置</el-button>
          </el-col>
          <el-col v-if="canManageVip" :span="1.5">
            <el-button
              type="success"
              plain
              icon="PictureRounded"
              @click="openVipAiGrantDialog"
              v-hasPermi="['system:user:ai:edit']"
            >VIP识图次数设置</el-button>
          </el-col>
          <el-col v-if="canManageVip" :span="1.5">
            <el-button
              type="warning"
              plain
              icon="Medal"
              :disabled="multiple"
              @click="openBatchVipDialog"
              v-hasPermi="['system:user:vip:edit']"
            >批量设置 VIP</el-button>
          </el-col>
          <el-col v-if="canManageVip" :span="1.5">
            <el-button
              type="primary"
              plain
              icon="SetUp"
              :disabled="multiple"
              @click="openBatchLimitDialog"
              v-hasPermi="['system:user:edit']"
            >批量内功上限</el-button>
          </el-col>
          <right-toolbar
            v-model:showSearch="showSearch"
            @queryTable="getList"
            :columns="toolbarColumns"
          ></right-toolbar>
        </el-row>

        <el-table
          v-loading="loading"
          :data="userList"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="50" align="center" />
          <el-table-column
            label="用户编号"
            align="center"
            key="userId"
            prop="userId"
            v-if="columns.userId.visible"
          />
          <el-table-column
            label="用户名称"
            align="center"
            key="userName"
            prop="userName"
            v-if="columns.userName.visible"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="用户昵称"
            align="center"
            key="nickName"
            prop="nickName"
            v-if="columns.nickName.visible"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="角色"
            align="center"
            key="role"
            v-if="columns.role.visible"
            min-width="180"
          >
            <template #default="scope">
              <div class="role-tags">
                <el-tag
                  v-for="role in scope.row.role || []"
                  :key="role.roleId"
                  type="info"
                  effect="plain"
                >
                  {{ role.roleName }}（{{ role.roleKey }}）
                </el-tag>
                <span v-if="!scope.row.role || scope.row.role.length === 0">--</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="VIP"
            align="center"
            key="isVip"
            v-if="canManageVip && columns.isVip.visible"
            min-width="150"
          >
            <template #default="scope">
              <div v-if="isGuildMemberRow(scope.row)" class="vip-cell">
                <el-tag :type="getVipTagType(scope.row)" effect="light">
                  {{ getVipLabel(scope.row) }}
                </el-tag>
                <small v-if="scope.row.vipExpireTime">{{ parseTime(scope.row.vipExpireTime) }}</small>
                <el-button
                  v-if="scope.row.userId !== 1"
                  link
                  type="primary"
                  @click="openVipDialog(scope.row)"
                  v-hasPermi="['system:user:vip:edit']"
                >设置</el-button>
              </div>
              <span v-else>--</span>
            </template>
          </el-table-column>
          <el-table-column
            label="赞助"
            align="center"
            key="sponsorEnabled"
            v-if="canManageVip && columns.sponsorEnabled.visible"
            min-width="130"
          >
            <template #default="scope">
              <el-switch
                v-if="isGuildManagerRow(scope.row)"
                v-model="scope.row.sponsorEnabled"
                active-value="1"
                inactive-value="0"
                active-text="开"
                inactive-text="关"
                :disabled="scope.row.userId === 1 || scope.row._sponsorSaving"
                @change="(value) => handleSponsorChange(scope.row, value)"
                v-hasPermi="['system:user:sponsor:edit']"
              />
              <span v-else>--</span>
            </template>
          </el-table-column>
          <el-table-column
            label="普通AI识图次数"
            align="center"
            key="aiImageRecognitionCount"
            v-if="canManageVip && columns.aiImageRecognitionCount.visible"
            min-width="140"
          >
            <template #default="scope">
              <el-input-number
                v-if="isGuildMemberRow(scope.row)"
                v-model="scope.row.aiImageRecognitionCount"
                :min="0"
                :precision="0"
                :step="1"
                controls-position="right"
                size="small"
                class="inline-limit-input"
                :disabled="scope.row.userId === 1 || scope.row._aiCountSaving"
                @change="(value, oldValue) => handleInlineAiCountChange(scope.row, value, oldValue)"
                v-hasPermi="['system:user:ai:edit']"
              />
              <span v-else>--</span>
            </template>
          </el-table-column>
          <el-table-column
            label="VIP AI识图次数"
            align="center"
            key="vipAiImageRecognitionCount"
            v-if="canManageVip && columns.vipAiImageRecognitionCount.visible"
            min-width="145"
          >
            <template #default="scope">
              <el-input-number
                v-if="isGuildMemberRow(scope.row)"
                v-model="scope.row.vipAiImageRecognitionCount"
                :min="0"
                :precision="0"
                :step="1"
                controls-position="right"
                size="small"
                class="inline-limit-input"
                :disabled="scope.row.userId === 1 || scope.row._vipAiCountSaving"
                @change="(value, oldValue) => handleInlineVipAiCountChange(scope.row, value, oldValue)"
                v-hasPermi="['system:user:ai:edit']"
              />
              <span v-else>--</span>
            </template>
          </el-table-column>
          <el-table-column
            label="最大内功数"
            align="center"
            key="maxInternalPowerCount"
            v-if="canManageVip && columns.maxInternalPowerCount.visible"
            min-width="130"
          >
            <template #default="scope">
              <div class="limit-cell">
                <el-input-number
                  v-model="scope.row.maxInternalPowerCount"
                  :min="20"
                  :precision="0"
                  :step="1"
                  controls-position="right"
                  size="small"
                  class="inline-limit-input"
                  :disabled="scope.row.userId === 1 || scope.row._limitSaving"
                  @change="(value, oldValue) => handleInlineLimitChange(scope.row, value, oldValue)"
                  v-hasPermi="['system:user:edit']"
                />
                <small v-if="scope.row.effectiveInternalPowerLimit == null">
                  {{ scope.row.isVipEffective ? 'VIP不限' : '管理员不限' }}
                </small>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="状态"
            align="center"
            key="status"
            v-if="columns.status.visible"
          >
            <template #default="scope">
              <el-switch
                v-model="scope.row.status"
                active-value="0"
                inactive-value="1"
                @change="handleStatusChange(scope.row)"
              ></el-switch>
            </template>
          </el-table-column>
          <el-table-column
            label="创建时间"
            align="center"
            prop="createTime"
            v-if="columns.createTime.visible"
            width="160"
          >
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            align="center"
            width="150"
            class-name="small-padding fixed-width"
          >
            <template #default="scope">
              <el-tooltip
                content="修改"
                placement="top"
                v-if="scope.row.userId !== 1"
              >
                <el-button
                  link
                  type="primary"
                  icon="Edit"
                  @click="handleUpdate(scope.row)"
                  v-hasPermi="['system:user:edit']"
                ></el-button>
              </el-tooltip>
              <el-tooltip
                content="删除"
                placement="top"
                v-if="scope.row.userId !== 1"
              >
                <el-button
                  link
                  type="primary"
                  icon="Delete"
                  @click="handleDelete(scope.row)"
                  v-hasPermi="['system:user:remove']"
                ></el-button>
              </el-tooltip>
              <el-tooltip
                content="重置密码"
                placement="top"
                v-if="scope.row.userId !== 1"
              >
                <el-button
                  link
                  type="primary"
                  icon="Key"
                  @click="handleResetPwd(scope.row)"
                  v-hasPermi="['system:user:resetPwd']"
                ></el-button>
              </el-tooltip>
              <el-tooltip
                content="分配角色"
                placement="top"
                v-if="scope.row.userId !== 1"
              >
                <el-button
                  link
                  type="primary"
                  icon="CircleCheck"
                  @click="handleAuthRole(scope.row)"
                  v-hasPermi="['system:user:edit']"
                ></el-button>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
        <pagination
          v-show="total > 0"
          :total="total"
          v-model:page="queryParams.pageNum"
          v-model:limit="queryParams.pageSize"
          @pagination="getList"
        />
      </el-col>
    </el-row>

    <el-dialog :title="title" v-model="open" width="600px" append-to-body>
      <el-form :model="form" :rules="rules" ref="userRef" label-width="80px">
        <el-row>
          <el-col :span="12">
            <el-form-item label="用户昵称" prop="nickName">
              <el-input
                v-model="form.nickName"
                placeholder="请输入用户昵称"
                maxlength="30"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="form.email"
                placeholder="请输入邮箱"
                maxlength="50"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              label="用户名称"
              prop="userName"
            >
              <el-input
                v-model="form.userName"
                placeholder="请输入用户名称"
                maxlength="30"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item
              v-if="form.userId == undefined"
              label="用户密码"
              prop="password"
            >
              <el-input
                v-model="form.password"
                placeholder="请输入用户密码"
                type="password"
                maxlength="20"
                show-password
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色">
              <el-select v-model="form.roleIds" multiple placeholder="请选择">
                <el-option
                  v-for="item in roleOptions"
                  :key="item.roleId"
                  :label="item.roleName"
                  :value="item.roleId"
                  :disabled="item.status == 1"
                ></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="用户性别">
              <el-select v-model="form.sex" placeholder="请选择">
                <el-option
                  v-for="dict in sys_user_sex"
                  :key="dict.value"
                  :label="dict.label"
                  :value="dict.value"
                ></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-radio-group v-model="form.status">
                <el-radio
                  v-for="dict in sys_normal_disable"
                  :key="dict.value"
                  :value="dict.value"
                  >{{ dict.label }}</el-radio
                >
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row v-if="canManageVip">
          <el-col :span="8">
            <el-form-item label="普通AI识图次数">
              <el-input-number
                v-model="form.aiImageRecognitionCount"
                :min="0"
                :precision="0"
                controls-position="right"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="VIP AI识图次数">
              <el-input-number
                v-model="form.vipAiImageRecognitionCount"
                :min="0"
                :precision="0"
                controls-position="right"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大内功数">
              <el-input-number
                v-model="form.maxInternalPowerCount"
                :min="20"
                :precision="0"
                controls-position="right"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input
                v-model="form.remark"
                type="textarea"
                placeholder="请输入内容"
              ></el-input>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="vipDialog.open" title="设置 VIP 授权" width="440px" append-to-body>
      <el-form label-width="96px">
        <el-form-item label="用户">
          <strong>{{ vipDialog.row?.userName }}</strong>
        </el-form-item>
        <el-form-item label="授权方式">
          <el-radio-group v-model="vipDialog.mode" @change="handleVipModeChange">
            <el-radio-button label="week">一周</el-radio-button>
            <el-radio-button label="month">一个月</el-radio-button>
            <el-radio-button label="quarter">三个月</el-radio-button>
            <el-radio-button label="custom">自定义</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="到期时间">
          <el-date-picker
            v-model="vipDialog.expireTime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="请选择到期时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button v-if="vipDialog.row?.isVip === '1'" type="danger" plain @click="cancelVip">取消 VIP</el-button>
          <el-button @click="vipDialog.open = false">取 消</el-button>
          <el-button type="primary" @click="submitVipDialog">保存 VIP</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="defaultAiDialog.open" title="新用户设置" width="420px" append-to-body>
      <el-form label-width="132px">
        <el-form-item label="普通AI识图次数">
          <el-input-number
            v-model="defaultAiDialog.aiImageRecognitionCount"
            :min="0"
            :precision="0"
            controls-position="right"
            style="width: 180px"
          />
        </el-form-item>
        <el-alert
          title="保存后会作为未来新用户默认次数，并同步覆盖现有老用户。"
          type="warning"
          :closable="false"
          show-icon
        />
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="defaultAiDialog.open = false">取 消</el-button>
          <el-button type="primary" :loading="defaultAiDialog.loading" @click="submitDefaultAiDialog">确 定</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="vipAiGrantDialog.open" title="VIP识图次数设置" width="440px" append-to-body>
      <el-form label-width="158px">
        <el-form-item label="成为VIP赠送次数">
          <el-input-number
            v-model="vipAiGrantDialog.vipAiImageRecognitionGrantCount"
            :min="0"
            :precision="0"
            controls-position="right"
            style="width: 180px"
          />
        </el-form-item>
        <el-alert
          title="用户从非VIP变为有效VIP时自动追加一次。续期不会重复赠送；VIP取消或到期后，剩余次数不会清零。"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="vipAiGrantDialog.open = false">取 消</el-button>
          <el-button type="primary" :loading="vipAiGrantDialog.loading" @click="submitVipAiGrantDialog">确 定</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="batchVipDialog.open" title="批量设置 VIP" width="480px" append-to-body>
      <el-form label-width="112px">
        <el-form-item label="目标用户">
          <span>{{ ids.length }} 个用户</span>
        </el-form-item>
        <el-form-item label="操作">
          <el-radio-group v-model="batchVipDialog.isVip" @change="handleBatchVipStatusChange">
            <el-radio-button label="1">开通 VIP</el-radio-button>
            <el-radio-button label="0">取消 VIP</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <template v-if="batchVipDialog.isVip === '1'">
          <el-form-item label="授权方式">
            <el-radio-group v-model="batchVipDialog.mode" @change="handleBatchVipModeChange">
              <el-radio-button label="week">一周</el-radio-button>
              <el-radio-button label="month">一个月</el-radio-button>
              <el-radio-button label="quarter">三个月</el-radio-button>
              <el-radio-button label="custom">自定义</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="到期时间">
            <el-date-picker
              v-model="batchVipDialog.expireTime"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="请选择到期时间"
              style="width: 100%"
            />
          </el-form-item>
        </template>
        <el-alert
          v-if="batchVipDialog.isVip === '1'"
          title="仅新成为VIP的用户会自动获得系统设置的VIP识图次数，已有余额会继续保留。"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="batchVipDialog.open = false">取 消</el-button>
          <el-button type="primary" :loading="batchVipDialog.loading" @click="submitBatchVipDialog">确 定</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="limitDialog.open" :title="limitDialog.batch ? '批量设置最大内功数' : '设置最大内功数'" width="420px" append-to-body>
      <el-form label-width="108px">
        <el-form-item label="目标用户">
          <span>{{ limitDialog.batch ? `${ids.length} 个用户` : limitDialog.row?.userName }}</span>
        </el-form-item>
        <el-form-item label="最大内功数">
          <el-input-number
            v-model="limitDialog.maxInternalPowerCount"
            :min="20"
            :precision="0"
            controls-position="right"
            style="width: 180px"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="limitDialog.open = false">取 消</el-button>
          <el-button type="primary" @click="submitLimitDialog">确 定</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      :title="upload.title"
      v-model="upload.open"
      width="400px"
      append-to-body
    >
      <el-upload
        ref="uploadRef"
        :limit="1"
        accept=".xlsx, .xls"
        :headers="upload.headers"
        :action="upload.url + '?updateSupport=' + upload.updateSupport"
        :disabled="upload.isUploading"
        :on-progress="handleFileUploadProgress"
        :on-success="handleFileSuccess"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :auto-upload="false"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip text-center">
            <div class="el-upload__tip">
              <el-checkbox
                v-model="upload.updateSupport"
              />是否更新已经存在的用户数据
            </div>
            <span>仅允许导入xls、xlsx格式文件。</span>
            <el-link
              type="primary"
              :underline="false"
              style="font-size: 12px; vertical-align: baseline"
              @click="importTemplate"
              >下载模板</el-link
            >
          </div>
        </template>
      </el-upload>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitFileForm">确 定</el-button>
          <el-button @click="upload.open = false">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="User">
import { getToken } from "@/utils/auth";
import { parseTime } from "@/utils/ruoyi";
import useUserStore from "@/store/modules/user";
import {
  batchInternalPowerLimit,
  batchUserVip,
  changeAiRecognitionCount,
  changeInternalPowerLimit,
  changeUserSponsor,
  changeUserVip,
  changeUserStatus,
  changeVipAiRecognitionCount,
  listUser,
  resetUserPwd,
  delUser,
  getUser,
  updateUser,
  addUser,
  getDefaultAiRecognitionCount,
  getVipAiRecognitionGrantCount,
  getRegisterCleanupRule,
  updateDefaultAiRecognitionCount,
  updateVipAiRecognitionGrantCount,
  updateRegisterCleanupRule,
} from "@/api/system/user";

const router = useRouter();
const userStore = useUserStore();
const { proxy } = getCurrentInstance();
const { sys_normal_disable, sys_user_sex } = proxy.useDict(
  "sys_normal_disable",
  "sys_user_sex"
);

const userList = ref([]);
const open = ref(false);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const total = ref(0);
const title = ref("");
const dateRange = ref([]);
const initPassword = ref(undefined);
const roleOptions = ref([]);
const registerCleanupEnabled = ref(false);
const registerCleanupLoading = ref(false);
const canManageVip = computed(() => (userStore.roles || []).includes("admin"));
const vipDialog = reactive({
  open: false,
  row: null,
  mode: "month",
  expireTime: "",
});
const defaultAiDialog = reactive({
  open: false,
  loading: false,
  aiImageRecognitionCount: 0,
});
const vipAiGrantDialog = reactive({
  open: false,
  loading: false,
  vipAiImageRecognitionGrantCount: 0,
});
const batchVipDialog = reactive({
  open: false,
  loading: false,
  isVip: "1",
  mode: "month",
  expireTime: "",
});
const limitDialog = reactive({
  open: false,
  batch: false,
  row: null,
  maxInternalPowerCount: 20,
});
const upload = reactive({
  open: false,
  title: "",
  isUploading: false,
  updateSupport: 0,
  headers: { Authorization: "Bearer " + getToken() },
  url: import.meta.env.VITE_APP_BASE_API + "/system/user/importData",
});

const columns = ref({
  userId: { label: "用户编号", visible: true },
  userName: { label: "用户名称", visible: true },
  nickName: { label: "用户昵称", visible: true },
  role: { label: "角色", visible: true },
  isVip: { label: "VIP", visible: true },
  sponsorEnabled: { label: "赞助", visible: true },
  aiImageRecognitionCount: { label: "普通AI识图次数", visible: true },
  vipAiImageRecognitionCount: { label: "VIP AI识图次数", visible: true },
  maxInternalPowerCount: { label: "最大内功数", visible: true },
  status: { label: "状态", visible: true },
  createTime: { label: "创建时间", visible: true },
});
const toolbarColumns = computed(() => {
  if (canManageVip.value) {
    return columns.value;
  }
  return Object.fromEntries(Object.entries(columns.value).filter(([key]) => !["isVip", "sponsorEnabled", "aiImageRecognitionCount", "vipAiImageRecognitionCount", "maxInternalPowerCount"].includes(key)));
});

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    userName: undefined,
    roleId: undefined,
    status: undefined,
  },
  rules: {
    userName: [
      { required: true, message: "用户名称不能为空", trigger: "blur" },
      {
        min: 2,
        max: 20,
        message: "用户名称长度必须介于 2 和 20 之间",
        trigger: "blur",
      },
    ],
    nickName: [
      { required: true, message: "用户昵称不能为空", trigger: "blur" },
    ],
    password: [
      { required: true, message: "用户密码不能为空", trigger: "blur" },
      {
        min: 5,
        max: 20,
        message: "用户密码长度必须介于 5 和 20 之间",
        trigger: "blur",
      },
      {
        pattern: /^[^<>"'|\\]+$/,
        message: "不能包含非法字符：< > \" ' \\\ |",
        trigger: "blur",
      },
    ],
    email: [
      {
        type: "email",
        message: "请输入正确的邮箱地址",
        trigger: ["blur", "change"],
      },
    ],
  },
});

const { queryParams, form, rules } = toRefs(data);

function getList() {
  loading.value = true;
  listUser(proxy.addDateRange(queryParams.value, dateRange.value)).then(
    (res) => {
      loading.value = false;
      userList.value = (res.rows || []).map((item) => ({
        ...item,
        isVip: item.isVip || "0",
        isVipEffective: !!item.isVipEffective,
        sponsorEnabled: item.sponsorEnabled || "0",
        sponsoredVip: item.sponsoredVip || "0",
        sponsoredByUserId: item.sponsoredByUserId,
        effectiveVipType: item.effectiveVipType || "none",
        aiImageRecognitionCount: Number(item.aiImageRecognitionCount || 0),
        vipAiImageRecognitionCount: Number(item.vipAiImageRecognitionCount || 0),
        maxInternalPowerCount: item.maxInternalPowerCount || 20,
        effectiveInternalPowerLimit: item.effectiveInternalPowerLimit,
      }));
      total.value = res.total;
    }
  );
}
function handleQuery() {
  queryParams.value.pageNum = 1;
  getList();
}
watch(
  () => queryParams.value.roleId,
  () => {
    handleQuery();
  }
);
function resetQuery() {
  dateRange.value = [];
  proxy.resetForm("queryRef");
  handleQuery();
}
function fetchRoleOptions() {
  getUser().then((response) => {
    roleOptions.value = response.roles || [];
  });
}
function fetchRegisterCleanupRule() {
  getRegisterCleanupRule().then((response) => {
    registerCleanupEnabled.value = !!response.data?.enabled;
  });
}
function handleRegisterCleanupChange(enabled) {
  registerCleanupLoading.value = true;
  updateRegisterCleanupRule({ enabled })
    .then(() => {
      proxy.$modal.msgSuccess(enabled ? "已开启自动清理规则" : "已关闭自动清理规则");
    })
    .catch(() => {
      registerCleanupEnabled.value = !enabled;
    })
    .finally(() => {
      registerCleanupLoading.value = false;
    });
}
function handleDelete(row) {
  const userIds = row.userId || ids.value;
  proxy.$modal
    .confirm('是否确认删除用户编号为"' + userIds + '"的数据项？')
    .then(function () {
      return delUser(userIds);
    })
    .then(() => {
      getList();
      proxy.$modal.msgSuccess("删除成功");
    })
    .catch(() => {});
}
function handleExport() {
  proxy.download(
    "system/user/export",
    {
      ...queryParams.value,
    },
    `user_${new Date().getTime()}.xlsx`
  );
}
function handleStatusChange(row) {
  let text = row.status === "0" ? "启用" : "停用";
  proxy.$modal
    .confirm('确认要"' + text + '""' + row.userName + '"用户吗?')
    .then(function () {
      return changeUserStatus(row.userId, row.status);
    })
    .then(() => {
      proxy.$modal.msgSuccess(text + "成功");
    })
    .catch(function () {
      row.status = row.status === "0" ? "1" : "0";
    });
}
function getRowRoleKeys(row) {
  return (row.role || []).map((role) => role?.roleKey).filter(Boolean);
}
function isGuildMemberRow(row) {
  return getRowRoleKeys(row).includes("user");
}
function isGuildManagerRow(row) {
  return getRowRoleKeys(row).includes("common");
}
function getVipLabel(row) {
  if (row.effectiveVipType === "sponsored" || row.sponsoredVip === "1") return "赞助VIP";
  if (row.isVip === "1" && row.isVipEffective) return "VIP有效";
  if (row.isVip === "1" && row.vipExpireTime) return "已过期";
  return "普通";
}
function getVipTagType(row) {
  if (row.effectiveVipType === "sponsored" || row.sponsoredVip === "1") return "success";
  if (row.isVip === "1" && row.isVipEffective) return "warning";
  if (row.isVip === "1" && row.vipExpireTime) return "danger";
  return "info";
}
function getFutureTime(mode) {
  const date = new Date();
  if (mode === "week") date.setDate(date.getDate() + 7);
  if (mode === "month") date.setMonth(date.getMonth() + 1);
  if (mode === "quarter") date.setMonth(date.getMonth() + 3);
  return parseTime(date, "{y}-{m}-{d} {h}:{i}:{s}");
}
function openVipDialog(row) {
  vipDialog.row = row;
  vipDialog.mode = "month";
  vipDialog.expireTime = row.vipExpireTime && row.isVipEffective ? row.vipExpireTime : getFutureTime("month");
  vipDialog.open = true;
}
function handleVipModeChange(mode) {
  if (mode !== "custom") {
    vipDialog.expireTime = getFutureTime(mode);
  }
}
function submitVipDialog() {
  if (!vipDialog.row || !vipDialog.expireTime) {
    proxy.$modal.msgError("请选择VIP到期时间");
    return;
  }
  changeUserVip(vipDialog.row.userId, "1", vipDialog.expireTime).then((response) => {
    proxy.$modal.msgSuccess(response.msg || "VIP授权已更新");
    vipDialog.open = false;
    getList();
  });
}
function cancelVip() {
  if (!vipDialog.row) return;
  changeUserVip(vipDialog.row.userId, "0", null).then(() => {
    proxy.$modal.msgSuccess("已取消VIP");
    vipDialog.open = false;
    getList();
  });
}
function openDefaultAiDialog() {
  defaultAiDialog.loading = true;
  defaultAiDialog.open = true;
  getDefaultAiRecognitionCount()
    .then((response) => {
      defaultAiDialog.aiImageRecognitionCount = Number(response.data?.aiImageRecognitionCount || 0);
    })
    .finally(() => {
      defaultAiDialog.loading = false;
    });
}
function submitDefaultAiDialog() {
  const count = Math.max(0, Number(defaultAiDialog.aiImageRecognitionCount || 0));
  defaultAiDialog.loading = true;
  updateDefaultAiRecognitionCount(count)
    .then((response) => {
      proxy.$modal.msgSuccess(response.msg || "已设置默认次数并同步老用户");
      defaultAiDialog.open = false;
      getList();
    })
    .finally(() => {
      defaultAiDialog.loading = false;
    });
}
function openVipAiGrantDialog() {
  vipAiGrantDialog.loading = true;
  vipAiGrantDialog.open = true;
  getVipAiRecognitionGrantCount()
    .then((response) => {
      vipAiGrantDialog.vipAiImageRecognitionGrantCount = Number(
        response.data?.vipAiImageRecognitionGrantCount || 0
      );
    })
    .finally(() => {
      vipAiGrantDialog.loading = false;
    });
}
function submitVipAiGrantDialog() {
  const count = Math.max(0, Number(vipAiGrantDialog.vipAiImageRecognitionGrantCount || 0));
  vipAiGrantDialog.loading = true;
  updateVipAiRecognitionGrantCount(count)
    .then((response) => {
      proxy.$modal.msgSuccess(response.msg || "VIP开通赠送识图次数已保存");
      vipAiGrantDialog.open = false;
    })
    .finally(() => {
      vipAiGrantDialog.loading = false;
    });
}
function openBatchVipDialog() {
  batchVipDialog.open = true;
  batchVipDialog.isVip = "1";
  batchVipDialog.mode = "month";
  batchVipDialog.expireTime = getFutureTime("month");
}
function handleBatchVipModeChange(mode) {
  if (mode !== "custom") {
    batchVipDialog.expireTime = getFutureTime(mode);
  }
}
function handleBatchVipStatusChange(value) {
  if (value === "1" && !batchVipDialog.expireTime) {
    batchVipDialog.expireTime = getFutureTime(batchVipDialog.mode || "month");
  }
}
function submitBatchVipDialog() {
  if (!ids.value.length) {
    proxy.$modal.msgError("请选择需要修改的用户");
    return;
  }
  if (batchVipDialog.isVip === "1" && !batchVipDialog.expireTime) {
    proxy.$modal.msgError("请选择VIP到期时间");
    return;
  }
  batchVipDialog.loading = true;
  batchUserVip(
    ids.value,
    batchVipDialog.isVip,
    batchVipDialog.isVip === "1" ? batchVipDialog.expireTime : null
  )
    .then((response) => {
      proxy.$modal.msgSuccess(response.msg || "批量VIP设置已更新");
      batchVipDialog.open = false;
      getList();
    })
    .finally(() => {
      batchVipDialog.loading = false;
    });
}
function handleSponsorChange(row, value) {
  const previousValue = value === "1" ? "0" : "1";
  row._sponsorSaving = true;
  changeUserSponsor(row.userId, value)
    .then(() => {
      proxy.$modal.msgSuccess(value === "1" ? "赞助已开启" : "赞助已关闭");
      getList();
    })
    .catch(() => {
      row.sponsorEnabled = previousValue;
    })
    .finally(() => {
      row._sponsorSaving = false;
    });
}
function handleInlineAiCountChange(row, value, oldValue) {
  const nextValue = Math.max(0, Number(value || 0));
  const previousValue = Math.max(0, Number(oldValue ?? row.aiImageRecognitionCount ?? 0));
  if (nextValue === previousValue) {
    row.aiImageRecognitionCount = nextValue;
    return;
  }
  row.aiImageRecognitionCount = nextValue;
  row._aiCountSaving = true;
  changeAiRecognitionCount(row.userId, nextValue)
    .then(() => {
      proxy.$modal.msgSuccess("AI识图次数已更新");
    })
    .catch(() => {
      row.aiImageRecognitionCount = previousValue;
    })
    .finally(() => {
      row._aiCountSaving = false;
    });
}
function handleInlineVipAiCountChange(row, value, oldValue) {
  const nextValue = Math.max(0, Number(value || 0));
  const previousValue = Math.max(0, Number(oldValue ?? row.vipAiImageRecognitionCount ?? 0));
  if (nextValue === previousValue) {
    row.vipAiImageRecognitionCount = nextValue;
    return;
  }
  row.vipAiImageRecognitionCount = nextValue;
  row._vipAiCountSaving = true;
  changeVipAiRecognitionCount(row.userId, nextValue)
    .then(() => {
      proxy.$modal.msgSuccess("VIP AI识图次数已更新");
    })
    .catch(() => {
      row.vipAiImageRecognitionCount = previousValue;
    })
    .finally(() => {
      row._vipAiCountSaving = false;
    });
}
function openBatchLimitDialog() {
  limitDialog.open = true;
  limitDialog.batch = true;
  limitDialog.row = null;
  limitDialog.maxInternalPowerCount = 20;
}
function handleInlineLimitChange(row, value, oldValue) {
  const nextValue = Math.max(20, Number(value || 20));
  const previousValue = Math.max(20, Number(oldValue || row.maxInternalPowerCount || 20));
  if (nextValue === previousValue) {
    row.maxInternalPowerCount = nextValue;
    return;
  }
  row.maxInternalPowerCount = nextValue;
  row._limitSaving = true;
  changeInternalPowerLimit(row.userId, nextValue)
    .then(() => {
      proxy.$modal.msgSuccess("最大内功数已更新");
      row.effectiveInternalPowerLimit = row.effectiveInternalPowerLimit == null ? null : nextValue;
    })
    .catch(() => {
      row.maxInternalPowerCount = previousValue;
    })
    .finally(() => {
      row._limitSaving = false;
    });
}
function submitLimitDialog() {
  const maxCount = Math.max(20, Number(limitDialog.maxInternalPowerCount || 20));
  batchInternalPowerLimit(ids.value, maxCount).then(() => {
    proxy.$modal.msgSuccess("最大内功数已更新");
    limitDialog.open = false;
    getList();
  });
}
function handleCommand(command, row) {
  switch (command) {
    case "handleResetPwd":
      handleResetPwd(row);
      break;
    case "handleAuthRole":
      handleAuthRole(row);
      break;
    default:
      break;
  }
}
function handleAuthRole(row) {
  const userId = row.userId;
  router.push("/system/user-auth/role/" + userId);
}
function handleResetPwd(row) {
  proxy
    .$prompt('请输入"' + row.userName + '"的新密码', "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      closeOnClickModal: false,
      inputPattern: /^.{5,20}$/,
      inputErrorMessage: "用户密码长度必须介于 5 和 20 之间",
      inputValidator: (value) => {
        if (/<|>|"|'|\||\\/.test(value)) {
          return "不能包含非法字符：< > \" ' \\\ |";
        }
      },
    })
    .then(({ value }) => {
      resetUserPwd(row.userId, value).then((response) => {
        proxy.$modal.msgSuccess("修改成功，新密码是：" + value);
      });
    })
    .catch(() => {});
}
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.userId);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}
function handleImport() {
  upload.title = "用户导入";
  upload.open = true;
  upload.selectedFile = null;
}
function importTemplate() {
  proxy.download(
    "system/user/importTemplate",
    {},
    `user_template_${new Date().getTime()}.xlsx`
  );
}
const handleFileUploadProgress = (event, file, fileList) => {
  upload.isUploading = true;
};
const handleFileChange = (file, fileList) => {
  upload.selectedFile = file;
};
const handleFileRemove = (file, fileList) => {
  upload.selectedFile = null;
};
const handleFileSuccess = (response, file, fileList) => {
  upload.open = false;
  upload.isUploading = false;
  proxy.$refs["uploadRef"].handleRemove(file);
  proxy.$alert(
    "<div style='overflow: auto;overflow-x: hidden;max-height: 70vh;padding: 10px 20px 0;'>" +
      response.msg +
      "</div>",
    "导入结果",
    { dangerouslyUseHTMLString: true }
  );
  getList();
};
function submitFileForm() {
  const file = upload.selectedFile;
  if (
    !file ||
    file.length === 0 ||
    (!file.name.toLowerCase().endsWith(".xls") &&
      !file.name.toLowerCase().endsWith(".xlsx"))
  ) {
    proxy.$modal.msgError("请选择后缀为 “xls”或“xlsx”的文件。");
    return;
  }
  proxy.$refs["uploadRef"].submit();
}
function reset() {
  form.value = {
    userId: undefined,
    userName: undefined,
    nickName: undefined,
    password: undefined,
    email: undefined,
    sex: undefined,
    status: "0",
    isVip: "0",
    aiImageRecognitionCount: 0,
    vipAiImageRecognitionCount: 0,
    sponsorEnabled: "0",
    maxInternalPowerCount: 20,
    remark: undefined,
    roleIds: [],
  };
  proxy.resetForm("userRef");
}
function buildUserPayload() {
  const payload = {
    userId: form.value.userId,
    userName: form.value.userName?.trim(),
    nickName: form.value.nickName?.trim(),
    email: form.value.email || "",
    sex: form.value.sex !== undefined && form.value.sex !== null ? String(form.value.sex) : undefined,
    status: form.value.status !== undefined && form.value.status !== null ? String(form.value.status) : "0",
    remark: form.value.remark || "",
    roleIds: Array.isArray(form.value.roleIds)
      ? form.value.roleIds.map((item) => Number(item)).filter((item) => !Number.isNaN(item))
      : [],
  };
  if (form.value.password) {
    payload.password = form.value.password;
  }
  if (canManageVip.value) {
    payload.isVip = form.value.isVip === "1" ? "1" : "0";
    payload.aiImageRecognitionCount = Math.max(0, Number(form.value.aiImageRecognitionCount || 0));
    payload.vipAiImageRecognitionCount = Math.max(0, Number(form.value.vipAiImageRecognitionCount || 0));
    payload.maxInternalPowerCount = Math.max(20, Number(form.value.maxInternalPowerCount || 20));
  }
  return payload;
}
function cancel() {
  open.value = false;
  reset();
}
function handleAdd() {
  reset();
  Promise.all([
    getUser(),
    getDefaultAiRecognitionCount().catch(() => ({ data: { aiImageRecognitionCount: 0 } })),
  ]).then(([response, defaultAiResponse]) => {
    roleOptions.value = response.roles;
    open.value = true;
    title.value = "添加用户";
    form.value.password = initPassword.value;
    form.value.isVip = "0";
    form.value.aiImageRecognitionCount = Number(defaultAiResponse.data?.aiImageRecognitionCount || 0);
    form.value.vipAiImageRecognitionCount = 0;
    form.value.maxInternalPowerCount = 20;
  });
}
function handleUpdate(row) {
  reset();
  const userId = row.userId || ids.value;
  getUser(userId).then((response) => {
    form.value = response.data;
    roleOptions.value = response.roles;
    form.value.roleIds = response.roleIds;
    form.value.isVip = response.data?.isVip || "0";
    form.value.aiImageRecognitionCount = Number(response.data?.aiImageRecognitionCount || 0);
    form.value.vipAiImageRecognitionCount = Number(response.data?.vipAiImageRecognitionCount || 0);
    form.value.maxInternalPowerCount = response.data?.maxInternalPowerCount || 20;
    open.value = true;
    title.value = "修改用户";
    form.value.password = undefined;
  });
}
function submitForm() {
  proxy.$refs["userRef"].validate((valid) => {
    if (valid) {
      const payload = buildUserPayload();
      if (form.value.userId != undefined) {
        updateUser(payload).then((response) => {
          proxy.$modal.msgSuccess("修改成功");
          open.value = false;
          getList();
        });
      } else {
        addUser(payload).then((response) => {
          proxy.$modal.msgSuccess("新增成功");
          open.value = false;
          getList();
        });
      }
    }
  });
}

onMounted(() => {
  fetchRoleOptions();
  fetchRegisterCleanupRule();
  getList();
  proxy.getConfigKey("sys.user.initPassword").then((response) => {
    initPassword.value = response.msg;
  });
});
</script>

<style scoped>
.role-tags {
  display: flex;
  justify-content: center;
  gap: 6px;
  flex-wrap: wrap;
}

.cleanup-rule-toggle {
  height: 32px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-regular);
  font-size: 13px;
  white-space: nowrap;
}

.vip-cell,
.limit-cell {
  display: grid;
  justify-items: center;
  gap: 4px;
}

.vip-cell small {
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.limit-cell strong {
  color: var(--el-color-primary);
}

.limit-cell small {
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.inline-limit-input {
  width: 116px;
}

.inline-limit-input :deep(.el-input__wrapper) {
  border-radius: 999px;
}
</style>
