export default (client) => {
  return {
    create(builderId, name, path, pathParams = {}) {
      return client.post(`builder/${builderId}/pages/`, {
        name,
        path,
        path_params: pathParams,
      })
    },
    update(pageId, values) {
      return client.patch(`builder/pages/${pageId}/`, values)
    },
    delete(pageId) {
      return client.delete(`builder/pages/${pageId}/`)
    },
    order(builderId, order) {
      return client.post(`/builder/${builderId}/pages/order/`, {
        page_ids: order,
      })
    },
    duplicate(pageId) {
      return client.post(`/builder/pages/${pageId}/duplicate/async/`)
    },
  }
}
