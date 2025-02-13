/**
 * If this middleware is added to a page, it will load the pending jobs
 * for the user from the server in order to show them in the UI.
 */
export default async function ({ req, store }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  if (
    // If the user is not authenticated we can't fetch unfinished jobs.
    store.getters['auth/isAuthenticated'] &&
    //  If the unfinished jobs haven't been loaded we will load them all.
    !store.getters['job/isLoaded'] &&
    !store.getters['job/isLoading']
  ) {
    await store.dispatch('job/fetchAllUnfinished')
  }
}
