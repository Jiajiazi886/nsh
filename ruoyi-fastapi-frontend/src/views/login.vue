<template>
  <div class="auth-page">
    <section class="auth-visual">
      <div class="visual-copy">
        <p>欢迎回来</p>
        <h1>帮会事务，从这里开始。</h1>
        <span>登录后继续管理成员、分团、约战和系统权限。</span>
      </div>

      <div class="characters-stage">
        <AnimatedCharacters
          :is-typing="isTyping"
          :show-password="showPassword"
          :password-length="loginForm.password.length"
          :login-failed="loginFailed"
          :login-success="loginSuccess"
        />
      </div>

      <div class="grid-overlay"></div>
      <div class="blur-circle blur-circle-1"></div>
      <div class="blur-circle blur-circle-2"></div>
    </section>

    <section class="auth-panel">
      <div class="form-wrapper">
        <div class="form-header">
          <p class="form-kicker">账号登录</p>
          <h2>进入管理系统</h2>
          <span>请输入账号信息，角色和权限会自动匹配。</span>
        </div>

        <el-form ref="loginRef" :model="loginForm" :rules="loginRules" class="auth-form">
          <el-form-item prop="username">
            <label class="form-label">账号</label>
            <el-input
              v-model="loginForm.username"
              type="text"
              size="large"
              autocomplete="off"
              placeholder="请输入账号"
              @focus="isTyping = true"
              @blur="isTyping = false"
            >
              <template #prefix><svg-icon icon-class="user" class="input-icon" /></template>
            </el-input>
          </el-form-item>

          <el-form-item prop="password">
            <label class="form-label">密码</label>
            <div class="password-field">
              <el-input
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                size="large"
                autocomplete="off"
                placeholder="请输入密码"
                @focus="isTyping = true"
                @blur="isTyping = false"
                @keyup.enter="handleLogin"
              >
                <template #prefix><svg-icon icon-class="password" class="input-icon" /></template>
              </el-input>
              <button type="button" class="password-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? "隐藏" : "显示" }}
              </button>
            </div>
          </el-form-item>

          <div class="form-options">
            <el-checkbox v-model="loginForm.rememberMe">记住密码</el-checkbox>
            <router-link v-if="register" class="auth-link" :to="'/register'">立即注册</router-link>
          </div>

          <el-button :loading="loading" class="submit-button" size="large" @click.prevent="handleLogin">
            <span>{{ loading ? "登录中..." : "登录" }}</span>
            <span v-if="!loading" class="button-arrow" aria-hidden="true"></span>
          </el-button>
        </el-form>
      </div>
    </section>

    <div class="auth-footer">
      <span>{{ footerContent }}</span>
      <button type="button" class="contact-admin-button" @click="contactDialogVisible = true">联系管理员</button>
    </div>

    <el-dialog
      v-model="contactDialogVisible"
      title="联系管理员"
      width="380px"
      class="contact-admin-dialog"
      append-to-body
      align-center
    >
      <div class="contact-admin-card">
        <img
          v-if="!qrLoadFailed"
          class="contact-admin-qr"
          :src="contactQrUrl"
          alt="联系管理员微信二维码"
          @error="qrLoadFailed = true"
        />
        <div v-else class="contact-admin-missing">
          <strong>二维码图片未放入项目</strong>
          <span>请放到 public/contact-admin-wechat.png</span>
        </div>
        <p>{{ qrLoadFailed ? "放入图片后刷新页面即可显示" : "扫码添加管理员微信" }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { getAuthConfig } from "@/api/login";
import Cookies from "js-cookie";
import { encrypt, decrypt } from "@/utils/jsencrypt";
import { resolveLoginRedirectPath } from "@/utils/loginRedirect";
import useUserStore from "@/store/modules/user";
import defaultSettings from "@/settings";
import AnimatedCharacters from "@/components/AuthCharacters/AnimatedCharacters.vue";

const footerContent = defaultSettings.footerContent;
const contactQrUrl = "/contact-admin-wechat.png";
const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const { proxy } = getCurrentInstance();

const loginForm = ref({
  username: "",
  password: "",
  rememberMe: false
});

const loginRules = {
  username: [{ required: true, trigger: "blur", message: "请输入您的账号" }],
  password: [{ required: true, trigger: "blur", message: "请输入您的密码" }]
};

const loading = ref(false);
const register = ref(false);
const redirect = ref(undefined);
const showPassword = ref(false);
const isTyping = ref(false);
const loginFailed = ref(false);
const loginSuccess = ref(false);
const contactDialogVisible = ref(false);
const qrLoadFailed = ref(false);

function printContactToConsole() {
  console.log("联系这个微信");
  console.log(`二维码图片：${window.location.origin}${contactQrUrl}`);
  console.log(
    "%c ",
    [
      "display: block",
      "width: 260px",
      "height: 340px",
      `background: url('${contactQrUrl}') center / contain no-repeat`,
      "border-radius: 12px",
      "background-color: #fff"
    ].join(";")
  );
}

watch(route, (newRoute) => {
  redirect.value = newRoute.query && newRoute.query.redirect;
}, { immediate: true });

function handleLogin() {
  proxy.$refs.loginRef.validate(valid => {
    if (!valid) {
      return;
    }
    loading.value = true;
    loginFailed.value = false;
    loginSuccess.value = false;
    if (loginForm.value.rememberMe) {
      Cookies.set("username", loginForm.value.username, { expires: 30 });
      Cookies.set("password", encrypt(loginForm.value.password), { expires: 30 });
      Cookies.set("rememberMe", loginForm.value.rememberMe, { expires: 30 });
    } else {
      Cookies.remove("username");
      Cookies.remove("password");
      Cookies.remove("rememberMe");
    }
    userStore.login(loginForm.value).then(() => {
      loginSuccess.value = true;
      const query = route.query;
      const otherQueryParams = Object.keys(query).reduce((acc, cur) => {
        if (cur !== "redirect") {
          acc[cur] = query[cur];
        }
        return acc;
      }, {});
      setTimeout(() => {
        router.push({ path: resolveLoginRedirectPath(redirect.value), query: otherQueryParams });
      }, 450);
    }).catch(() => {
      loading.value = false;
      loginFailed.value = true;
      setTimeout(() => {
        loginFailed.value = false;
      }, 3000);
    });
  });
}

function fetchAuthConfig() {
  getAuthConfig().then(res => {
    register.value = res.registerEnabled === undefined ? false : res.registerEnabled;
  });
}

function getCookie() {
  const username = Cookies.get("username");
  const password = Cookies.get("password");
  const rememberMe = Cookies.get("rememberMe");
  loginForm.value.username = username === undefined ? loginForm.value.username : username;
  loginForm.value.password = password === undefined ? loginForm.value.password : decrypt(password);
  loginForm.value.rememberMe = rememberMe === undefined ? false : Boolean(rememberMe);
}

fetchAuthConfig();
getCookie();
onMounted(() => {
  printContactToConsole();
});
</script>

<style lang="scss" scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(520px, 1fr) minmax(420px, 0.86fr);
  background: #ffffff;
  color: #111827;
  overflow: hidden;
}

