<template>
  <div class="navbar" :class="'nav' + settingsStore.navType">
    <hamburger id="hamburger-container" :is-active="appStore.sidebar.opened" class="hamburger-container" @toggleClick="toggleSideBar" />
    <breadcrumb v-if="settingsStore.navType == 1" id="breadcrumb-container" class="breadcrumb-container" />
    <top-nav v-if="settingsStore.navType == 2" id="topmenu-container" class="topmenu-container" />
    <template v-if="settingsStore.navType == 3">
      <logo v-show="settingsStore.sidebarLogo" :collapse="false"></logo>
      <top-bar id="topbar-container" class="topbar-container" />
    </template>

    <div class="nav-signal" aria-hidden="true">
      <span></span>
      <span></span>
      <span></span>
    </div>
    <div class="nav-context" aria-hidden="true">
      <strong>Guild Console</strong>
      <span>live workspace</span>
    </div>
    <div class="right-menu">
      <template v-if="appStore.device !== 'mobile'">
        <el-tooltip content="主题模式" effect="dark" placement="bottom">
          <div class="right-menu-item hover-effect theme-switch-wrapper" @click="toggleTheme">
            <svg-icon v-if="settingsStore.isDark" icon-class="sunny" />
            <svg-icon v-if="!settingsStore.isDark" icon-class="moon" />
          </div>
        </el-tooltip>
      </template>

      <el-dropdown @command="handleCommand" class="avatar-container right-menu-item hover-effect" trigger="hover">
        <div class="avatar-wrapper">
          <img :src="userStore.avatar" class="user-avatar" />
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <router-link to="/user/profile">
              <el-dropdown-item>个人中心</el-dropdown-item>
            </router-link>
            <el-dropdown-item command="setLayout" v-if="settingsStore.showSettings">
                <span>布局设置</span>
              </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <span>退出登录</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'
import Breadcrumb from '@/components/Breadcrumb'
import TopNav from '@/components/TopNav'
import TopBar from './TopBar'
import Logo from './Sidebar/Logo'
import Hamburger from '@/components/Hamburger'
import useAppStore from '@/store/modules/app'
import useUserStore from '@/store/modules/user'
import useSettingsStore from '@/store/modules/settings'

const appStore = useAppStore()
const userStore = useUserStore()
const settingsStore = useSettingsStore()

function toggleSideBar() {
  appStore.toggleSideBar()
}

function handleCommand(command) {
  switch (command) {
    case "setLayout":
      setLayout()
      break
    case "logout":
      logout()
      break
    default:
      break
  }
}

function logout() {
  ElMessageBox.confirm('确定注销并退出系统吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    userStore.logOut().then(() => {
      location.href = '/index'
    })
  }).catch(() => { })
}

const emits = defineEmits(['setLayout'])
function setLayout() {
  emits('setLayout')
}

async function toggleTheme(event) {
  const x = event?.clientX || window.innerWidth / 2
  const y = event?.clientY || window.innerHeight / 2
  const wasDark = settingsStore.isDark

  const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
  const isSupported = document.startViewTransition && !isReducedMotion

  if (!isSupported) {
    settingsStore.toggleTheme()
    return
  }

  try {
    const transition = document.startViewTransition(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10))
      settingsStore.toggleTheme()
      await nextTick()
    })
    await transition.ready

    const endRadius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y))
    const clipPath = [`circle(0px at ${x}px ${y}px)`, `circle(${endRadius}px at ${x}px ${y}px)`]
    document.documentElement.animate(
      {
        clipPath: !wasDark ? [...clipPath].reverse() : clipPath
      }, {
        duration: 650,
        easing: "cubic-bezier(0.4, 0, 0.2, 1)",
        fill: "forwards",
        pseudoElement: !wasDark ? "::view-transition-old(root)" : "::view-transition-new(root)"
      }
    )
    await transition.finished
  } catch (error) {
    console.warn("View transition failed, falling back to immediate toggle:", error)
    settingsStore.toggleTheme()
  }
}
</script>

<style lang='scss' scoped>
.navbar.nav3 {
  .hamburger-container {
    display: none !important;
  }
}

