<template>
  <div></div>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import PremiumFeatures from '@baserow_premium/components/PremiumFeatures'

export default {
  name: 'PremiumModal',
  components: { PremiumFeatures },
  mixins: [modal],
  props: {
    name: {
      type: String,
      required: true,
    },
    workspace: {
      type: [Object, null],
      required: false,
      default: null,
    },
  },
  computed: {
    buttonsComponent() {
      return this.$registry
        .get('plugin', 'premium')
        .getPremiumModalButtonsComponent()
    },
  },
}
</script>
