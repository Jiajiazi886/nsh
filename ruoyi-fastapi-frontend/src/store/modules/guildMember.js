import { getMemberList } from '@/api/guild/member'
import { getToken } from '@/utils/auth'

const MEMBER_CACHE_SESSION_KEY = '__guildMemberCacheSession__'
const MEMBER_CACHE_STORAGE_KEY = 'guild-member-list-cache:v1'

function canUseSessionStorage() {
  return typeof window !== 'undefined' && Boolean(window.sessionStorage)
}

function readStoredMemberCache(token) {
  if (!token || !canUseSessionStorage()) return null
  try {
    const raw = window.sessionStorage.getItem(MEMBER_CACHE_STORAGE_KEY)
    if (!raw) return null
    const cache = JSON.parse(raw)
    if (cache?.token !== token || !Array.isArray(cache.list)) return null
    return cache
  } catch {
    return null
  }
}

function writeStoredMemberCache(token, list) {
  if (!token || !canUseSessionStorage()) return
  try {
    window.sessionStorage.setItem(MEMBER_CACHE_STORAGE_KEY, JSON.stringify({
      token,
      list,
      cachedAt: Date.now()
    }))
  } catch {
    // sessionStorage may be unavailable in private browsing or quota-limited contexts.
  }
}

function clearStoredMemberCache() {
  if (!canUseSessionStorage()) return
  try {
    window.sessionStorage.removeItem(MEMBER_CACHE_STORAGE_KEY)
  } catch {
    // no-op
  }
}

function getCacheSession() {
  const target = typeof window === 'undefined' ? globalThis : window
  if (!target[MEMBER_CACHE_SESSION_KEY]) {
    target[MEMBER_CACHE_SESSION_KEY] = {
      pendingMemberListPromise: null,
      pendingMemberListToken: '',
      pendingPreloadPromise: null,
      pendingPreloadToken: '',
      memberListRequestSeq: 0,
      visibleLoadingRequests: 0
    }
  }
  return target[MEMBER_CACHE_SESSION_KEY]
}

function hasMemberListPermission(permissions = []) {
  return permissions.includes('*:*:*') || permissions.includes('guild:member:list')
}

function beginVisibleLoading(store, silent) {
  if (silent) return
  const session = getCacheSession()
  session.visibleLoadingRequests += 1
  store.loading = true
}

function endVisibleLoading(store, silent) {
  if (silent) return
  const session = getCacheSession()
  session.visibleLoadingRequests = Math.max(0, session.visibleLoadingRequests - 1)
  store.loading = session.visibleLoadingRequests > 0
}

function clearPendingRequest(session) {
  session.pendingMemberListPromise = null
  session.pendingMemberListToken = ''
  session.pendingPreloadPromise = null
  session.pendingPreloadToken = ''
}

function buildInitialState() {
  const token = getToken() || ''
  const storedCache = readStoredMemberCache(token)
  if (storedCache) {
    return {
      list: storedCache.list,
      loaded: true,
      loadedToken: token,
      lastLoadedAt: storedCache.cachedAt || Date.now(),
      loading: false
    }
  }
  return {
    list: [],
    loaded: false,
    loadedToken: '',
    lastLoadedAt: 0,
    loading: false
  }
}

const useGuildMemberStore = defineStore(
  'guildMember',
  {
    state: buildInitialState,
    getters: {
      members(state) {
        return state.list
      },
      hasReadyCache(state) {
        return state.loaded && state.loadedToken === (getToken() || '')
      }
    },
    actions: {
      reset() {
        const session = getCacheSession()
        clearPendingRequest(session)
        session.memberListRequestSeq += 1
        session.visibleLoadingRequests = 0
        this.list = []
        this.loaded = false
        this.loadedToken = ''
        this.lastLoadedAt = 0
        this.loading = false
        clearStoredMemberCache()
      },
      async load(options = {}) {
        const force = options.force === true
        const silent = options.silent === true
        const throwOnError = options.throwOnError === true
        const token = getToken() || ''

        if (!token) {
          this.reset()
          return []
        }

        if (!force && this.loaded && this.loadedToken === token) {
          return this.list
        }

        const session = getCacheSession()

        if (
          session.pendingMemberListPromise &&
          session.pendingMemberListToken === token &&
          !force
        ) {
          beginVisibleLoading(this, silent)
          return session.pendingMemberListPromise
            .then(list => {
              if (!this.loaded || this.loadedToken !== token) {
                this.list = list
                this.loaded = true
                this.loadedToken = token
                this.lastLoadedAt = Date.now()
              }
              return this.list
            })
            .catch(error => {
              if (!silent || throwOnError) {
                throw error
              }
              return this.list
            })
            .finally(() => {
              endVisibleLoading(this, silent)
            })
        }

        beginVisibleLoading(this, silent)

        const requestSeq = ++session.memberListRequestSeq
        session.pendingMemberListToken = token
        session.pendingMemberListPromise = getMemberList()
          .then(res => {
            const list = res.data || []
            if (requestSeq === session.memberListRequestSeq) {
              this.list = list
              this.loaded = true
              this.loadedToken = token
              this.lastLoadedAt = Date.now()
              writeStoredMemberCache(token, list)
            }
            return list
          })
          .finally(() => {
            if (requestSeq === session.memberListRequestSeq) {
              session.pendingMemberListPromise = null
              session.pendingMemberListToken = ''
            }
            endVisibleLoading(this, silent)
          })

        return session.pendingMemberListPromise.catch(error => {
          if (!silent || throwOnError) {
            throw error
          }
          return this.list
        })
      },
      refresh(options = {}) {
        return this.load({ ...options, force: true })
      },
      preloadAfterLogin(permissions = []) {
        if (!hasMemberListPermission(permissions)) {
          return Promise.resolve(this.list)
        }
        const token = getToken() || ''
        if (!token) {
          this.reset()
          return Promise.resolve([])
        }
        if (this.loaded && this.loadedToken === token) {
          return Promise.resolve(this.list)
        }
        const session = getCacheSession()
        if (session.pendingPreloadPromise && session.pendingPreloadToken === token) {
          return session.pendingPreloadPromise
        }
        session.pendingPreloadToken = token
        session.pendingPreloadPromise = this.load({ silent: true })
          .catch(() => this.list)
          .finally(() => {
            if (session.pendingPreloadToken === token) {
              session.pendingPreloadPromise = null
              session.pendingPreloadToken = ''
            }
          })
        return session.pendingPreloadPromise
      },
      handleMembersChanged() {
        this.loaded = false
        this.loadedToken = ''
        if (!getToken()) {
          this.reset()
          return Promise.resolve([])
        }
        return this.refresh({ silent: true }).catch(() => this.list)
      }
    }
  }
)

export default useGuildMemberStore
