import { isSecureURL } from '@baserow/modules/core/utils/string'
import jwtDecode from 'jwt-decode'
import { getDomain } from 'tldjs'

const cookieTokenName = 'jwt_token'
export const userSourceCookieTokenName = 'user_source_token'
export const userSessionCookieName = 'user_session'
const refreshTokenMaxAge = 60 * 60 * 24 * 7

export const setToken = (
  { $config, $cookies },
  token,
  key = cookieTokenName,
  configuration = { sameSite: null }
) => {
  if (process.SERVER_BUILD) return
  const secure = isSecureURL($config.PUBLIC_WEB_FRONTEND_URL)
  $cookies.set(key, token, {
    path: '/',
    maxAge: refreshTokenMaxAge,
    sameSite:
      configuration.sameSite || $config.BASEROW_FRONTEND_SAME_SITE_COOKIE,
    secure,
  })
}

/**
 * Sets a session cookie in the browser to store the user's signed session payload upon
 * login. This cookie facilitates backend authentication for GET requests, such as
 * downloading files with the secure_file_serve feature, when the Authorization header
 * is unavailable. The payload includes a token hash to invalidate the cookie upon
 * logout.
 *
 * @param {*} app: the nuxt app instance
 * @param {*} signedUserSession: the signed user session payload to be stored in the
 * cookie
 * @param {*} key: the cookie name
 * @param {*} configuration: the configuration object with the sameSite key
 * @returns
 */
export const setUserSessionCookie = (
  { $config, $cookies },
  signedUserSession,
  key = userSessionCookieName,
  configuration = { sameSite: null }
) => {
  if (process.SERVER_BUILD) return
  const secure = isSecureURL($config.PUBLIC_WEB_FRONTEND_URL)

  // To make the cookie available to all subdomains, set the domain to the top-level
  // domain. This is necessary for the secure_file_serve feature to work across
  // subdomains, as when the backend serves files from a different subdomain from the
  // frontend. The top-level domain is extracted from the backend URL.
  // NOTE: For security reasons, it's not possible to set a cookie for a different
  // domain, so this won't work if the frontend and backend are on different domains.
  const topLevelDomain = getDomain($config.PUBLIC_BACKEND_URL)

  $cookies.set(key, signedUserSession, {
    path: '/',
    maxAge: refreshTokenMaxAge,
    sameSite:
      configuration.sameSite || $config.BASEROW_FRONTEND_SAME_SITE_COOKIE,
    secure,
    domain: topLevelDomain,
  })
}

export const unsetToken = ({ $cookies }, key = cookieTokenName) => {
  if (process.SERVER_BUILD) return
  $cookies.remove(key)
}

export const unsetUserSessionCookie = (
  { $cookies },
  key = userSessionCookieName
) => {
  if (process.SERVER_BUILD) return
  $cookies.remove(key)
}

export const getToken = ({ $cookies }, key = cookieTokenName) => {
  return $cookies.get(key)
}

export const getTokenIfEnoughTimeLeft = (
  { $cookies },
  key = cookieTokenName
) => {
  const token = getToken({ $cookies }, key)
  const now = Math.ceil(new Date().getTime() / 1000)

  let data
  try {
    data = jwtDecode(token)
  } catch (error) {
    return null
  }
  // Return the token if it is still valid for more of the 10% of the lifespan.
  return data && (data.exp - now) / (data.exp - data.iat) > 0.1 ? token : null
}

export const logoutAndRedirectToLogin = (
  router,
  store,
  showSessionExpiredToast = false,
  showPasswordChangedToast = false,
  invalidateToken = false
) => {
  if (showPasswordChangedToast) {
    store.dispatch('auth/forceLogoff')
  } else {
    store.dispatch('auth/logoff', { invalidateToken })
  }
  router.push({ name: 'login', query: { noredirect: null } }, () => {
    if (showSessionExpiredToast) {
      store.dispatch('toast/setUserSessionExpired', true)
    } else if (showPasswordChangedToast) {
      store.dispatch('toast/setUserPasswordChanged', true)
    }
    store.dispatch('auth/clearAllStoreUserData')
  })
}
