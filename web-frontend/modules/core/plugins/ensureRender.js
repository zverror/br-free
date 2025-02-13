import Vue from 'vue'
import flushPromises from 'flush-promises'

export default function (context, inject) {
  const ensureRender = async () => {
    // Ensure the dom is up to date
    await Vue.nextTick()
    // Wait until the browser has had a chance to repaint the UI
    await new Promise((resolve) => requestAnimationFrame(resolve))
    // And purge all promises created in the meantime
    await flushPromises()
  }
  inject('ensureRender', ensureRender)
}
