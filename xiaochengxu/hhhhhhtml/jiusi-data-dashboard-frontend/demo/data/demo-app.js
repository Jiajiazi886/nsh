const PROFESSIONS = ['铁衣', '素问', '神相', '龙吟', '碎梦', '血河', '九灵', '玄机', '潮光', '沧澜']

const NAMES = [
  '封不覺', '万斯琳', '家猫素问', '桃姿素问', '怀川', '惊鸿', '青砚', '听风',
  '云归', '墨迟', '长歌', '照夜', '观棋', '辞镜', '临川', '星河',
  '问舟', '折竹', '清商', '沉璧', '鹤归', '疏影', '照雪', '南枝',
  '砚辞', '江晚', '霜序', '停云', '既白', '栖迟', '知许', '望舒'
]

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function buildSeats(total, occupied) {
  const seats = []
  for (let index = 0; index < total; index++) {
    const filled = index < occupied
    const isPreset = filled && index > 0 && index % 13 === 0
    const isProxy = filled && !isPreset && index > 0 && index % 6 === 0
    seats.push({
      no: index + 1,
      status: !filled ? 0 : (isPreset ? 2 : 1),
      name: filled ? NAMES[index % NAMES.length] : '',
      profession: filled ? PROFESSIONS[index % PROFESSIONS.length] : '',
      hasOrangeWeapon: filled && index % 4 === 0,
      isProxy,
      proxyBy: isProxy ? '九肆指挥' : '',
      canVacate: filled && index === 1
    })
  }
  return seats
}

function activity(config) {
  const seats = buildSeats(config.totalSeats, config.occupied)
  return {
    id: config.id,
    title: config.title,
    orgType: config.orgType,
    orgName: config.orgName,
    isPublic: !!config.isPublic,
    publicRemark: config.publicRemark || '',
    status: config.status,
    startTime: config.startTime,
    endTime: config.endTime,
    totalSeats: config.totalSeats,
    seats,
    filled: seats.filter(item => item.status !== 0).length,
    canManage: config.canManage !== false,
    csv: config.csv || null
  }
}

function members() {
  return NAMES.slice(0, 18).map((name, index) => ({
    id: 'member_' + (index + 1),
    name,
    profession: PROFESSIONS[index % PROFESSIONS.length],
    role: index === 0 ? 2 : (index < 3 ? 1 : 0),
    hasOrangeWeapon: index % 4 === 0,
    team: index < 6 ? '进攻一团 · 一队' : (index < 12 ? '进攻二团 · 三队' : '防守团 · 五队')
  }))
}

function createDemoData() {
  return {
    version: 1,
    session: { loggedIn: false },
    user: {
      id: 'player_demo_1',
      name: '九肆指挥',
      server: '梦回江南',
      profession: '铁衣',
      subProfession: '素问',
      hasOrangeWeapon: true
    },
    professions: PROFESSIONS.slice(),
    organizations: [
      {
        id: 'org_jiusi',
        type: 'guild',
        name: '༺九肆✈',
        role: 2,
        roleText: '管理员',
        memberCount: 60,
        limit: 80,
        inviteCode: 'JIUSI94',
        inviteExpire: '2026-09-12 23:59',
        members: members(),
        teams: [
          { group: '进攻一团', count: 18, teams: ['一队', '二队', '三队'] },
          { group: '进攻二团', count: 18, teams: ['四队', '五队', '六队'] },
          { group: '防守团', count: 24, teams: ['七队', '八队', '九队', '十队'] }
        ]
      },
      {
        id: 'org_training',
        type: 'club',
        name: '九肆联赛训练营',
        role: 1,
        roleText: '助理',
        memberCount: 126,
        limit: 800,
        inviteCode: 'TRAIN26',
        inviteExpire: '2026-09-11 23:59',
        members: members().slice(0, 10),
        teams: []
      }
    ],
    activities: [
      activity({
        id: 'act_weekend', title: '周六帮会联赛', orgType: 'guild', orgName: '༺九肆✈',
        status: '报名中', startTime: '2026-09-12 19:00', endTime: '2026-09-12 21:00',
        totalSeats: 60, occupied: 38, canManage: true
      }),
      activity({
        id: 'act_training', title: '百人战术训练', orgType: 'club', orgName: '九肆联赛训练营',
        status: '报名中', startTime: '2026-09-13 14:00', endTime: '2026-09-13 16:30',
        totalSeats: 120, occupied: 46, canManage: true
      }),
      activity({
        id: 'act_public', title: '跨服自由约战', orgType: 'club', orgName: '云海论剑社',
        isPublic: true, publicRemark: '缺素问与铁衣，欢迎跨帮会报名。',
        status: '报名中', startTime: '2026-09-14 20:00', endTime: '2026-09-14 22:00',
        totalSeats: 60, occupied: 21, canManage: false
      }),
      activity({
        id: 'act_finished', title: '九月第一周联赛', orgType: 'guild', orgName: '༺九肆✈',
        status: '已结束', startTime: '2026-09-05 19:00', endTime: '2026-09-05 21:00',
        totalSeats: 60, occupied: 60, canManage: true,
        csv: { fileName: '20260905_九肆联赛.csv', size: 18426, uploadedAt: '2026-09-05 21:36', parsed: true }
      })
    ],
    selectedAnalysisActivityId: 'act_finished',
    notices: [
      { id: 'notice_1', tone: 'gold', text: '周六帮会联赛仍有 22 个空位' },
      { id: 'notice_2', tone: 'cyan', text: '九月第一周联赛数据已完成解析' }
    ]
  }
}

module.exports = {
  PROFESSIONS,
  clone,
  buildSeats,
  createDemoData
}