.navbar {
  height: 66px;
  overflow: hidden;
  position: relative;
  background:
    radial-gradient(circle at 18% -20%, var(--app-yellow-soft), transparent 34%),
    linear-gradient(90deg, var(--app-primary-soft), transparent 42%),
    var(--navbar-bg);
  color: var(--navbar-text);
  border-bottom: 1px solid var(--app-border);
  backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  padding: 0 14px;
  box-sizing: border-box;

  .hamburger-container {
    line-height: 44px;
    height: 100%;
    cursor: pointer;
    transition: background 0.3s;
    -webkit-tap-highlight-color: transparent;
    display: flex;
    align-items: center;
    flex-shrink: 0;
    margin-right: 10px;
    color: var(--navbar-text);
    border-radius: 16px;

    &:hover {
      background: var(--navbar-hover, rgba(108, 63, 245, 0.08));
    }
  }

  .breadcrumb-container {
    flex-shrink: 0;
  }

  .topmenu-container {
    position: absolute;
    left: 50px;
  }

  .topbar-container {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
    overflow: hidden;
    margin-left: 8px;
  }

  .errLog-container {
    display: inline-block;
    vertical-align: top;
  }

  .right-menu {
    height: 100%;
    line-height: 66px;
    display: flex;
    align-items: center;
    margin-left: auto;

    &:focus {
      outline: none;
    }

    .right-menu-item {
      display: inline-block;
      padding: 0 8px;
      height: 40px;
      font-size: 18px;
      color: var(--app-ink-soft);
      vertical-align: text-bottom;
      border-radius: 999px;

      &.hover-effect {
        cursor: pointer;
        transition: background 0.3s;

        &:hover {
          background: var(--navbar-hover, rgba(108, 63, 245, 0.08));
        }
      }

      &.theme-switch-wrapper {
        display: flex;
        align-items: center;

        svg {
          transition: transform 0.3s;
          
          &:hover {
            transform: scale(1.15);
          }
        }
      }
    }

    .avatar-container {
      margin-right: 0px;
      padding-right: 0px;

      .avatar-wrapper {
        margin-top: 4px;
        right: 8px;
        position: relative;

        .user-avatar {
          cursor: pointer;
          width: 34px;
          height: 34px;
          border-radius: 50%;
          vertical-align: middle;
          border: 2px solid var(--app-yellow);
          box-shadow: 0 10px 24px rgba(17, 24, 39, 0.22);
        }

        i {
          cursor: pointer;
          position: absolute;
          right: -20px;
          top: 25px;
          font-size: 12px;
        }
      }
    }
  }
}

:global(.themeLight) .navbar {
  height: 72px;
  padding: 0 18px;
  background:
    radial-gradient(circle at 16% -30%, rgba(232, 215, 84, 0.2), transparent 34%),
    linear-gradient(90deg, rgba(105, 71, 242, 0.08), transparent 46%),
    rgba(255, 255, 255, 0.84);
  color: #111827;
  border-bottom-color: rgba(38, 50, 69, 0.1);

  .right-menu {
    line-height: 72px;
  }

  .hamburger-container {
    width: 42px;
    justify-content: center;
    background: rgba(38, 50, 69, 0.06);
    color: #263245;
  }
}

:global(.themeDark) .navbar {
  height: 62px;
  padding: 0 12px;
  background:
    radial-gradient(circle at 18% -24%, rgba(240, 223, 97, 0.1), transparent 32%),
    linear-gradient(90deg, rgba(155, 121, 255, 0.15), transparent 45%),
    rgba(7, 12, 22, 0.84);
  color: #f8fbff;
  border-bottom-color: rgba(255, 255, 255, 0.1);

  .right-menu {
    line-height: 62px;
  }

  .hamburger-container {
    color: #f8fbff;
  }
}

.nav-signal {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-left: 18px;
  padding: 8px 10px;
  border: 1px solid var(--app-border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.26);

  span {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--app-primary);
    box-shadow: 0 0 0 5px var(--app-primary-soft);

    &:nth-child(2) {
      background: var(--app-yellow);
      box-shadow: 0 0 0 5px rgba(232, 215, 84, 0.14);
    }

    &:nth-child(3) {
      background: var(--app-orange);
      box-shadow: 0 0 0 5px rgba(255, 155, 107, 0.14);
    }
  }
}

.nav-context {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-left: 12px;
  padding-left: 14px;
  border-left: 1px solid var(--app-border);
  line-height: 1;

  strong {
    color: var(--app-ink);
    font-size: 12px;
    font-weight: 900;
  }

  span {
    color: var(--app-muted);
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
  }
}

html.dark {
  .navbar .right-menu .right-menu-item {
    color: var(--app-ink-soft);
  }

  .nav-signal {
    background: rgba(255, 255, 255, 0.07);
  }
}

:global(.themeDark) .nav-context {
  border-left-color: rgba(255, 255, 255, 0.12);

  strong {
    color: #ffffff;
  }

  span {
    color: #aebbd0;
  }
}

:global(.themeLight) .nav-context {
  strong {
    color: #111827;
  }

  span {
    color: #64748b;
  }
}

@media (max-width: 991px) {
  .nav-context,
  .nav-signal {
    display: none;
  }
}

/* Liquid glass shell reset: stable old layout height, refreshed material. */
:global(.themeLight) .navbar {
  height: 66px;
  padding: 0 18px;
  background:
    radial-gradient(circle at 18% -34%, rgba(232, 215, 84, 0.2), transparent 34%),
    linear-gradient(90deg, rgba(255, 255, 255, 0.88), rgba(241, 248, 255, 0.72));
  border-bottom: 1px solid rgba(38, 50, 69, 0.1);

  .right-menu {
    line-height: 66px;
  }
}

:global(.themeDark) .navbar {
  height: 62px;
  padding: 0 16px;
  background:
    radial-gradient(circle at 18% -34%, rgba(240, 223, 97, 0.08), transparent 34%),
    linear-gradient(90deg, rgba(7, 12, 22, 0.9), rgba(17, 24, 39, 0.78));
  border-bottom: 1px solid rgba(255, 255, 255, 0.09);

  .right-menu {
    line-height: 62px;
  }
}
</style>
