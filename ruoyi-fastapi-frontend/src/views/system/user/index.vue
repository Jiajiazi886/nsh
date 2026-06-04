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
          <right-toolbar
            v-model:showSearch="showSearch"
            @queryTable="getList"
            :columns="columns"
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
              v-if="form.userId == undefined"
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
import {
  changeUserStatus,
  listUser,
  resetUserPwd,
  delUser,
  getUser,
  updateUser,
  addUser,
} from "@/api/system/user";

const router = useRouter();
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
  status: { label: "状态", visible: true },
  createTime: { label: "创建时间", visible: true },
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
      userList.value = res.rows;
      total.value = res.total;
    }
  );
}
function handleQuery() {
  queryParams.value.pageNum = 1;
  getList();
}
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
    remark: undefined,
    roleIds: [],
  };
  proxy.resetForm("userRef");
}
function cancel() {
  open.value = false;
  reset();
}
function handleAdd() {
  reset();
  getUser().then((response) => {
    roleOptions.value = response.roles;
    open.value = true;
    title.value = "添加用户";
    form.value.password = initPassword.value;
  });
}
function handleUpdate(row) {
  reset();
  const userId = row.userId || ids.value;
  getUser(userId).then((response) => {
    form.value = response.data;
    roleOptions.value = response.roles;
    form.value.roleIds = response.roleIds;
    open.value = true;
    title.value = "修改用户";
    form.value.password = undefined;
  });
}
function submitForm() {
  proxy.$refs["userRef"].validate((valid) => {
    if (valid) {
      if (form.value.userId != undefined) {
        updateUser(form.value).then((response) => {
          proxy.$modal.msgSuccess("修改成功");
          open.value = false;
          getList();
        });
      } else {
        addUser(form.value).then((response) => {
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
</style>
