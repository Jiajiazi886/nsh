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
    'pages/guild-join/index',
    'pages/battle-invite/index',
    'pages/schedule/index',
    'pages/profile/index',
  ])
})

test('all JavaScript files are valid scripts', () => {
  for (const filePath of walk(projectRoot, '.js')) {
    if (filePath.includes(`${path.sep}tests${path.sep}`)) continue
    assert.doesNotThrow(() => new vm.Script(fs.readFileSync(filePath, 'utf8'), { filename: filePath }))
  }
})

test('authentication uses the existing backend contracts', () => {
  const authService = read('services/auth.js')
  assert.match(authService, /url: '\/login'/)
  assert.match(authService, /form: true/)
  assert.match(authService, /url: '\/register'/)
  assert.match(authService, /url: '\/getInfo'/)
})

test('invite join uses the authenticated account endpoint', () => {
  const battleService = read('services/battle.js')
  assert.match(battleService, /\/guild\/battle-registration\/invite\/\$\{encodeURIComponent\(inviteCode\)\}\/join/)
  assert.doesNotMatch(battleService, /url: `\/public\/battle\/\$\{encodeURIComponent\(inviteCode\)\}\/join`/)
})

test('trial and release builds use the production API', () => {
  const envSource = read('config/env.js')
  assert.match(envSource, /\['trial', 'release'\]\.includes/)
  assert.match(envSource, /https:\/\/www\.xn--kbrr2vyxjytebq4azkrrie\.icu\/prod-api/)
})
