export const PLAYER_CENTER_PATH = '/personal/profile-edit'

export function legacyProfileRedirect(route) {
  const query = {...route.query}
  if (route.params?.activeTab === 'resetPwd') query.security = 'password'
  return {path: PLAYER_CENTER_PATH, query, hash: route.hash}
}
