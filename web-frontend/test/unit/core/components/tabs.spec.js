import { mount } from '@vue/test-utils'
import Tabs from '@baserow/modules/core/components/Tabs'
import Tab from '@baserow/modules/core/components/Tab'

describe('Tabs', () => {
  it('renders the correct number of tabs', () => {
    const tabs = [
      { title: 'Tab 1', content: 'Tab 1 content' },
      { title: 'Tab 2', content: 'Tab 2 content' },
      { title: 'Tab 3', content: 'Tab 3 content' },
    ]

    const wrapper = mount(Tabs, {
      components: {
        Tab,
      },
      slots: {
        default: tabs
          .map((tab) => `<Tab title="${tab.title}">${tab.content}</Tab>`)
          .join(''),
      },
    })

    expect(wrapper.findAllComponents(Tab).length).toEqual(tabs.length)
  })

  it('emits a tab-selected event when a tab is clicked', () => {
    const tabs = [
      { title: 'Tab 1', content: 'Tab 1 content' },
      { title: 'Tab 2', content: 'Tab 2 content' },
      { title: 'Tab 3', content: 'Tab 3 content' },
    ]

    const wrapper = mount(Tabs, {
      components: {
        Tab,
      },
      slots: {
        default: tabs
          .map((tab) => `<Tab title="${tab.title}">${tab.content}</Tab>`)
          .join(''),
      },
    })

    wrapper.findAllComponents(Tab).at(1).vm.$emit('click', 1)
    expect(wrapper.emitted('update:selectedIndex')).toBeTruthy()
  })
})
