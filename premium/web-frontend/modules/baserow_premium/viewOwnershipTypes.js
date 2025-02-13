import { ViewOwnershipType } from '@baserow/modules/database/viewOwnershipTypes'
import PremiumFeatures from '@baserow_premium/features'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import ViewOwnershipMenuLink from '@baserow_premium/components/views/ViewOwnershipMenuLink'

export class PersonalViewOwnershipType extends ViewOwnershipType {
  static getType() {
    return 'personal'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewOwnershipType.personal')
  }

  getFeatureName() {
    const { i18n } = this.app
    return i18n.t('premiumFeatures.personalViews')
  }

  getIconClass() {
    return 'iconoir-lock'
  }

  isDeactivated(workspaceId) {
    return false
  }

  getDeactivatedText() {
    return ''
  }

  getDeactivatedModal() {
    return null
  }

  getListViewTypeSort() {
    return 40
  }

  /**
   * Returns the component that should be used in the menu for changing the
   * ownership type for the view.
   */
  getChangeOwnershipTypeMenuItemComponent() {
    return ViewOwnershipMenuLink
  }

  userCanTryCreate(table, workspaceId) {
    return this.app.$hasPermission(
      'database.table.create_and_use_personal_view',
      table,
      workspaceId
    )
  }
}
