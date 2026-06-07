<template>
  <div class="auth-page register-page">
    <section class="auth-visual">
      <div class="brand-mark">
        <span class="brand-leaf"></span>
        <strong>{{ title }}</strong>
      </div>

      <div class="visual-copy">
        <p>创建新账号</p>
        <h1>加入系统，开始你的帮会管理旅程。</h1>
        <span>注册后默认成为 user 角色，可继续申请帮会、维护个人信息并参与后续流程。</span>
      </div>

      <div class="characters-stage">
        <AnimatedCharacters
          :is-typing="isTyping"
          :show-password="showPassword || showConfirmPassword"
          :password-length="registerForm.password.length + registerForm.confirmPassword.length"
          :login-failed="registerFailed"
          :login-success="registerSuccess"
        />
      </div>

      <div class="grid-overlay"></div>
      <div class="blur-circle blur-circle-1"></div>
      <div class="blur-circle blur-circle-2"></div>
    </section>

    <section class="auth-panel">
      <div class="form-wrapper">
        <div class="form-header">
          <p class="form-kicker">账号注册</p>
          <h2>创建账号</h2>
          <span>填写账号和密码，注册成功后再返回登录。</span>
        </div>

        <el-form ref="registerRef" :model="registerForm" :rules="registerRules" class="auth-form">
          <el-form-item prop="username">
            <label class="form-label">账号</label>
            <el-input
              v-model="registerForm.username"
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
                v-model="registerForm.password"
                :type="showPassword ? 'text' : 'password'"
                size="large"
                autocomplete="new-password"
                placeholder="请输入密码"
                @focus="isTyping = true"
                @blur="isTyping = false"
                @keyup.enter="handleRegister"
              >
                <template #prefix><svg-icon icon-class="password" class="input-icon" /></template>
              </el-input>
              <button type="button" class="password-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? "隐藏" : "显示" }}
              </button>
            </div>
            <div class="password-meter" aria-hidden="true">
              <span :class="{ active: passwordStrength >= 1 }"></span>
              <span :class="{ active: passwordStrength >= 2 }"></span>
              <span :class="{ active: passwordStrength >= 3 }"></span>
            </div>
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <label class="form-label">确认密码</label>
            <div class="password-field">
              <el-input
                v-model="registerForm.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                size="large"
                autocomplete="new-password"
                placeholder="请再次输入密码"
                @focus="isTyping = true"
                @blur="isTyping = false"
                @keyup.enter="handleRegister"
              >
                <template #prefix><svg-icon icon-class="password" class="input-icon" /></template>
              </el-input>
              <button type="button" class="password-toggle" @click="showConfirmPassword = !showConfirmPassword">
                {{ showConfirmPassword ? "隐藏" : "显示" }}
              </button>
            </div>
          </el-form-item>

          <el-form-item prop="code" v-if="captchaEnabled">
            <label class="form-label">验证码</label>
            <div class="captcha-row">
              <el-input
                v-model="registerForm.code"
                size="large"
                autocomplete="off"
                placeholder="请输入验证码"
                @focus="isTyping = true"
                @blur="isTyping = false"
                @keyup.enter="handleRegister"
              >
                <template #prefix><svg-icon icon-class="validCode" class="input-icon" /></template>
              </el-input>
              <button type="button" class="captcha-image" @click="getCode">
                <img :src="codeUrl" alt="验证码" />
              </button>
            </div>
          </el-form-item>

          <el-button :loading="loading" class="submit-button" size="large" @click.prevent="handleRegister">
            <span>{{ loading ? "创建中..." : "创建账号" }}</span>
            <span v-if="!loading" class="button-arrow" aria-hidden="true"></span>
          </el-button>

          <div class="signin-link">
            已有账号？
            <router-link class="auth-link" :to="'/login'">返回登录</router-link>
          </div>
        </el-form>
      </div>
    </section>

    <div class="auth-footer">
      <span>{{ footerContent }}</span>
    </div>
  </div>
</template>

<script setup>
import { ElMessageBox } from "element-plus";
import { getCodeImg, register } from "@/api/login";
import defaultSettings from "@/settings";
import AnimatedCharacters from "@/components/AuthCharacters/AnimatedCharacters.vue";

const title = import.meta.env.VITE_APP_TITLE;
const footerContent = defaultSettings.footerContent;
const router = useRouter();
const { proxy } = getCurrentInstance();

const registerForm = ref({
  username: "",
  password: "",
  confirmPassword: "",
  code: "",
  uuid: ""
});

const showPassword = ref(false);
const showConfirmPassword = ref(false);
const isTyping = ref(false);
const registerFailed = ref(false);
const registerSuccess = ref(false);

