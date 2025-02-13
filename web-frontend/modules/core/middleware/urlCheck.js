function isValidHttpUrl(rawString) {
  try {
    const url = new URL(rawString)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch (_) {
    return false
  }
}

function invalidUrlEnvVariable(envVariableName) {
  /**
   * This function lets us check on startup that a provided environment variable is
   * a valid url. If we didn't do this then whenever the user would try to send a
   * HTTP request they would get a mysterious 500 error raised by the http client.
   *
   * @type {string}
   */

  const envValue = process.env[envVariableName]
  return envValue && !isValidHttpUrl(envValue)
}
/**
 * This middleware makes sure that the current user is admin else a 403 error
 * will be shown to the user.
 */
export default function ({ store, req, error, i18n }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  if (process.server && !process.env.BASEROW_DISABLE_PUBLIC_URL_CHECK) {
    const urlEnvVarsToCheck = []
    if (process.env.BASEROW_PUBLIC_URL) {
      urlEnvVarsToCheck.push('BASEROW_PUBLIC_URL')
    } else {
      urlEnvVarsToCheck.push('PUBLIC_BACKEND_URL', 'PUBLIC_WEB_FRONTEND_URL')
    }

    for (const name of urlEnvVarsToCheck) {
      if (invalidUrlEnvVariable(name)) {
        // noinspection HttpUrlsUsage
        return error({
          statusCode: 500,
          hideBackButton: true,
          message: i18n.t('urlCheck.invalidUrlEnvVarTitle', { name }),
          content: i18n.t('urlCheck.invalidUrlEnvVarDescription', { name }),
        })
      }
    }
  }
}
