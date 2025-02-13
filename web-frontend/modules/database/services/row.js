import _ from 'lodash'
import { callGrouper } from '@baserow/modules/core/utils/function'

const GRACE_DELAY = 50 // ms before querying the backend with a get query

const groupGetNameCalls = callGrouper(GRACE_DELAY)

export default (client) => {
  return {
    get(tableId, rowId) {
      return client.get(`/database/rows/table/${tableId}/${rowId}/`)
    },
    fetchAll({
      tableId,
      page = 1,
      size = 10,
      search = null,
      viewId = null,
      searchMode = null,
    }) {
      const config = {
        params: {
          page,
          size,
        },
      }

      if (search !== null && search !== '') {
        config.params.search = search
        config.params.search_mode = searchMode
      }

      if (viewId !== null) {
        config.params.view_id = viewId
      }

      return client.get(`/database/rows/table/${tableId}/`, config)
    },
    /**
     * Returns the name of specified table row. Batch consecutive queries into one
     * during the defined GRACE_TIME.
     */
    getName: groupGetNameCalls(async (argList) => {
      // [[tableId, id], ...] -> { table__<id>: Array<row ids> }
      const tableMap = argList.reduce((acc, [tableId, rowId]) => {
        if (!acc[`table__${tableId}`]) {
          acc[`table__${tableId}`] = new Set()
        }
        acc[`table__${tableId}`].add(rowId)
        return acc
      }, {})

      const config = {
        params: _.mapValues(tableMap, (rowIds) => Array.from(rowIds).join(',')),
      }

      const { data } = await client.get(`/database/rows/names/`, config)

      return (tableId, rowId) => {
        if (!data[tableId]) {
          return null
        }
        return data[tableId][rowId]
      }
    }),
    getIds(tableId, rowNames) {
      return Promise.all(rowNames.map((name) => this.getId(tableId, name)))
    },
    create(tableId, values, beforeId = null) {
      const config = { params: {} }

      if (beforeId !== null) {
        config.params.before = beforeId
      }

      return client.post(`/database/rows/table/${tableId}/`, values, config)
    },
    batchCreate(tableId, rows, beforeId = null) {
      const config = { params: {} }

      if (beforeId !== null) {
        config.params.before = beforeId
      }

      return client.post(
        `/database/rows/table/${tableId}/batch/`,
        { items: rows },
        config
      )
    },
    update(tableId, rowId, values) {
      return client.patch(`/database/rows/table/${tableId}/${rowId}/`, values)
    },
    batchUpdate(tableId, items) {
      return client.patch(`/database/rows/table/${tableId}/batch/`, { items })
    },
    /**
     * Moves the row to the position before the row related to the beforeRowId
     * parameters. If the before id is not provided then the row will be moved
     * to the end.
     */
    move(tableId, rowId, beforeRowId = null) {
      const config = { params: {} }

      if (beforeRowId !== null) {
        config.params.before_id = beforeRowId
      }

      return client.patch(
        `/database/rows/table/${tableId}/${rowId}/move/`,
        null,
        config
      )
    },
    delete(tableId, rowId) {
      return client.delete(`/database/rows/table/${tableId}/${rowId}/`)
    },
    batchDelete(tableId, items) {
      return client.post(`/database/rows/table/${tableId}/batch-delete/`, {
        items,
      })
    },
    getAdjacent({
      tableId,
      rowId,
      viewId = null,
      previous = false,
      search = null,
      searchMode = null,
    }) {
      const searchSanitized = search === '' ? null : search
      return client.get(`/database/rows/table/${tableId}/${rowId}/adjacent/`, {
        params: {
          previous,
          search: searchSanitized,
          view_id: viewId,
          search_mode: searchMode,
        },
      })
    },
  }
}
