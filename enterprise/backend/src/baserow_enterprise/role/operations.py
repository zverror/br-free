from baserow.contrib.database.table.operations import DatabaseTableOperationType
from baserow.core.operations import ApplicationOperationType, WorkspaceCoreOperationType


class AssignRoleWorkspaceOperationType(WorkspaceCoreOperationType):
    type = "workspace.assign_role"


class ReadRoleWorkspaceOperationType(WorkspaceCoreOperationType):
    type = "workspace.read_role"


class ReadRoleApplicationOperationType(ApplicationOperationType):
    type = "application.read_role"


class UpdateRoleApplicationOperationType(ApplicationOperationType):
    type = "application.update_role"


class ReadRoleTableOperationType(DatabaseTableOperationType):
    type = "database.table.read_role"


class UpdateRoleTableOperationType(DatabaseTableOperationType):
    type = "database.table.update_role"
