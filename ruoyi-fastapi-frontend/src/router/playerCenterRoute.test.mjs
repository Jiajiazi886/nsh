import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import {PLAYER_CENTER_PATH,legacyProfileRedirect} from './playerCenterLinks.mjs'
test('self player center has a stable authenticated route independent of guild/menu grants',()=>{
 const router=fs.readFileSync(new URL('./index.js',import.meta.url),'utf8')
 assert.match(router,/path: '\/personal\/profile-edit'/)
 assert.match(router,/AccountPlayerCenter/)
 assert.match(router,/@\/views\/personal\/profileEdit\/index.vue/)
})

test('legacy profile routes and avatar use the sole player center, retaining password deep links',()=>{
 const router=fs.readFileSync(new URL('./index.js',import.meta.url),'utf8')
 const navbar=fs.readFileSync(new URL('../layout/components/Navbar.vue',import.meta.url),'utf8')
 assert.match(router,/redirect:\s*legacyProfileRedirect/)
 assert.doesNotMatch(router,/@\/views\/system\/user\/profile\/index/)
 assert.match(navbar,/:to="PLAYER_CENTER_PATH"/)
 assert.equal(PLAYER_CENTER_PATH,'/personal/profile-edit')
 assert.deepEqual(legacyProfileRedirect({query:{from:'avatar'},params:{},hash:'#profile'}),{path:PLAYER_CENTER_PATH,query:{from:'avatar'},hash:'#profile'})
 assert.deepEqual(legacyProfileRedirect({query:{},params:{activeTab:'resetPwd'}}),{path:PLAYER_CENTER_PATH,query:{security:'password'},hash:undefined})
})
