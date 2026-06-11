import { nextTick, onBeforeUnmount, onMounted } from 'vue'

let gsapLoader = null

async function loadGsap() {
  if (!gsapLoader) {
    gsapLoader = import('gsap').then(gsapModule => {
      const gsap = gsapModule.gsap || gsapModule.default || gsapModule
      return { gsap }
    })
  }
  return gsapLoader
}

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

export function useGuildPageMotion(rootRef, options = {}) {
  let ctx = null
  let disposed = false

  onMounted(async () => {
    await nextTick()
    const root = rootRef.value
    if (!root || prefersReducedMotion()) return

    const { gsap } = await loadGsap()
    if (disposed) return

    const heroSelector = options.heroSelector || '[data-guild-motion="hero"]'
    const revealSelector = options.revealSelector || '[data-guild-reveal]'

    ctx = gsap.context(() => {
      const query = gsap.utils.selector(root)
      const hero = query(heroSelector)
      const revealItems = query(revealSelector)

      if (hero.length) {
        gsap.from(hero, {
          autoAlpha: 0,
          y: 14,
          duration: 0.36,
          ease: 'power2.out',
          clearProps: 'transform,opacity,visibility'
        })
      }

      if (!revealItems.length) return

      gsap.from(revealItems, {
        autoAlpha: 0,
        y: 12,
        duration: 0.28,
        ease: 'power2.out',
        stagger: 0.025,
        clearProps: 'transform,opacity,visibility'
      })
    }, root)
  })

  onBeforeUnmount(() => {
    disposed = true
    ctx?.revert()
    ctx = null
  })
}
