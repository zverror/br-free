import { TestApp } from '@baserow/test/helpers/testApp'

describe('Auth store', () => {
  let testApp = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
    store = testApp.store
    const fakeUserData = {
      user: {
        id: 256,
      },
      access_token:
        `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImpvaG5AZXhhb` +
        `XBsZS5jb20iLCJpYXQiOjE2NjAyOTEwODYsImV4cCI6MTY2MDI5NDY4NiwianRpIjo` +
        `iNDZmNzUwZWUtMTJhMS00N2UzLWJiNzQtMDIwYWM4Njg3YWMzIiwidXNlcl9pZCI6M` +
        `iwidXNlcl9wcm9maWxlX2lkIjpbMl0sIm9yaWdfaWF0IjoxNjYwMjkxMDg2fQ.RQ-M` +
        `NQdDR9zTi8CbbQkRrwNsyDa5CldQI83Uid1l9So`,
    }
    store.dispatch('auth/forceSetUserData', {
      ...fakeUserData,
    })
  })

  afterEach(() => {
    testApp.afterEach()
  })

  test('can update a users additional data', () => {
    store.dispatch('auth/forceUpdateUserData', {
      active_licenses: {
        per_workspace: { workspaceId: { test: true } },
      },
    })
    const additionalData = store.getters['auth/getAdditionalUserData']
    expect(JSON.parse(JSON.stringify(additionalData))).toStrictEqual({
      active_licenses: {
        per_workspace: { workspaceId: { test: true } },
      },
    })
  })

  test('updating a users additional data merges with existing values', () => {
    store.dispatch('auth/forceUpdateUserData', {
      active_licenses: {
        per_workspace: { workspaceId: { test: true } },
      },
    })
    store.dispatch('auth/forceUpdateUserData', {
      active_licenses: {
        per_workspace: { workspaceId: { otherKey: true } },
      },
    })
    const additionalData = store.getters['auth/getAdditionalUserData']
    expect(JSON.parse(JSON.stringify(additionalData))).toStrictEqual({
      active_licenses: {
        per_workspace: { workspaceId: { test: true, otherKey: true } },
      },
    })
  })

  test('updating a users additional data overrides arrays', () => {
    store.dispatch('auth/forceUpdateUserData', {
      array_data: [1, 2, 3],
    })
    store.dispatch('auth/forceUpdateUserData', {
      array_data: [3, 4, 5],
    })
    const additionalData = store.getters['auth/getAdditionalUserData']
    expect(JSON.parse(JSON.stringify(additionalData))).toStrictEqual({
      array_data: [3, 4, 5],
    })
  })
  test('updating a users additional data can set to false', () => {
    store.dispatch('auth/forceUpdateUserData', {
      active_licenses: { instance_wide: { premium: true } },
    })
    store.dispatch('auth/forceUpdateUserData', {
      active_licenses: {
        instance_wide: { premium: false },
      },
    })
    const additionalData = store.getters['auth/getAdditionalUserData']
    expect(JSON.parse(JSON.stringify(additionalData))).toStrictEqual({
      active_licenses: {
        instance_wide: { premium: false },
      },
    })
  })
})