const equalToPassword = (rule, value, callback) => {
  if (registerForm.value.password !== value) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const registerRules = {
  username: [
    { required: true, trigger: "blur", message: "请输入您的账号" },
    { min: 2, max: 20, message: "用户账号长度必须介于 2 和 20 之间", trigger: "blur" }
  ],
  password: [
    { required: true, trigger: "blur", message: "请输入您的密码" },
    { min: 5, max: 20, message: "用户密码长度必须介于 5 和 20 之间", trigger: "blur" },
    { pattern: /^[^<>"'|\\]+$/, message: "不能包含非法字符：< > \" ' \\ |", trigger: "blur" }
  ],
  confirmPassword: [
    { required: true, trigger: "blur", message: "请再次输入您的密码" },
    { required: true, validator: equalToPassword, trigger: "blur" }
  ],
  code: [{ required: true, trigger: "change", message: "请输入验证码" }]
};

const passwordStrength = computed(() => {
  let score = 0;
  if (registerForm.value.password.length >= 5) score += 1;
  if (/[A-Z]/.test(registerForm.value.password) || /\d/.test(registerForm.value.password)) score += 1;
  if (registerForm.value.password.length >= 10 || /[^A-Za-z0-9]/.test(registerForm.value.password)) score += 1;
  return score;
});

const codeUrl = ref("");
const loading = ref(false);
const captchaEnabled = ref(true);

function handleRegister() {
  proxy.$refs.registerRef.validate(valid => {
    if (!valid) {
      return;
    }
    loading.value = true;
    registerFailed.value = false;
    registerSuccess.value = false;
    register(registerForm.value).then(() => {
      const username = registerForm.value.username;
      registerSuccess.value = true;
      setTimeout(() => {
        ElMessageBox.alert("<font color='red'>恭喜你，您的账号 " + username + " 注册成功！</font>", "系统提示", {
          dangerouslyUseHTMLString: true,
          type: "success"
        }).then(() => {
          router.push("/login");
        }).catch(() => {});
      }, 450);
    }).catch(() => {
      loading.value = false;
      registerFailed.value = true;
      setTimeout(() => {
        registerFailed.value = false;
      }, 3000);
      if (captchaEnabled.value) {
        getCode();
      }
    });
  });
}

function getCode() {
  getCodeImg().then(res => {
    captchaEnabled.value = res.captchaEnabled === undefined ? true : res.captchaEnabled;
    if (captchaEnabled.value) {
      codeUrl.value = "data:image/gif;base64," + res.img;
      registerForm.value.uuid = res.uuid;
    }
  });
}

getCode();
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

.brand-mark {
  position: relative;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  letter-spacing: 0;
}

.brand-leaf {
  width: 34px;
  height: 34px;
  border-radius: 12px 12px 2px 12px;
  background: linear-gradient(135deg, #6c3ff5, #ff9b6b);
  transform: rotate(-24deg);
  box-shadow: 0 12px 30px rgba(17, 24, 39, 0.25);
}

.visual-copy {
  position: relative;
  z-index: 2;
  max-width: 600px;
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
  font-size: 44px;
  line-height: 1.1;
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
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 44px 48px;
  background:
    radial-gradient(circle at top right, rgba(232, 215, 84, 0.18), transparent 34%),
    #ffffff;
  overflow-y: auto;
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
}

.form-header {
  margin-bottom: 24px;
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
  gap: 2px;
}

.form-label {
  display: block;
  width: 100%;
  margin-bottom: 8px;
  color: #374151;
  font-size: 14px;
  font-weight: 700;
}

.password-field,
.captcha-row {
  width: 100%;
  display: flex;
  gap: 10px;
}

.password-field :deep(.el-input),
.captcha-row :deep(.el-input) {
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

.password-toggle,
.captcha-image {
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

.password-toggle:hover,
.captcha-image:hover {
  border-color: #6c3ff5;
  color: #6c3ff5;
  transform: translateY(-1px);
}

.captcha-image {
  width: 116px;
  padding: 0;
  overflow: hidden;
}

.captcha-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.password-meter {
  display: flex;
  gap: 6px;
  margin-top: 10px;
}

.password-meter span {
  height: 4px;
  flex: 1;
  border-radius: 999px;
  background: #e5e7eb;
  transition: background 0.2s ease;
}

.password-meter span.active:nth-child(1) {
  background: #ff9b6b;
}

.password-meter span.active:nth-child(2) {
  background: #e8d754;
}

.password-meter span.active:nth-child(3) {
  background: #30b08f;
}

.submit-button {
  width: 100%;
  height: 48px;
  margin-top: 4px;
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

.signin-link {
  margin-top: 18px;
  color: #6b7280;
  text-align: center;
}

.auth-link {
  color: #6c3ff5;
  font-weight: 700;
}

.auth-footer {
  position: fixed;
  left: 0;
  right: auto;
  bottom: 10px;
  width: 54vw;
  z-index: 3;
  text-align: center;
  color: rgba(255, 255, 255, 0.76);
  font-size: 12px;
}

@media (max-width: 1080px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .auth-visual {
    display: none;
  }

  .auth-footer {
    width: 100%;
    color: #9ca3af;
  }
}

@media (max-width: 520px) {
  .auth-panel {
    padding: 32px 20px;
  }

  .form-header h2 {
    font-size: 28px;
  }

  .captcha-row {
    flex-direction: column;
  }

  .captcha-image {
    width: 100%;
  }
}
</style>
