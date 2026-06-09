# Liquid Glass SCSS Skill for nsh

## 适用项目

本 Skill 适用于 `Jiajiazi886/nsh` 项目的前端工程：

```text
ruoyi-fastapi-frontend/
```

项目技术栈：

- Vue 3
- Vite
- Element Plus
- SCSS / Sass
- RuoYi-Vue3-FastAPI 前端结构

当前项目已经具备 SCSS 编译能力，`package.json` 中包含 `sass-embedded`，全局样式入口为：

```text
ruoyi-fastapi-frontend/src/assets/styles/index.scss
```

不要把本 Skill 应用于后端目录：

```text
ruoyi-fastapi-backend/
```

---

## 触发条件

当用户提出以下需求时，优先使用本 Skill：

- 给页面增加液态玻璃效果
- 做苹果 Liquid Glass 风格
- 做毛玻璃、透明玻璃、玻璃拟态、玻璃卡片
- 适配 SCSS 的液态玻璃效果
- 优化登录页、后台首页、AI 聊天页、表单页的高级玻璃 UI
- 将普通 Element Plus 页面改成高级透明玻璃风格

---

## 核心原则

1. 只修改前端样式和必要的前端模板结构。
2. 不修改后端 Python、FastAPI、数据库、权限、登录逻辑。
3. 不破坏 RuoYi 原有布局、菜单、路由、权限判断。
4. 优先使用 SCSS mixin 封装，避免在每个页面重复写大量样式。
5. Element Plus 组件样式需要使用 Vue scoped 样式下的 `:deep()`。
6. 所有新增文件必须使用 UTF-8 编码。
7. 如果页面已有业务逻辑，只改视觉层，不动接口调用和状态管理。
8. 液态玻璃效果应兼顾性能，不要默认引入 WebGL。
9. 默认使用 `backdrop-filter`、半透明背景、高光边框、内阴影、柔和投影、渐变背景实现。
10. SVG / WebGL 折射只作为增强项，不作为默认方案。

---

## 推荐文件结构

优先新增：

```text
ruoyi-fastapi-frontend/src/assets/styles/liquid-glass.scss
```

然后在全局样式入口中引入：

```text
ruoyi-fastapi-frontend/src/assets/styles/index.scss
```

引入方式：

```scss
@use './liquid-glass.scss';
```

如果单个 Vue 页面需要使用 mixin，则在页面的 scoped 样式中写：

```scss
@use "@/assets/styles/liquid-glass.scss" as glass;
```

---

## 标准 liquid-glass.scss 内容

创建或更新：

```text
ruoyi-fastapi-frontend/src/assets/styles/liquid-glass.scss
```

推荐内容：

```scss
$liquid-bg: rgba(255, 255, 255, 0.16) !default;
$liquid-border: rgba(255, 255, 255, 0.36) !default;
$liquid-highlight: rgba(255, 255, 255, 0.62) !default;
$liquid-radius: 28px !default;
$liquid-blur: 26px !default;
$liquid-shadow: 0 24px 80px rgba(15, 23, 42, 0.28) !default;

@mixin liquid-glass(
  $radius: $liquid-radius,
  $blur: $liquid-blur,
  $bg: $liquid-bg,
  $border: $liquid-border,
  $shadow: $liquid-shadow
) {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  border-radius: $radius;
  background: $bg;
  border: 1px solid $border;

  backdrop-filter: blur($blur) saturate(180%);
  -webkit-backdrop-filter: blur($blur) saturate(180%);

  box-shadow:
    inset 0 1px 0 $liquid-highlight,
    inset 0 -1px 0 rgba(255, 255, 255, 0.12),
    $shadow;

  &::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    border-radius: inherit;
    background:
      radial-gradient(circle at 18% 10%, rgba(255, 255, 255, 0.48), transparent 32%),
      radial-gradient(circle at 86% 90%, rgba(255, 255, 255, 0.2), transparent 36%);
    opacity: 0.82;
    pointer-events: none;
  }

  &::after {
    content: "";
    position: absolute;
    inset: 1px;
    z-index: 1;
    border-radius: inherit;
    border: 1px solid rgba(255, 255, 255, 0.14);
    pointer-events: none;
  }
}

@mixin liquid-hover {
  transition:
    transform 0.28s ease,
    box-shadow 0.28s ease,
    background 0.28s ease,
    border-color 0.28s ease;

  &:hover {
    transform: translateY(-2px);
    background: rgba(255, 255, 255, 0.22);
    border-color: rgba(255, 255, 255, 0.48);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.7),
      0 30px 90px rgba(15, 23, 42, 0.34);
  }
}

.liquid-glass {
  @include liquid-glass;
}

.liquid-glass-hover {
  @include liquid-hover;
}

.liquid-glass-card {
  @include liquid-glass(24px, 24px, rgba(255, 255, 255, 0.18));
}

.liquid-glass-panel {
  @include liquid-glass(34px, 30px, rgba(255, 255, 255, 0.2));
}

.liquid-glass-button {
  @include liquid-glass(999px, 18px, rgba(255, 255, 255, 0.22));
  @include liquid-hover;

  border: 0;
  color: #fff;
  cursor: pointer;
  font-weight: 700;
}
```

---

## 全局入口修改规则

修改：

```text
ruoyi-fastapi-frontend/src/assets/styles/index.scss
```

在现有 `@use` 列表后追加：

```scss
@use './liquid-glass.scss';
```

不要删除原有内容，例如：

```scss
@use './mixin.scss';
@use './transition.scss';
@use './element-ui.scss';
@use './sidebar.scss';
@use './btn.scss';
@use './ruoyi.scss';
@use './liquid-glass.scss';
```

---

## 登录页适配规则

目标文件：

