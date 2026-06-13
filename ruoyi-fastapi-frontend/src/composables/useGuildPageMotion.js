import { nextTick, onBeforeUnmount, onMounted } from 'vue'

let gsapLoader = null

async function loadGsap() {
  if (!gsapLoader) {
    gsapLoader = import('gsap').then(async gsapModule => {
      const gsap = gsapModule.gsap || gsapModule.default || gsapModule
      const scrollModule = await import('gsap/ScrollTrigger')
      const ScrollTrigger = scrollModule.ScrollTrigger || scrollModule.default
      gsap.registerPlugin(ScrollTrigger)
      return { gsap, ScrollTrigger }
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

    const { gsap, ScrollTrigger } = await loadGsap()
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

      gsap.set(revealItems, { autoAlpha: 0, y: 10 })

      ScrollTrigger.batch(revealItems, {
        start: 'top 94%',
        once: true,
        interval: 0.08,
        batchMax: 6,
        onEnter: batch => {
          if (disposed) return
          gsap.to(batch, {
            autoAlpha: 1,
            y: 0,
            duration: 0.24,
            ease: 'power2.out',
            stagger: 0.025,
            overwrite: true,
            clearProps: 'transform,opacity,visibility'
          })
        }
      })

      requestAnimationFrame(() => ScrollTrigger.refresh())
    }, root)
  })

  onBeforeUnmount(() => {
    disposed = true
    ctx?.revert()
    ctx = null
  })
}
