import { escapeRegExp } from '@baserow/modules/core/utils/string'

export default {
  inject: ['multiple'],
  props: {
    value: {
      validator: () => true,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    alias: {
      type: String,
      required: false,
    },
    icon: {
      type: String,
      required: false,
      default: null,
    },
    image: {
      type: String,
      required: false,
      default: null,
    },
    iconTooltip: {
      type: String,
      required: false,
      default: null,
    },
    description: {
      type: String,
      required: false,
      default: null,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    visible: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  data() {
    return {
      // This field is being used by `getDropdownItemComponents` in ``dropdown.js to
      // figure out if the child component is a dropdown item or not
      isDropdownItem: true,
      query: '',
    }
  },
  computed: {
    // Retrieve the first parent of this component that has 'isDropdown'
    // property set.
    parent() {
      let parent = this.$parent
      while (parent) {
        if (parent.isDropdown) {
          return parent
        }
        parent = parent.$parent
      }
      return parent
    },
  },
  methods: {
    select(value, disabled) {
      if (!disabled) {
        this.parent.select(value)
      }
      this.$emit('click', value)
    },
    hover(value, disabled) {
      if (!disabled && this.parent.hover !== value) {
        this.parent.hover = value
      }
    },
    search(query) {
      this.query = query
      return this.isVisible(query)
    },
    isVisible(query) {
      if (!query) {
        return true
      }
      const regex = new RegExp('(' + escapeRegExp(query) + ')', 'i')
      return this.name.match(regex) || this.alias?.match(regex)
    },
    isActive(value) {
      if (this.multiple.value) {
        return this.parent.value.includes(value)
      } else {
        return this.parent.value === value
      }
    },
    isHovering(value) {
      return this.parent.hover === value
    },
  },
}
