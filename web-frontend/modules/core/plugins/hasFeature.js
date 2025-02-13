export default function (context) {
  const { app } = context
  app.$hasFeature = (feature, workspaceId = null) => {
    return true
  }
}