.auth-visual {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 42px 56px 48px;
  color: #ffffff;
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 42%, #2d2d2d 100%);
  overflow: hidden;
}

.visual-copy {
  position: relative;
  z-index: 2;
  max-width: 560px;
}

.visual-copy p,
.form-kicker {
  margin: 0 0 12px;
  color: #e8d754;
  font-size: 14px;
  font-weight: 700;
}

.visual-copy h1 {
  margin: 0;
  font-size: 46px;
  line-height: 1.08;
  letter-spacing: 0;
}

.visual-copy span {
  display: block;
  margin-top: 18px;
  color: rgba(255, 255, 255, 0.78);
  font-size: 16px;
  line-height: 1.7;
}

.characters-stage {
  position: relative;
  z-index: 2;
  height: 420px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 22px 22px;
  opacity: 0.9;
}

.blur-circle {
  position: absolute;
  border-radius: 999px;
  filter: blur(46px);
  opacity: 0.75;
}

.blur-circle-1 {
  width: 240px;
  height: 240px;
  right: -80px;
  top: 12%;
  background: rgba(108, 63, 245, 0.3);
}

.blur-circle-2 {
  width: 210px;
  height: 210px;
  left: -70px;
  bottom: 12%;
  background: rgba(255, 155, 107, 0.28);
}

