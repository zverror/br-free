import { shallowMount } from '@vue/test-utils'

import FormGroup from '@baserow/modules/core/components/FormGroup.vue'

describe('FormGroup.vue', () => {
  it('renders the helper text when provided', () => {
    const wrapper = shallowMount(FormGroup, {
      propsData: {
        helperText: 'This is helper text',
      },
    })

    expect(wrapper.find('.control__helper-text').text()).toBe(
      'This is helper text'
    )
  })

  it('renders the error slot when error prop is true', () => {
    const wrapper = shallowMount(FormGroup, {
      propsData: {
        error: true,
      },
      slots: {
        error: '<div>This is an error message</div>',
      },
    })

    expect(wrapper.find('.control__messages--error').exists()).toBe(true)
    expect(wrapper.find('.control__messages--error').text()).toBe(
      'This is an error message'
    )
  })

  it('does not render the error slot when error prop is false', () => {
    const wrapper = shallowMount(FormGroup, {
      propsData: {
        error: false,
      },
      slots: {
        error: '<div>This is an error message</div>',
      },
    })

    expect(wrapper.find('.control__messages--error').exists()).toBe(false)
  })
  it('renders the warning slot when provided', () => {
    const wrapper = shallowMount(FormGroup, {
      slots: {
        warning: '<div>This is a warning message</div>',
      },
    })

    expect(wrapper.find('.control__messages--warning').exists()).toBe(true)
    expect(wrapper.find('.control__messages--warning').text()).toBe(
      'This is a warning message'
    )
  })

  it('renders the helper slot when provided', () => {
    const wrapper = shallowMount(FormGroup, {
      slots: {
        helper: '<div>This is helper slot content</div>',
      },
    })

    expect(wrapper.find('.control__helper-text').exists()).toBe(true)
    expect(wrapper.find('.control__helper-text').text()).toContain(
      'This is helper slot content'
    )
  })

  it('renders the default slot content', () => {
    const wrapper = shallowMount(FormGroup, {
      slots: {
        default: '<div>This is default slot content</div>',
      },
    })

    expect(wrapper.find('.control__elements').exists()).toBe(true)
    expect(wrapper.find('.control__elements').text()).toBe(
      'This is default slot content'
    )
  })
})
