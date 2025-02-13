from typing import TYPE_CHECKING, List

from django.db.models import Q

if TYPE_CHECKING:
    from baserow.contrib.database.fields import models as field_models

from baserow.contrib.database.fields.dependencies.circular_reference_checker import (
    will_cause_circular_dep,
)
from baserow.contrib.database.fields.dependencies.exceptions import (
    CircularFieldDependencyError,
)
from baserow.contrib.database.fields.dependencies.models import FieldDependency
from baserow.contrib.database.fields.field_cache import FieldCache


def break_dependencies_for_field(field):
    """
    Given a specific field ensures no fields depend on it any more, and if they do
    those dependencies are set to be broken and only reference the field name.

    :param field: The field whose dependants will have their relationships broken for.
    """

    from baserow.contrib.database.fields.models import LinkRowField

    FieldDependency.objects.filter(dependant=field).delete()
    field.dependants.update(dependency=None, broken_reference_field_name=field.name)
    if isinstance(field, LinkRowField):
        field.vias.all().delete()


def update_fields_with_broken_references(field: "field_models.Field"):
    """
    Checks to see if there are any fields which should now depend on `field` if it's
    name has changed to match a broken reference.

    :param field: The field that has potentially just been renamed.
    :return: True if some fields were found which now depend on field, False otherwise.
    """

    broken_dependencies_fixed_by_fields_name = FieldDependency.objects.filter(
        Q(
            dependant__table=field.table,
            broken_reference_field_name=field.name,
        )
        | Q(
            via__link_row_table=field.table,
            broken_reference_field_name=field.name,
        )
    )
    updated_deps = []
    for dep in broken_dependencies_fixed_by_fields_name:
        if not will_cause_circular_dep(dep.dependant, field):
            dep.dependency = field
            dep.broken_reference_field_name = None
            updated_deps.append(dep)
    FieldDependency.objects.bulk_update(
        updated_deps, ["dependency", "broken_reference_field_name"]
    )

    return len(updated_deps) > 0


def rebuild_field_dependencies(
    field_instance,
    field_cache: FieldCache,
) -> List[FieldDependency]:
    """
    Deletes all existing dependencies a field has and resets them to the ones
    defined by the field_instances FieldType.get_field_dependencies. Does not
    affect any dependencies from other fields to this field.

    :param field_instance: The field whose dependencies to change.
    :param field_cache: A cache which will be used to lookup the actual
        fields referenced by any provided field dependencies.
    :return: Any new dependencies created by the rebuild.
    """

    from baserow.contrib.database.fields.registries import field_type_registry

    field_type = field_type_registry.get_by_model(field_instance)
    new_dependencies = field_type.get_field_dependencies(field_instance, field_cache)

    current_dependencies = field_instance.dependencies.all()

    # The str of a dependency can be used to compare two dependencies to see if they
    # are functionally the same.
    current_deps_by_str = {str(dep): dep for dep in current_dependencies}
    new_deps_by_str = {str(dep): dep for dep in new_dependencies}
    new_dependencies_to_create = []

    for new_dep_str, new_dep in new_deps_by_str.items():
        try:
            # By removing from current_deps_by_str once we have finished the loop
            # it will contain all the old dependencies we need to delete.
            current_deps_by_str.pop(new_dep_str)
        except KeyError:
            # The new dependency does not exist in the current dependencies so we must
            # create it.
            new_dependencies_to_create.append(new_dep)

    for dep in new_dependencies_to_create:
        if dep.dependency is not None and will_cause_circular_dep(
            field_instance, dep.dependency
        ):
            raise CircularFieldDependencyError()

    new_dependencies = FieldDependency.objects.bulk_create(new_dependencies_to_create)
    # All new dependencies will have been removed from current_deps_by_str and so any
    # remaining ones are old dependencies which should no longer exist. Delete them.
    delete_ids = [dep.id for dep in current_deps_by_str.values()]
    FieldDependency.objects.filter(pk__in=delete_ids).delete()
    return new_dependencies
