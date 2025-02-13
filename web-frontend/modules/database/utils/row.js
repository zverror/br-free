/**
 * Serializes a row to make sure that the values are according to what the API expects.
 *
 * If a field doesn't have a value it will be assigned the empty value of the field
 * type.
 */
export function prepareRowForRequest(row, fields, registry) {
  return fields.reduce((preparedRow, field) => {
    const name = `field_${field.id}`
    const fieldType = registry.get('field', field._.type.type)

    if (fieldType.isReadOnly) {
      return preparedRow
    }

    preparedRow[name] = Object.prototype.hasOwnProperty.call(row, name)
      ? (preparedRow[name] = fieldType.prepareValueForUpdate(field, row[name]))
      : fieldType.getEmptyValue(field)

    return preparedRow
  }, {})
}

/**
 * This helper function prepares objects that can be used to update a row with an
 * immediate user experience.
 *
 * newRowValues: contains an object of values that can immediately be applied to the
 * row. It will hold the updated value, and the related field values we can can
 * update optimisticly.
 *
 * oldRowValues: contains an object with the same keys as the newRowValues, but with
 * their old values. This can be used to revert back to the old values if something
 * fails.
 *
 * updateRequestValues: contains the values that new values prepared for an API
 * request update. These are the ones you want to pass into the service.
 */
export function prepareNewOldAndUpdateRequestValues(
  row,
  allFields,
  field,
  value,
  oldValue,
  registry
) {
  const newRowValues = {
    id: row.id,
    [`field_${field.id}`]: value,
  }
  const oldRowValues = {
    id: row.id,
    [`field_${field.id}`]: oldValue,
  }
  const updateRequestValues = {}

  // Loop over all fields except the one that we're going to update, to figure out
  // if the `onRowChange` return value of the field has changed. If so, we want to
  // add that to immediately add that to the `newRowValues` immediately, so that the
  // update feels instant to the user.
  allFields
    .filter((f) => f.id !== field.id)
    .forEach((fieldToCall) => {
      const fieldType = registry.get('field', fieldToCall.type)
      const fieldID = `field_${fieldToCall.id}`
      const currentFieldValue = row[fieldID]
      const optimisticFieldValue = fieldType.onRowChange(
        row,
        fieldToCall,
        currentFieldValue
      )

      if (currentFieldValue !== optimisticFieldValue) {
        newRowValues[fieldID] = optimisticFieldValue
        oldRowValues[fieldID] = currentFieldValue
      }
    })

  const fieldType = registry.get('field', field.type)
  const updateValue = fieldType.prepareValueForUpdate(field, value)
  updateRequestValues[`field_${field.id}`] = updateValue

  return { newRowValues, oldRowValues, updateRequestValues }
}

/**
 * Returns an object only containing the read-only values of the row, and the id.
 * This can be used to update a row with the return data after making an update
 * request. The reason we need to do this, is because the other values might have
 * changed in the meantime, and they should not be updated.
 */
export function extractRowReadOnlyValues(row, allFields, registry) {
  const readOnlyValues = { id: row.id }
  allFields.forEach((field) => {
    const fieldType = registry.get('field', field.type)
    const fieldKey = `field_${field.id}`
    if (
      (fieldType.getIsReadOnly() || field.read_only) &&
      Object.prototype.hasOwnProperty.call(row, fieldKey)
    ) {
      readOnlyValues[fieldKey] = row[fieldKey]
    }
  })
  return readOnlyValues
}