```text
ruoyi-fastapi-frontend/src/views/login.vue
```

该页面已有：

```vue
<style lang="scss" scoped>
```

需要改为：

```scss
<style lang="scss" scoped>
@use "@/assets/styles/liquid-glass.scss" as glass;
```

### `.auth-page`

将登录页背景改为暗色液态渐变：

```scss
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(520px, 1fr) minmax(420px, 0.86fr);
  color: #111827;
  overflow: hidden;
  background:
    radial-gradient(circle at 15% 18%, rgba(108, 63, 245, 0.42), transparent 30%),
    radial-gradient(circle at 82% 22%, rgba(232, 215, 84, 0.34), transparent 28%),
    radial-gradient(circle at 52% 88%, rgba(255, 155, 107, 0.36), transparent 32%),
    linear-gradient(135deg, #0f172a 0%, #1f2937 46%, #111827 100%);
}
```

### `.auth-visual`

```scss
.auth-visual {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 42px 56px 48px;
  color: #ffffff;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.02)),
    radial-gradient(circle at 28% 20%, rgba(255, 255, 255, 0.16), transparent 34%);
}
```

### `.auth-panel`

```scss
.auth-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 56px 48px;
  background: transparent;
}
```

### `.form-wrapper`

```scss
.form-wrapper {
  @include glass.liquid-glass(34px, 32px, rgba(255, 255, 255, 0.2));

  width: 100%;
  max-width: 440px;
  padding: 38px;
  color: #ffffff;
}
```

### 表单文字颜色

```scss
.form-header h2 {
  margin: 0;
  color: #ffffff;
  font-size: 34px;
  line-height: 1.18;
  letter-spacing: 0;
}

.form-header span {
  display: block;
  margin-top: 12px;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.7;
}

.form-label {
  color: rgba(255, 255, 255, 0.86);
}
```

### Element Plus 输入框

在 scoped 样式中必须使用 `:deep()`：

```scss
:deep(.el-input__wrapper) {
  min-height: 48px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.18);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.34),
    inset 0 0 0 1px rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.48),
    inset 0 0 0 1.5px rgba(232, 215, 84, 0.82),
    0 0 0 4px rgba(232, 215, 84, 0.16);
}

:deep(.el-input__inner) {
  color: #ffffff;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.56);
}
```

### 登录按钮

```scss
.submit-button {
  width: 100%;
  height: 50px;
  border: 0;
  border-radius: 999px;
  color: #ffffff;
  font-weight: 800;
  background:
    linear-gradient(135deg, rgba(232, 215, 84, 0.92), rgba(255, 155, 107, 0.9)),
    rgba(255, 255, 255, 0.18);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.42),
    0 18px 40px rgba(0, 0, 0, 0.24);
  transition: all 0.22s ease;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.56),
    0 24px 54px rgba(0, 0, 0, 0.32);
}
```

---

## 后台内容页适配规则

对于普通后台页面，不要大面积改布局。优先只给主要容器加玻璃卡片：

```vue
<div class="app-container liquid-page-bg">
  <div class="liquid-glass-card page-card">
    <!-- 原页面内容 -->
  </div>
</div>
```

推荐 SCSS：

```scss
.liquid-page-bg {
  min-height: calc(100vh - 84px);
  background:
    radial-gradient(circle at 10% 10%, rgba(108, 63, 245, 0.18), transparent 28%),
    radial-gradient(circle at 90% 20%, rgba(232, 215, 84, 0.16), transparent 30%),
    linear-gradient(135deg, #f8fafc, #eef2ff);
}

.page-card {
  padding: 20px;
}
```

---

## Element Plus 表格适配规则

如果需要让 `el-table` 更贴合玻璃风格，使用：

```scss
:deep(.el-table) {
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.7);
}

:deep(.el-table__header-wrapper th) {
  background: rgba(255, 255, 255, 0.72);
}

:deep(.el-table__body-wrapper td) {
  background: rgba(255, 255, 255, 0.48);
}
```

不要强行给所有表格全局加玻璃效果，避免影响后台可读性。

---

## 性能约束

1. `backdrop-filter` 不要套在大量列表项上。
2. 表格行、菜单项、树节点不建议每一项都使用液态玻璃。
3. 大面积区域使用渐变背景，小面积区域使用玻璃卡片。
4. 移动端降低 blur 强度，例如从 `32px` 降到 `18px`。
5. 避免在后台系统中默认使用 WebGL shader。

移动端建议：

```scss
@media (max-width: 768px) {
  .form-wrapper,
  .liquid-glass-panel,
  .liquid-glass-card {
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
  }
}
```

---

## 禁止事项

不要执行以下操作：

- 不要修改 `ruoyi-fastapi-backend/`。
- 不要删除原有权限、路由、登录逻辑。
- 不要把所有 Element Plus 组件全局强制改成透明。
- 不要在没有需求的情况下引入 Three.js、WebGL、GSAP 等重依赖。
- 不要修改数据库配置。
- 不要提交 `node_modules`、`dist`、`.env.*`。
- 不要为了视觉效果牺牲表格、表单、按钮的可读性。

---

## 验收标准

完成适配后，需要确认：

1. `npm run dev` 可以正常启动。
2. 登录页可以正常输入账号密码。
3. 登录按钮 hover 和 loading 状态正常。
4. 页面没有 Sass 编译报错。
5. Element Plus 输入框样式没有被 scoped 隔离影响。
6. 暗色玻璃背景下文字可读。
7. 移动端宽度小于 `1080px` 时布局正常。
8. 后端接口和登录逻辑没有被修改。

---

## 推荐提交信息

```text
feat: add liquid glass scss theme
```

或：

```text
style: apply liquid glass style to login page
```
