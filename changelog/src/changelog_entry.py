import abc
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

GITLAB_URL = os.environ.get("GITLAB_URL", "https://gitlab.com/baserow/baserow")


class ChangelogEntry(abc.ABC):
    type = None
    heading = None

    # Name of the current directory
    dir_name = os.path.dirname(__file__)

    def generate_entry_dict(
        self,
        message: str,
        issue_number: Optional[int] = None,
        bullet_points: List[str] = None,
    ) -> Dict[str, any]:
        if bullet_points is None:
            bullet_points = []

        return {
            "type": self.type,
            "message": message,
            "issue_number": issue_number,
            "bullet_points": bullet_points,
            "created_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
        }

    @staticmethod
    def get_markdown_string(message: str, issue_number: Union[int, None] = None) -> str:
        string = f"* {message}"

        if issue_number is not None:
            string += f" [#{issue_number}]({GITLAB_URL}/-/issues/{issue_number})"

        return string

    @property
    def markdown_heading(self) -> str:
        return f"### {self.heading}"


class FeatureChangelogEntry(ChangelogEntry):
    type = "feature"
    heading = "New features"


class BugChangelogEntry(ChangelogEntry):
    type = "bug"
    heading = "Bug fixes"


class RefactorChangelogEntry(ChangelogEntry):
    type = "refactor"
    heading = "Refactors"


class BreakingChangeChangelogEntry(ChangelogEntry):
    type = "breaking_change"
    heading = "Breaking API changes"


changelog_entry_types: Dict[str, type[ChangelogEntry]] = {
    FeatureChangelogEntry.type: FeatureChangelogEntry,
    BugChangelogEntry.type: BugChangelogEntry,
    RefactorChangelogEntry.type: RefactorChangelogEntry,
    BreakingChangeChangelogEntry.type: BreakingChangeChangelogEntry,
}
