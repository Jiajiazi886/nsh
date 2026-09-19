const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const test = require('node:test')
const vm = require('node:vm')

const projectRoot = path.resolve(__dirname, '..')

function read(relativePath) {
  return fs.readFileSync(path.join(projectRoot, relativePath), 'utf8')
}

function walk(directory, extension) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(directory, entry.name)
    if (entry.isDirectory()) return walk(target, extension)
    return target.endsWith(extension) ? [target] : []
  })
}

test('app.json registers every Demo page', () => {
  const appConfig = JSON.parse(read('app.json'))
  assert.deepEqual(appConfig.pages, [
    'pages/login/index',
    'pages/register/index',
    'pages/home/index',
    'pages/activities/index',
    'pages/guild/index',
    'pages/records/index',
    'pages/profile/index',
    'pages/guild-members/index',
    'pages/guild-join/index',
    'pages/battle-invite/index',
    'pages/schedule/index',
    'pages/activity-detail/index',
    'pages/activity-report/index',
  ])
})

test('primary functions use a five-item custom tab bar', () => {
  const appConfig = JSON.parse(read('app.json'))
  assert.equal(appConfig.tabBar.custom, true)
  assert.deepEqual(appConfig.tabBar.list.map((item) => item.text), ['首页', '活动', '帮会', '战绩', '我的'])
  assert.equal(appConfig.tabBar.list.length, 5)
  assert.match(read('custom-tab-bar/index.js'), /wx\.switchTab/)
})

test('all JavaScript files are valid scripts', () => {
  for (const filePath of walk(projectRoot, '.js')) {
    if (filePath.includes(`${path.sep}tests${path.sep}`)) continue
    assert.doesNotThrow(() => new vm.Script(fs.readFileSync(filePath, 'utf8'), { filename: filePath }))
  }
})

test('authentication uses the existing backend contracts', () => {
  const authService = read('services/auth.js')
  assert.match(authService, /getClient\(\)\.login/)
  assert.match(authService, /userName:/)
  assert.match(authService, /validateSession/)
  assert.match(authService, /url: '\/register'/)
  assert.match(authService, /url: '\/getInfo'/)
})

test('invite join uses the authenticated account endpoint', () => {
  const battleService = read('services/battle.js')
  assert.match(battleService, /\/guild\/battle-registration\/invite\/\$\{encodeURIComponent\(inviteCode\)\}\/join/)
  assert.doesNotMatch(battleService, /url: `\/public\/battle\/\$\{encodeURIComponent\(inviteCode\)\}\/join`/)
})

test('guild manager workspace uses role-scoped dashboard and member APIs', () => {
  const guildService = read('services/guild.js')
  const homePage = read('pages/home/index.js')
  assert.match(guildService, /url: '\/guild\/dashboard\/summary'/)
  assert.match(guildService, /url: '\/guild\/member\/list'/)
  assert.match(homePage, /roles\.includes\('common'\)/)
  assert.match(homePage, /permissions\.includes\('guild:member:list'\)/)
})

test('activity, guild, and records pages use existing backend modules', () => {
  const battleService = read('services/battle.js')
  const guildService = read('services/guild.js')
  const scheduleService = read('services/schedule.js')
  assert.match(battleService, /\/guild\/battle-registration\/invite\/list/)
  assert.match(battleService, /\/guild\/battle\/list/)
  assert.match(guildService, /\/guild\/join\/pending/)
  assert.match(guildService, /\/guild\/member\/guild-name/)
  assert.match(scheduleService, /\/guild\/schedule\/current/)
})

test('trial and release builds use the production API', () => {
  const envSource = read('config/env.js')
  assert.match(envSource, /\['trial', 'release'\]\.includes/)
  assert.match(envSource, /https:\/\/www\.xn--kbrr2vyxjytebq4azkrrie\.icu\/docker-api/)
})
