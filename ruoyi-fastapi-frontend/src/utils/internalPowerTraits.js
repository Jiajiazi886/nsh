export const INTERNAL_POWER_TRAITS = [
  {
    name: '贯山月',
    element: '金',
    effect: '攻击时在8秒内获得7.5%全流派克制，触发期间参与击败敌方玩家可延长3秒增益时间，冷却20秒'
  },
  {
    name: '破釜',
    element: '金',
    effect: '攻击提高6%，受到伤害提高2.5%'
  },
  {
    name: '惊羽',
    element: '金',
    effect: '获得3%流派克制，自身气血降至60%以下时，在8秒内增益翻倍，冷却6秒（治疗姿态为治疗提高）'
  },
  {
    name: '锻寒芒',
    element: '金',
    effect: '会心率提高10%、会心伤害提高6.5%，造成伤害/治疗降低2.5%'
  },
  {
    name: '击衰',
    element: '金',
    effect: '攻击血量低于30%的目标时，伤害提高15%（治疗姿态为额外治疗）'
  },
  {
    name: '移星障',
    element: '木',
    effect: '对有护盾目标伤害提高12%。攻击有护盾目标时，使其在4秒内每秒损失1.5%气血上限的护盾，冷却10秒'
  },
  {
    name: '凌穹',
    element: '木',
    effect: '每释放4次流派技能，对目标造成135%倍率的伤害（对怪物伤害提高，治疗姿态为单体治疗），冷却3秒'
  },
  {
    name: '沧浪行',
    element: '木',
    effect: '释放位移技能或燕回风时，自身在5秒内获得5.4%伤害/治疗提高'
  },
  {
    name: '裁锋',
    element: '木',
    effect: '流派技能伤害提高5%，每次触发木周天减冷却效果时，对目标造成60%倍率的伤害（对怪物伤害提高，治疗姿态为单体治疗）'
  },
  {
    name: '破重云',
    element: '木',
    effect: '攻击时造成150%倍率的范围伤害（对怪物伤害提高），并提高4%首领克制和对建筑伤害提高，冷却12秒，若命中目标大于2个则冷却减半（治疗姿态为范围治疗与治疗提高）'
  },
  {
    name: '珠明',
    element: '水',
    effect: '释放技能时获得治疗光环，10秒内每2秒治疗周围30丈内队友600%倍率的气血，冷却20秒'
  },
  {
    name: '望惊川',
    element: '水',
    effect: '释放技能时给自身和30丈内的选中队友施加2%首领克制增益，持续10秒，冷却3秒（治疗姿态为治疗提高，增益不可叠加）'
  },
  {
    name: '鲸落',
    element: '水',
    effect: '周围25丈内队友攻击提高1.8%，自身获得双倍效果'
  },
  {
    name: '沉浪',
    element: '水',
    effect: '周天·水增益额外获得1.2%伤害/治疗提高与减伤，作用范围提高至32丈'
  },
  {
    name: '噬汐',
    element: '水',
    effect: '释放技能时给自身和血量最低的队友施加4.5%最大气血的护盾，持续10秒，若无队友则自身效果提高60%（同一目标在10秒内只能获得一次噬汐护盾）'
  },
  {
    name: '楚狂歌',
    element: '火',
    effect: '周围每有一个敌方玩家，获得1.35%流派克制，最多提高5.4%（治疗姿态下为治疗提高）'
  },
  {
    name: '斩精',
    element: '火',
    effect: '攻击血量高于50%的目标时，伤害提高9%（治疗姿态为额外治疗），并且施加21%重创效果'
  },
  {
    name: '众妙',
    element: '火',
    effect: '攻击时造成每秒30%倍率的范围周期性灼烧（对怪物伤害提高，治疗姿态为持续治疗），并对被灼烧目标伤害提高1.5%'
  },
  {
    name: '燎原',
    element: '火',
    effect: '周天·火叠层时，每层额外获得1.1%首领克制（最高5层，获得5.5%），脱战后移除增益（治疗姿态为治疗提高）'
  },
  {
    name: '焚刃',
    element: '火',
    effect: '参与击败玩家时获得1层0.3%流派克制（造成击败或助攻获得1层），最高可叠加24层（最高7.2%），被击败后层数减少60%'
  },
  {
    name: '征袍',
    element: '土',
    effect: '战斗状态下，每隔10秒给自身施加6%最大气血的护盾且拥有护盾时获得3%受治疗提高'
  },
  {
    name: '御千嶂',
    element: '土',
    effect: '获得12%会心防御提高。受到单次伤害大于自身气血上限的20%时，减免本次伤害的24%，冷却10秒'
  },
  {
    name: '固垒',
    element: '土',
    effect: '减伤提高6%，造成伤害/治疗降低2.5%'
  },
  {
    name: '覆沙阙',
    element: '土',
    effect: '周围25丈内队友获得1.5%减伤，自身获得双倍效果'
  },
  {
    name: '纳百观',
    element: '土',
    effect: '受击时提高自身1.5%伤害/治疗并叠层，5层触发反击：回复6%最大气血并在5秒内获得双倍增益（进入格挡状态时，立即触发反击），冷却10秒'
  },
  {
    name: '五韵谣',
    element: '金木水火土',
    effect: '伤害/治疗提高2%，激活每级内功周天所需元素数量减少1个，元素数量达到3/6/9个即可激活1/2/3级周天'
  },
  {
    name: '稀有-日月两仪',
    element: ['火', '土'],
    effect: '气血大于50%时，造成伤害（治疗）效果提高5.6%；气血低于50%时，受到伤害降低5.6%',
    lingyunEffect: '获得<灵韵>效果后，增伤/减伤效果提高2.5%'
  },
  {
    name: '稀有-不动明王',
    element: ['木', '水'],
    effect: '解控技能冷却时，获得常驻4%减伤。使用解控技能时，回复自身4%最大气血，冷却15秒',
    lingyunEffect: '获得<灵韵>效果后，减伤与气血回复提高50%'
  },
  {
    name: '稀有-绝电惊沙',
    element: ['金', '木'],
    effect: '攻击时在4秒内对目标造成每秒105%倍率的伤害（对怪物伤害提高，治疗姿态为持续治疗），冷却10秒，对半血以下目标伤害额外提高15%',
    lingyunEffect: '获得<灵韵>效果后，冷却降至7.5秒，额外伤害提升至30%'
  },
  {
    name: '稀有-承影锋烁',
    element: ['金', '火'],
    effect: '激活承影武学时提高4%伤害/治疗，承影追击与共鸣伤害/治疗提高30%',
    lingyunEffect: '获得<灵韵>效果后，增益与额外伤害均提高50%'
  },
  {
    name: '稀有-灼星贯日',
    element: ['木', '火'],
    effect: '内功周天和特性中造成的伤害/治疗提高20%。攻击时对目标造成每秒30%倍率的周期性伤害（对怪物伤害提高，治疗姿态为治疗）',
    lingyunEffect: '获得<灵韵>效果后，增益与伤害效果均提高50%'
  }
]

const traitMap = new Map(INTERNAL_POWER_TRAITS.map(item => [normalizeTraitName(item.name), item]))

export function findInternalPowerTrait(name) {
  const normalizedName = normalizeTraitName(name)
  return traitMap.get(normalizedName) || traitMap.get(normalizeTraitName(stripElementSuffix(normalizedName))) || null
}

export function getInternalPowerTraitEffect(name) {
  return findInternalPowerTrait(name)?.effect || ''
}

function normalizeTraitName(name) {
  return String(name || '').trim().replace(/[（(](金|木|水|火|土|全元素|金木水火土)[）)]$/u, '')
}

function stripElementSuffix(name) {
  return String(name || '').replace(/[（(].*?[）)]$/u, '')
}
