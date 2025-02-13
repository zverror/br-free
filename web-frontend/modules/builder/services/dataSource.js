import { callGrouper } from '@baserow/modules/core/utils/function'

const GRACE_DELAY = 50 // ms before querying the backend with a get query

const groupGetNameCalls = callGrouper(GRACE_DELAY)

export default (client) => {
  return {
    fetchAll(pageId) {
      return client.get(`builder/page/${pageId}/data-sources/`)
    },
    create(pageId, values = {}, beforeId = null) {
      const payload = {
        page_id: pageId,
        ...values,
      }

      if (beforeId !== null) {
        payload.before_id = beforeId
      }

      return client.post(`builder/page/${pageId}/data-sources/`, payload)
    },
    update(dataSourceId, values) {
      return client.patch(`builder/data-source/${dataSourceId}/`, values)
    },
    delete(dataSourceId) {
      return client.delete(`builder/data-source/${dataSourceId}/`)
    },
    move(dataSourceId, beforeId) {
      return client.patch(`builder/data-source/${dataSourceId}/move/`, {
        before_id: beforeId,
      })
    },
    dispatch(dataSourceId, dispatchContext, { range }) {
      // Using POST Http method here is not Restful but it the cleanest way to send
      // data with the call without relying on GET parameter and serialization of
      // complex object.
      const params = {}
      if (range) {
        params.offset = range[0]
        params.count = range[1]
      }

      return client.post(
        `builder/data-source/${dataSourceId}/dispatch/`,
        dispatchContext,
        { params }
      )
    },
    dispatchAll(pageId, params) {
      return client.post(
        `builder/page/${pageId}/dispatch-data-sources/`,
        params
      )
    },
    /**
     * Group multiple calls in one query to optimize perfs
     */
    getRecordNames: groupGetNameCalls(async (argList) => {
      // [[dataSourceId, recordIds], ...]
      //    ->{ <dataSourceId>: Array<with all record ids> }
      const dataSourceMap = argList.reduce((acc, [dataSourceId, recordIds]) => {
        if (!acc[`${dataSourceId}`]) {
          acc[`${dataSourceId}`] = new Set()
        }
        recordIds.forEach(acc[`${dataSourceId}`].add, acc[`${dataSourceId}`])
        return acc
      }, {})

      const data = Object.fromEntries(
        await Promise.all(
          Object.entries(dataSourceMap).map(
            async ([dataSourceId, recordIds]) => {
              try {
                const { data } = await client.get(
                  `builder/data-source/${dataSourceId}/record-names/`,
                  {
                    params: {
                      record_ids: Array.from(recordIds)
                        .map((item) => `${item}`)
                        .join(','),
                    },
                  }
                )
                return [dataSourceId, data]
              } catch (e) {
                return [dataSourceId, e]
              }
            }
          )
        )
      )

      return (dataSourceId, recordIds) => {
        if (!data[dataSourceId]) {
          return null
        }
        if (data[dataSourceId] instanceof Error) {
          throw data[dataSourceId]
        }
        return Object.fromEntries(
          Object.entries(data[dataSourceId]).filter(([key]) =>
            recordIds.includes(parseInt(key))
          )
        )
      }
    }),
  }
}