.auth-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 56px 48px;
  background:
    radial-gradient(circle at top right, rgba(232, 215, 84, 0.18), transparent 34%),
    #ffffff;
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
}

.form-header {
  margin-bottom: 28px;
}

.form-header h2 {
  margin: 0;
  color: #111827;
  font-size: 34px;
  line-height: 1.18;
  letter-spacing: 0;
}

.form-header span {
  display: block;
  margin-top: 12px;
  color: #6b7280;
  line-height: 1.7;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.form-label {
  display: block;
  width: 100%;
  margin-bottom: 8px;
  color: #374151;
  font-size: 14px;
  font-weight: 700;
}

.password-field {
  width: 100%;
  display: flex;
  gap: 10px;
}

.password-field :deep(.el-input) {
  flex: 1;
}

:deep(.el-input__wrapper) {
  min-height: 48px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: inset 0 0 0 1.5px rgba(209, 213, 219, 0.9);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 0 0 1.5px #6c3ff5,
    0 0 0 4px rgba(108, 63, 245, 0.12);
}

.input-icon {
  color: #9ca3af;
}

.password-toggle {
  height: 48px;
  border: 1.5px solid rgba(209, 213, 219, 0.9);
  border-radius: 8px;
  background: #ffffff;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s ease;
}

.password-toggle {
  width: 68px;
  font-weight: 700;
}

.password-toggle:hover {
  border-color: #6c3ff5;
  color: #6c3ff5;
  transform: translateY(-1px);
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 2px 0 18px;
}

.auth-link {
  color: #6c3ff5;
  font-weight: 700;
}

.submit-button {
  width: 100%;
  height: 48px;
  border: 0;
  border-radius: 8px;
  background: #111827;
  color: #ffffff;
  font-weight: 800;
  box-shadow: 0 16px 34px rgba(17, 24, 39, 0.2);
  transition: all 0.22s ease;
}

.submit-button:hover {
  background: #2d2d2d;
  transform: translateY(-2px);
  box-shadow: 0 20px 36px rgba(17, 24, 39, 0.25);
}

.button-arrow {
  width: 18px;
  height: 12px;
  margin-left: 8px;
  position: relative;
  transition: transform 0.22s ease;
}

.button-arrow::before,
.button-arrow::after {
  content: "";
  position: absolute;
  right: 0;
  top: 50%;
  background: currentColor;
}

.button-arrow::before {
  width: 18px;
  height: 2px;
  transform: translateY(-50%);
}

.button-arrow::after {
  width: 8px;
  height: 8px;
  border-top: 2px solid currentColor;
  border-right: 2px solid currentColor;
  background: transparent;
  transform: translateY(-50%) rotate(45deg);
}

.submit-button:hover .button-arrow {
  transform: translateX(4px);
}

.auth-footer {
  position: fixed;
  left: 0;
  right: auto;
  bottom: 10px;
  width: 54vw;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  color: rgba(255, 255, 255, 0.76);
  font-size: 12px;
}

.contact-admin-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: rgba(232, 215, 84, 0.95);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition: color 0.2s ease, transform 0.2s ease;
}

.contact-admin-button:hover {
  color: #ffffff;
  transform: translateY(-1px);
}

.contact-admin-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 6px 0 4px;
}

.contact-admin-qr {
  width: min(100%, 300px);
  aspect-ratio: 1 / 1.28;
  object-fit: contain;
  border-radius: 10px;
  background: #ffffff;
}

.contact-admin-missing {
  width: min(100%, 300px);
  aspect-ratio: 1 / 1.28;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px;
  border: 1px dashed rgba(107, 114, 128, 0.4);
  border-radius: 10px;
  background:
    linear-gradient(135deg, rgba(232, 215, 84, 0.12), rgba(108, 63, 245, 0.08)),
    #ffffff;
  color: #111827;
  text-align: center;
}

.contact-admin-missing span {
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}

.contact-admin-card p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

@media (max-width: 1080px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .auth-visual {
    display: none;
  }

  .auth-panel {
    min-height: 100vh;
  }

  .auth-footer {
    width: 100%;
    color: #9ca3af;
  }

  .contact-admin-button {
    color: #6c3ff5;
  }
}

@media (max-width: 520px) {
  .auth-panel {
    padding: 32px 20px;
  }

  .form-header h2 {
    font-size: 28px;
  }

}
</style>
