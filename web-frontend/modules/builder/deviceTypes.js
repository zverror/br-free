import { Registerable } from '@baserow/modules/core/registry'

export class DeviceType extends Registerable {
  get iconClass() {
    return null
  }

  getOrder() {
    return null
  }

  get minWidth() {
    return 0
  }

  get maxWidth() {
    return 0
  }
}

export class DesktopDeviceType extends DeviceType {
  static getType() {
    return 'desktop'
  }

  get iconClass() {
    return 'iconoir-apple-imac-2021'
  }

  getOrder() {
    return 1
  }

  get minWidth() {
    return 1100
  }

  get maxWidth() {
    return null // Can be as wide as you want
  }
}

export class TabletDeviceType extends DeviceType {
  static getType() {
    return 'tablet'
  }

  get iconClass() {
    return 'baserow-icon-tablet'
  }

  getOrder() {
    return 2
  }

  get minWidth() {
    return 768
  }

  get maxWidth() {
    return 768
  }
}

export class SmartphoneDeviceType extends DeviceType {
  static getType() {
    return 'smartphone'
  }

  get iconClass() {
    return 'baserow-icon-smartphone'
  }

  getOrder() {
    return 3
  }

  get minWidth() {
    return 420
  }

  get maxWidth() {
    return 420
  }
}
