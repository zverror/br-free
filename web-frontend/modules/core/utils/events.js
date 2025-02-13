/*
  This function is a helper which determines whether the pressed key
  is 'not a Control Key Character'
  thereby determining if the key is a 'printable character'.
  Any key combination with a control or a meta key is NOT a
  'printable character' thereby making it possible to use combinations
  such as CTRL+C/CTRL+V.
*/
export function isPrintableUnicodeCharacterKeyPress(event) {
  if (event == null || isOsSpecificModifierPressed(event)) {
    return false
  }
  const { key } = event

  const nonControlCharacterRegex = /^\P{C}$/iu
  if (nonControlCharacterRegex.test(key)) {
    return true
  }
  return false
}

/**
 * This function is a helper which determines whether the pressed key
 * is the CMD key on Mac or the CTRL key on Windows/Linux.
 */
export const isOsSpecificModifierPressed = (event) => {
  const isMac = navigator.platform.toUpperCase().includes('MAC')
  return isMac ? event.metaKey : event.ctrlKey
}

export const keyboardShortcutsToPriorityEventBus = (event, priorityBus) => {
  if (
    isOsSpecificModifierPressed(event) &&
    event.shiftKey &&
    event.key.toLowerCase() === 's'
  ) {
    priorityBus.$emit('start-search', { event })
  }
}
