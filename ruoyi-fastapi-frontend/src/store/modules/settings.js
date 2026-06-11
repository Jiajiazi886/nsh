import defaultSettings from '@/settings'
import { useDynamicTitle } from '@/utils/dynamicTitle'

const { sideTheme, showSettings, navType, tagsView, tagsIcon, fixedHeader, sidebarLogo, dynamicTitle, footerVisible, footerContent } = defaultSettings

const DARK_MODE_STORAGE_KEY = 'vueuse-color-scheme'
const storageSetting = JSON.parse(localStorage.getItem('layout-setting')) || ''
const defaultTheme = '#6C3FF5'
const savedTheme = storageSetting.theme === '#409EFF' ? defaultTheme : storageSetting.theme
const savedSideTheme = storageSetting.sideTheme === 'theme-dark' ? 'theme-light' : storageSetting.sideTheme

function applyLightMode() {
  document.documentElement.classList.remove('dark')
  localStorage.setItem(DARK_MODE_STORAGE_KEY, 'light')
}

applyLightMode()

const useSettingsStore = defineStore(
  'settings',
  {
    state: () => ({
      title: '',
      theme: savedTheme || defaultTheme,
      sideTheme: savedSideTheme || sideTheme,
      showSettings: showSettings,
      navType: storageSetting.navType === undefined ? navType : storageSetting.navType,
      tagsView: storageSetting.tagsView === undefined ? tagsView : storageSetting.tagsView,
      tagsIcon: storageSetting.tagsIcon === undefined ? tagsIcon : storageSetting.tagsIcon,
      fixedHeader: storageSetting.fixedHeader === undefined ? fixedHeader : storageSetting.fixedHeader,
      sidebarLogo: storageSetting.sidebarLogo === undefined ? sidebarLogo : storageSetting.sidebarLogo,
      dynamicTitle: storageSetting.dynamicTitle === undefined ? dynamicTitle : storageSetting.dynamicTitle,
      footerVisible: storageSetting.footerVisible === undefined ? footerVisible : storageSetting.footerVisible,
      footerContent: footerContent,
      isDark: false
    }),
    actions: {
      // 修改布局设置
      changeSetting(data) {
        const { key, value } = data
        if (this.hasOwnProperty(key)) {
          this[key] = value
        }
      },
      // 设置网页标题
      setTitle(title) {
        this.title = title
        useDynamicTitle()
      },
      // 保持浅色模式
      toggleTheme() {
        this.isDark = false
        this.sideTheme = 'theme-light'
        applyLightMode()
      }
    }
  })

export default useSettingsStore
