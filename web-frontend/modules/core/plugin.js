import Vue from 'vue'

import { Registry } from '@baserow/modules/core/registry'
import { PasswordAuthProviderType } from '@baserow/modules/core/authProviderTypes'
import {
  CreateSnapshotJobType,
  DuplicateApplicationJobType,
  ExportApplicationsJobType,
  ImportApplicationsJobType,
  InstallTemplateJobType,
  RestoreSnapshotJobType,
} from '@baserow/modules/core/jobTypes'

import {
  AccountSettingsType,
  PasswordSettingsType,
  EmailNotificationsSettingsType,
  DeleteAccountSettingsType,
} from '@baserow/modules/core/settingsTypes'
import { GenerativeAIWorkspaceSettingsType } from '@baserow/modules/core/workspaceSettingsTypes'
import {
  OpenAIModelType,
  OllamaModelType,
  AnthropicModelType,
  MistralModelType,
  OpenRouterModelType,
} from '@baserow/modules/core/generativeAIModelTypes'
import {
  UploadFileUserFileUploadType,
  UploadViaURLUserFileUploadType,
} from '@baserow/modules/core/userFileUploadTypes'
import {
  DashboardAdminType,
  UsersAdminType,
  WorkspacesAdminType,
  HealthCheckAdminType,
  SettingsAdminType,
} from '@baserow/modules/core/adminTypes'

import {
  BasicPermissionManagerType,
  CorePermissionManagerType,
  StaffPermissionManagerType,
  WorkspaceMemberPermissionManagerType,
  StaffOnlySettingOperationPermissionManagerType,
  AllowIfTemplateOperationPermissionManagerType,
} from '@baserow/modules/core/permissionManagerTypes'

import {
  MembersWorkspaceSettingsPageType,
  InvitesWorkspaceSettingsPageType,
} from '@baserow/modules/core/workspaceSettingsPageTypes'
import {
  WorkspaceInvitationCreatedNotificationType,
  WorkspaceInvitationAcceptedNotificationType,
  WorkspaceInvitationRejectedNotificationType,
  BaserowVersionUpgradeNotificationType,
} from '@baserow/modules/core/notificationTypes'
import {
  TeamOnboardingType,
  MoreOnboardingType,
  WorkspaceOnboardingType,
  InviteOnboardingType,
} from '@baserow/modules/core/onboardingTypes'

import settingsStore from '@baserow/modules/core/store/settings'
import applicationStore from '@baserow/modules/core/store/application'
import authProviderStore from '@baserow/modules/core/store/authProvider'
import authStore from '@baserow/modules/core/store/auth'
import workspaceStore from '@baserow/modules/core/store/workspace'
import jobStore from '@baserow/modules/core/store/job'
import toastStore from '@baserow/modules/core/store/toast'
import undoRedoStore from '@baserow/modules/core/store/undoRedo'
import integrationStore from '@baserow/modules/core/store/integration'
import userSourceStore from '@baserow/modules/core/store/userSource'
import notificationStore from '@baserow/modules/core/store/notification'
import userSourceUserStore from '@baserow/modules/core/store/userSourceUser'

import en from '@baserow/modules/core/locales/en.json'
import fr from '@baserow/modules/core/locales/fr.json'
import nl from '@baserow/modules/core/locales/nl.json'
import de from '@baserow/modules/core/locales/de.json'
import es from '@baserow/modules/core/locales/es.json'
import it from '@baserow/modules/core/locales/it.json'
import pl from '@baserow/modules/core/locales/pl.json'
import ko from '@baserow/modules/core/locales/ko.json'
import { DefaultErrorPageType } from '@baserow/modules/core/errorPageTypes'
import {
  RuntimeAdd,
  RuntimeConcat,
  RuntimeGet,
} from '@baserow/modules/core/runtimeFormulaTypes'

import priorityBus from '@baserow/modules/core/plugins/priorityBus'

import {
  AdminRoleType,
  MemberRoleType,
} from '@baserow/modules/database/roleTypes'

