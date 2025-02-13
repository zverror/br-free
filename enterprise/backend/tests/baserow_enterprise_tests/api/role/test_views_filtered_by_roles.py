from django.shortcuts import reverse

import pytest

from baserow_enterprise.role.handler import RoleAssignmentHandler


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db(transaction=True)
def test_list_applications_filtered_by_roles(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    workspace_1 = data_fixture.create_workspace(user=user)
    workspace_2 = data_fixture.create_workspace(user=user)
    database_1 = data_fixture.create_database_application(
        workspace=workspace_1, order=1
    )
    database_2 = data_fixture.create_database_application(
        workspace=workspace_1, order=3
    )
    database_3 = data_fixture.create_database_application(
        workspace=workspace_1, order=2
    )
    database_4 = data_fixture.create_database_application(
        workspace=workspace_2, order=1
    )
    database_5 = data_fixture.create_database_application(
        workspace=workspace_2, order=2
    )

    no_access = RoleAssignmentHandler().get_role_by_uid("NO_ACCESS")
    RoleAssignmentHandler().assign_role(
        user, workspace_1, role=no_access, scope=database_1.application_ptr
    )
    RoleAssignmentHandler().assign_role(
        user, workspace_2, role=no_access, scope=database_5.application_ptr
    )

    # Does it filter the application list for one workspace?
    response = api_client.get(
        reverse("api:applications:list", kwargs={"workspace_id": workspace_1.id}),
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()

    assert len(response_json) == 2

    assert [a["id"] for a in response_json] == [database_3.id, database_2.id]

    # Is it filtering out the full application list with multiple workspaces?
    response = api_client.get(
        reverse("api:applications:list"), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )

    response_json = response.json()

    assert len(response_json) == 3

    assert [a["id"] for a in response_json] == [
        database_3.id,
        database_2.id,
        database_4.id,
    ]


@pytest.mark.django_db
def test_list_tables_filtered_by_roles(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table_1 = data_fixture.create_database_table(database=database, order=2)
    table_2 = data_fixture.create_database_table(database=database, order=1)

    no_access = RoleAssignmentHandler().get_role_by_uid("NO_ACCESS")
    RoleAssignmentHandler().assign_role(
        user, database.workspace, role=no_access, scope=table_2
    )

    url = reverse("api:database:tables:list", kwargs={"database_id": database.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
    response_json = response.json()

    assert len(response_json) == 1

    assert [t["id"] for t in response_json] == [table_1.id]


@pytest.mark.django_db
def test_get_database_application_with_tables_filtered_by_roles(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table_1 = data_fixture.create_database_table(database=database, order=0)
    table_2 = data_fixture.create_database_table(database=database, order=1)

    no_access = RoleAssignmentHandler().get_role_by_uid("NO_ACCESS")
    RoleAssignmentHandler().assign_role(
        user, database.workspace, role=no_access, scope=table_2
    )

    url = reverse("api:applications:item", kwargs={"application_id": database.id})

    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    response_json = response.json()

    assert len(response_json["tables"]) == 1
    assert [t["id"] for t in response_json["tables"]] == [table_1.id]
