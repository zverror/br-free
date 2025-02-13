from typing import List

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType

from baserow.core.models import Workspace
from baserow.core.registries import SubjectType
from baserow.core.types import Subject
from baserow_enterprise.api.role.serializers import SubjectTeamSerializer
from baserow_enterprise.teams.models import Team, TeamSubject

User = get_user_model()


class TeamSubjectType(SubjectType):
    type = "baserow_enterprise.Team"
    model_class = Team

    def are_in_workspace(
        self, subjects: List[Subject], workspace: Workspace
    ) -> List[bool]:
        team_ids_in_workspace = set(
            Team.objects.filter(
                id__in=[s.id for s in subjects],
                workspace=workspace,
                trashed=False,
            ).values_list("id", flat=True)
        )

        return [t.id in team_ids_in_workspace for t in subjects]

    def get_serializer(self, model_instance, **kwargs):
        return SubjectTeamSerializer(model_instance, **kwargs)

    def get_users_included_in_subject(self, subject: Team) -> List[AbstractUser]:
        return list(
            User.objects.filter(
                pk__in=TeamSubject.objects_and_trash.filter(
                    team_id=subject.id,
                    subject_type=ContentType.objects.get_for_model(User),
                ).values_list("subject_id", flat=True)
            )
        )
