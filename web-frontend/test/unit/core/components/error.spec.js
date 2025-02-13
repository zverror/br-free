import Error from '@baserow/modules/core/components/Error'
import { TestApp } from '@baserow/test/helpers/testApp'
// import { bootstrapVueContext } from '@baserow/test/helpers/components'

describe('Error Component Tests', () => {
  let testApp = null

  beforeAll(() => {
    testApp = new TestApp()
  })

  afterEach(() => {
    testApp.afterEach()
  })

  const mountComponent = (
    props = {
      error: {
        visible: true,
        title: 'error title',
        message: 'error content message',
      },
    }
  ) => {
    return testApp.mount(Error, { propsData: props })
  }

  test('When visible prop is true title and message are shown', async () => {
    const wrapper = await mountComponent()

    expect(wrapper.html()).toContain('error title')
    expect(wrapper.find('.alert__message p').text()).toContain(
      'error content message'
    )
  })

  test('When visible prop is false no html is rendered', async () => {
    const wrapper = await mountComponent({ error: { visible: false } })

    expect(wrapper.html()).toStrictEqual('')
  })
})
