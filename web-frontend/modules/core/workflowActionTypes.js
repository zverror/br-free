import { Registerable } from '@baserow/modules/core/registry'

export class WorkflowActionType extends Registerable {
  get form() {
    return null
  }

  get label() {
    return null
  }

  /**
   * This function executes the action. This can happen in the frontend but also in the
   * backend, depending on what your action does.
   *
   * @param context {object} - Any additional information the action needs to execute
   * @returns {Promise<any> | void}
   */
  async execute(context) {
    return await Promise.resolve()
  }

  /**
   * Should return a JSON schema of the data returned by this workflow action.
   */
  getDataSchema(applicationContext, workflowAction) {
    throw new Error('Must be set on the type.')
  }
}
