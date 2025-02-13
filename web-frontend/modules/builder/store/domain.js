import DomainService from '@baserow/modules/builder/services/domain'

const populateDomain = (domain) => {
  domain._ = {
    loading: false,
  }
  if (domain.last_published) {
    domain.last_published = new Date(domain.last_published)
  }
  return domain
}

const state = {
  domains: [],
}

const mutations = {
  SET_ITEMS(state, { domains }) {
    state.domains = domains.map(populateDomain)
  },
  UPDATE_ITEM(state, { domainId, values }) {
    state.domains.forEach((domain) => {
      if (domain.id === domainId) {
        Object.assign(domain, values)
      }
    })
  },
  CLEAR_ITEMS(state) {
    state.domains = []
  },
  ADD_ITEM(state, { domain }) {
    state.domains.push(populateDomain(domain))
  },
  SET_ITEM_LOADING(state, { domainId, value }) {
    const domain = state.domains.find((domain) => domain.id === domainId)
    domain._.loading = value
  },
  DELETE_ITEM(state, { domainId }) {
    const index = state.domains.findIndex((domain) => domain.id === domainId)
    state.domains.splice(index, 1)
  },
}

const actions = {
  forceUpdate({ commit }, { domainId, values }) {
    commit('UPDATE_ITEM', { domainId, values })
  },
  async fetch({ commit }, { builderId }) {
    commit('CLEAR_ITEMS')

    const { data: domains } = await DomainService(this.$client).fetchAll(
      builderId
    )

    commit('SET_ITEMS', { domains })
  },
  async create({ commit }, { builderId, type, ...data }) {
    const { data: domain } = await DomainService(this.$client).create(
      builderId,
      { type, ...data }
    )

    commit('ADD_ITEM', { domain })
  },
  async delete({ commit }, { domainId }) {
    commit('SET_ITEM_LOADING', { domainId, value: true })

    try {
      await DomainService(this.$client).delete(domainId)
    } catch (e) {
      commit('SET_ITEM_LOADING', { domainId, value: false })
      throw e
    }

    commit('DELETE_ITEM', { domainId })
  },
}

const getters = {
  getDomains(state) {
    return state.domains
  },
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters,
}
