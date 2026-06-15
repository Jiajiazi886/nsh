import { nextTick, onActivated, onBeforeUnmount, onMounted } from 'vue'

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

function getMotionScroller(root, configuredScroller) {
  if (configuredScroller) {
    return typeof configuredScroller === 'function' ? configuredScroller(root) : configuredScroller
  }
  return root.closest?.('.app-main') || window
}

function revealImmediately(root, selector) {
  const items = root?.querySelectorAll?.(selector)
  if (!items?.length) return

  items.forEach(item => {
    item.style.opacity = ''
    item.style.visibility = ''
    item.style.transform = ''
  })
}

export function useGuildPageMotion(rootRef, options = {}) {
  let ctx = null
  let disposed = false
  let ScrollTriggerRef = null
  let fallbackTimer = null

  const revealSelector = options.revealSelector || '[data-guild-reveal]'

  function clearFallbackTimer() {
    if (!fallbackTimer) return
    window.clearTimeout(fallbackTimer)
    fallbackTimer = null
  }

  function scheduleRevealFallback(root) {
    clearFallbackTimer()
    fallbackTimer = window.setTimeout(() => {
      if (disposed) return
      revealImmediately(root, revealSelector)
      ScrollTriggerRef?.refresh()
    }, options.fallbackDelay ?? 1200)
  }

  onMounted(async () => {
    await nextTick()
    const root = rootRef.value
    if (!root) return
    if (prefersReducedMotion()) {
      revealImmediately(root, revealSelector)
      return
    }

    try {
      const { gsap, ScrollTrigger } = await loadGsap()
      if (disposed) return

      ScrollTriggerRef = ScrollTrigger
      const heroSelector = options.heroSelector || '[data-guild-motion="hero"]'

      ctx = gsap.context(() => {
        const query = gsap.utils.selector(root)
        const hero = query(heroSelector)
        const revealItems = query(revealSelector)
        const scroller = getMotionScroller(root, options.scroller)

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
        scheduleRevealFallback(root)

        ScrollTrigger.batch(revealItems, {
          scroller,
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
    } catch (error) {
      console.warn('[guild-motion] reveal fallback used:', error)
      revealImmediately(root, revealSelector)
    }
  })

  onActivated(() => {
    nextTick(() => {
      const root = rootRef.value
      if (!root) return
      ScrollTriggerRef?.refresh()
      scheduleRevealFallback(root)
    })
  })

  onBeforeUnmount(() => {
    disposed = true
    clearFallbackTimer()
    ctx?.revert()
    ctx = null
  })
}
