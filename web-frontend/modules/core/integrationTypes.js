import { Registerable } from '@baserow/modules/core/registry'

export class IntegrationType extends Registerable {
  get name() {
    throw new Error('Must be set on the type.')
  }

  /**
   * The image associated to this integration.
   */
  get image() {
    throw new Error('Must be set on the type.')
  }

  /**
   * Return a summary describing the integration in one sentence.
   *
   * @param {object} integration The integration we want the summary for.
   * @returns A string description.
   */
  getSummary(integration) {
    return this.name
  }

  /**
   * The form to edit this integration.
   */
  get formComponent() {
    return null
  }

  /**
   * An optional warning to display when editing this integration
   */
  get warning() {
    return ''
  }

  /**
   * Default values on integration creation.
   *
   * @returns an object with the default values.
   */
  getDefaultValues() {
    return {}
  }

  getOrder() {
    return 0
  }
}
