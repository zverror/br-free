import { getWorkspaceCookie } from '@baserow/modules/core/utils/workspace'

/**
 * This middleware will make sure that all the workspaces and applications belonging to
 * the user are fetched and added to the store.
 */
export default async function WorkspacesAndApplications({
  store,
  req,
  app,
  redirect,
}) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // Get the selected workspace id
  let workspaceId = getWorkspaceCookie(app)

  // If the workspaces haven't already been selected we will
  if (store.getters['auth/isAuthenticated']) {
    // If the workspaces haven't been loaded we will load them all.
    if (!store.getters['workspace/isLoaded']) {
      await store.dispatch('workspace/fetchAll')

      const workspaces = store.getters['workspace/getAll']
      const workspaceExists =
        workspaces.find((w) => w.id === workspaceId) !== undefined
      if (!workspaceExists) {
        workspaceId = null
      }

      // If no workspace was remembered, or the remembered workspace doesn't exist, we
      // automatically select the first one if it
      // exists.
      if (!workspaceExists && store.getters['workspace/getAll'].length > 0) {
        workspaceId = workspaces[0].id
      }

      // If there is a workspaceId cookie we will select that workspace.
      if (workspaceId) {
        try {
          await store.dispatch('workspace/selectById', workspaceId)
        } catch {}
      }
    }
    // If the applications haven't been loaded we will also load them all.
    if (!store.getters['application/isLoaded']) {
      await store.dispatch('application/fetchAll')
    }

    // If the user hasn't completed the onboarding, and the doesn't have any workspaces,
    // then redirect to the on-boarding page so that the user can create their first
    // one.
    const user = store.getters['auth/getUserObject']
    const workspaces = store.getters['workspace/getAll']
    if (!user.completed_onboarding && workspaces.length === 0) {
      return redirect({ name: 'onboarding' })
    }
  }
}
