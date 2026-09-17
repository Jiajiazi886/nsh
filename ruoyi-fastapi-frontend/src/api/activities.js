import '@/utils/nshApiSdk.js'
import { getToken } from '@/utils/auth'
const prefix=import.meta.env.VITE_APP_BASE_API || '/dev-api'
// Same SDK as wx; deployment proxy is a root, never a second activity backend.
export const activityApi=globalThis.NshApi.createClient({baseUrl: /^https?:/.test(prefix) ? prefix : window.location.origin+prefix, getToken, transport:globalThis.NshApi.createFetchTransport(window.fetch.bind(window))})
