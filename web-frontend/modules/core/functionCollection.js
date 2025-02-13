import { FunctionCollection } from '@baserow/modules/core/formula/parser/javascriptExecutor'

export class RuntimeFunctionCollection extends FunctionCollection {
  constructor($registry) {
    super()
    this.$registry = $registry
  }

  get(name) {
    return this.$registry.get('runtimeFormulaFunction', name)
  }

  getAll() {
    return this.$registry.getAll('runtimeFormulaFunction')
  }
}