export default (context, inject) => {
  const { store, isDev, app } = context
  inject('bus', new Vue())
  inject('priorityBus', priorityBus)

  // Allow locale file hot reloading in dev
  if (isDev && app.i18n) {
    const { i18n } = app
    i18n.mergeLocaleMessage('en', en)
    i18n.mergeLocaleMessage('fr', fr)
    i18n.mergeLocaleMessage('nl', nl)
    i18n.mergeLocaleMessage('de', de)
    i18n.mergeLocaleMessage('es', es)
    i18n.mergeLocaleMessage('it', it)
    i18n.mergeLocaleMessage('pl', pl)
    i18n.mergeLocaleMessage('ko', ko)
  }

  const registry = new Registry()
  registry.registerNamespace('plugin')
  registry.registerNamespace('permissionManager')
  registry.registerNamespace('application')
  registry.registerNamespace('authProvider')
  registry.registerNamespace('job')
  registry.registerNamespace('view')
  registry.registerNamespace('field')
  registry.registerNamespace('settings')
  registry.registerNamespace('workspaceSettings')
  registry.registerNamespace('userFileUpload')
  registry.registerNamespace('membersPagePlugins')
  registry.registerNamespace('runtimeFormulaFunction')
  registry.registerNamespace('notification')
  registry.registerNamespace('workflowAction')
  registry.registerNamespace('integration')
  registry.registerNamespace('service')
  registry.registerNamespace('userSource')
  registry.registerNamespace('appAuthProvider')
  registry.registerNamespace('roles')
  registry.registerNamespace('generativeAIModel')
  registry.registerNamespace('onboarding')

  registry.register('settings', new AccountSettingsType(context))
  registry.register('settings', new PasswordSettingsType(context))
  registry.register('settings', new EmailNotificationsSettingsType(context))
  registry.register('settings', new DeleteAccountSettingsType(context))

  registry.register(
    'workspaceSettings',
    new GenerativeAIWorkspaceSettingsType(context)
  )

  registry.register('generativeAIModel', new OpenAIModelType(context))
  registry.register('generativeAIModel', new AnthropicModelType(context))
  registry.register('generativeAIModel', new MistralModelType(context))
  registry.register('generativeAIModel', new OllamaModelType(context))
  registry.register('generativeAIModel', new OpenRouterModelType(context))

  registry.register('permissionManager', new CorePermissionManagerType(context))
  registry.register(
    'permissionManager',
    new StaffPermissionManagerType(context)
  )
  registry.register(
    'permissionManager',
    new WorkspaceMemberPermissionManagerType(context)
  )
  registry.register(
    'permissionManager',
    new BasicPermissionManagerType(context)
  )
  registry.register(
    'permissionManager',
    new StaffOnlySettingOperationPermissionManagerType(context)
  )
  registry.register(
    'permissionManager',
    new AllowIfTemplateOperationPermissionManagerType(context)
  )

  registry.register('userFileUpload', new UploadFileUserFileUploadType(context))
  registry.register(
    'userFileUpload',
    new UploadViaURLUserFileUploadType(context)
  )
  registry.register('admin', new DashboardAdminType(context))
  registry.register('admin', new UsersAdminType(context))
  registry.register('admin', new WorkspacesAdminType(context))
  registry.register('admin', new SettingsAdminType(context))
  registry.register('admin', new HealthCheckAdminType(context))
  inject('registry', registry)

  store.registerModule('settings', settingsStore)
  store.registerModule('application', applicationStore)
  store.registerModule('authProvider', authProviderStore)
  store.registerModule('auth', authStore)
  store.registerModule('job', jobStore)
  store.registerModule('workspace', workspaceStore)
  store.registerModule('toast', toastStore)
  store.registerModule('undoRedo', undoRedoStore)
  store.registerModule('integration', integrationStore)
  store.registerModule('userSource', userSourceStore)
  store.registerModule('notification', notificationStore)
  store.registerModule('userSourceUser', userSourceUserStore)

  registry.register('authProvider', new PasswordAuthProviderType(context))
  registry.register('job', new DuplicateApplicationJobType(context))
  registry.register('job', new InstallTemplateJobType(context))
  registry.register('job', new CreateSnapshotJobType(context))
  registry.register('job', new RestoreSnapshotJobType(context))
  registry.register('job', new ExportApplicationsJobType(context))
  registry.register('job', new ImportApplicationsJobType(context))

  registry.register(
    'workspaceSettingsPage',
    new MembersWorkspaceSettingsPageType(context)
  )
  registry.register(
    'workspaceSettingsPage',
    new InvitesWorkspaceSettingsPageType(context)
  )

  registry.register('errorPage', new DefaultErrorPageType(context))

  registry.register('runtimeFormulaFunction', new RuntimeConcat(context))
  registry.register('runtimeFormulaFunction', new RuntimeGet(context))
  registry.register('runtimeFormulaFunction', new RuntimeAdd(context))

  registry.register('roles', new AdminRoleType(context))
  registry.register('roles', new MemberRoleType(context))

  // Notification types
  registry.register(
    'notification',
    new WorkspaceInvitationCreatedNotificationType(context)
  )
  registry.register(
    'notification',
    new WorkspaceInvitationAcceptedNotificationType(context)
  )
  registry.register(
    'notification',
    new WorkspaceInvitationRejectedNotificationType(context)
  )
  registry.register(
    'notification',
    new BaserowVersionUpgradeNotificationType(context)
  )

  registry.register('onboarding', new TeamOnboardingType(context))
  registry.register('onboarding', new MoreOnboardingType(context))
  registry.register('onboarding', new WorkspaceOnboardingType(context))
  registry.register('onboarding', new InviteOnboardingType(context))
}
