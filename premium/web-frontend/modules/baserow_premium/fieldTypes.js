import {
  FieldType,
  FormulaFieldType,
} from '@baserow/modules/database/fieldTypes'

import GridViewFieldAI from '@baserow_premium/components/views/grid/fields/GridViewFieldAI'
import FunctionalGridViewFieldAI from '@baserow_premium/components/views/grid/fields/FunctionalGridViewFieldAI'
import RowEditFieldAI from '@baserow_premium/components/row/RowEditFieldAI'
import FieldAISubForm from '@baserow_premium/components/field/FieldAISubForm'
import FormulaFieldAI from '@baserow_premium/components/field/FormulaFieldAI'
import GridViewFieldAIGenerateValuesContextItem from '@baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import PremiumFeatures from '@baserow_premium/features'

export class AIFieldType extends FieldType {
  static getType() {
    return 'ai'
  }

  getIconClass() {
    return 'iconoir-magic-wand'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('premiumFieldType.ai')
  }

  getIsReadOnly() {
    return true
  }

  getGridViewFieldComponent() {
    return GridViewFieldAI
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldAI
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldAI
  }

  getFormComponent() {
    return FieldAISubForm
  }

  isEnabled(workspace) {
    return Object.values(workspace.generative_ai_models_enabled).some(
      (models) => models.length > 0
    )
  }

  isDeactivated(workspaceId) {
    // Always return false to disable premium check
    return false
  }

  getDeactivatedClickModal(workspaceId) {
    return PremiumModal
  }
}

export class PremiumFormulaFieldType extends FormulaFieldType {
  getAdditionalFormInputComponents() {
    return [FormulaFieldAI]
  }
}
