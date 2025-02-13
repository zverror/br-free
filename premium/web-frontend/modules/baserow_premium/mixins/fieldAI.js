import { notifyIf } from '@baserow/modules/core/utils/error'

import FieldService from '@baserow_premium/services/field'

export default {
  data() {
    return {
      generating: false,
    }
  },
  computed: {
    workspace() {
      return this.$store.getters['workspace/get'](this.workspaceId)
    },
    modelAvailable() {
      const aIModels =
        this.$store.getters['settings/get'].generative_ai[
          this.field.ai_generative_ai_type
        ] || []
      return (
        this.$registry
          .get('field', this.field.type)
          .isEnabled(this.workspace) &&
        aIModels.includes(this.field.ai_generative_ai_model)
      )
    },
    isDeactivated() {
      return false
    },
    deactivatedClickComponent() {
      return null
    },
  },
  watch: {
    value() {
      this.generating = false
    },
  },
  methods: {
    async generate() {
      this.generating = true
      try {
        await FieldService(this.$client).generateAIFieldValues(this.field.id, [
          this.$parent.row.id,
        ])
      } catch (error) {
        notifyIf(error, 'field')
        this.generating = false
      }
    },
  },
}
