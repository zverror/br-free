import json
import os
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, List, Optional, Union

from changelog_entry import changelog_entry_types
from pygit2 import Repository

LINE_BREAK_CHARACTER = "\n"
INDENT_CHARACTER = "  "
MAXIMUM_FILE_NAME_MESSAGE_LENGTH = 60


class ChangelogHandler:
    UNRELEASED_FOLDER_NAME = "unreleased"

    @property
    def release_meta_data_file_path(self):
        return f"{self.working_dir}/releases.json"

    @property
    def entries_file_path(self):
        return f"{self.working_dir}/entries"

    @property
    def changelog_path(self):
        return f"{self.working_dir}/changelog.md"

    def __init__(self, working_dir: str = os.path.dirname(__file__)):
        self.working_dir = working_dir

    def add_entry(
        self,
        changelog_entry_type_name: str,
        message: str,
        issue_number: Optional[int] = None,
        release: str = UNRELEASED_FOLDER_NAME,
        bullet_points: List[str] = None,
    ) -> str:
        changelog_entry_type = changelog_entry_types[changelog_entry_type_name]

        path = Path(f"{self.entries_file_path}/{release}/{changelog_entry_type.type}")
        path.mkdir(parents=True, exist_ok=True)

        file_name = ChangelogHandler.generate_entry_file_name(message, issue_number)

        full_path = f"{path}/{file_name}"

        if os.path.isfile(full_path):
            print(f'Existing change log entry "{file_name}" is being overwritten')

        with open(full_path, "w+") as entry_file:
            entry = changelog_entry_type().generate_entry_dict(
                message, issue_number, bullet_points=bullet_points
            )
            json.dump(entry, entry_file, indent=4)

        return full_path

    def get_changelog_entries(
        self,
        release_name: str = UNRELEASED_FOLDER_NAME,
    ) -> Dict[str, List[Dict]]:
        base_path = f"{self.entries_file_path}/{release_name}"
        entries = {entry_type: [] for entry_type in changelog_entry_types.keys()}

        for category_dir_name in os.listdir(base_path):
            if category_dir_name == ".gitkeep":
                continue

            category_dir = f"{base_path}/{category_dir_name}"

            entry_file_names = os.listdir(category_dir)
            entry_file_names.sort()

            for entry_file_name in entry_file_names:
                if entry_file_name == ".gitkeep":
                    continue

                entry_file_path = f"{category_dir}/{entry_file_name}"

                print(entry_file_path)
                with open(entry_file_path, "r") as entry_file:
                    entry = json.load(entry_file)
                    entries[entry["type"]].append(entry)

        return entries

    def get_releases_meta_data(self) -> Optional[Dict]:
        try:
            with open(self.release_meta_data_file_path, "r") as releases_file:
                return json.load(releases_file)
        except FileNotFoundError:
            print("Tried to read release meta data, but no file was found")
            return None

    def order_release_folders(self, release_folders: List[str]) -> List[str]:
        release_folders_ordered = []
        releases_meta_data = self.get_releases_meta_data()

        for release in releases_meta_data["releases"]:
            found_release = False
            for release_folder_name in release_folders:
                if release["name"] == release_folder_name:
                    release_folders_ordered.append(release_folder_name)
                    found_release = True
            if not found_release:
                print(
                    f"The release {release['name']} was not found and has been omitted "
                    f"from the changelog. Please check if the release folder exists."
                )

        return release_folders_ordered

    def generate_changelog_markdown_file(self):
        release_folders = os.listdir(self.entries_file_path)

        if ChangelogHandler.UNRELEASED_FOLDER_NAME in release_folders:
            release_folders.remove(ChangelogHandler.UNRELEASED_FOLDER_NAME)

        release_folders = self.order_release_folders(release_folders)

        changelog_file = open(self.changelog_path, "w+")

        changelog_file.write(f"# Changelog{LINE_BREAK_CHARACTER}{LINE_BREAK_CHARACTER}")

        for release_folder in release_folders:
            entries = self.get_changelog_entries(release_folder)

            release_heading = f"## Released {release_folder}"
            changelog_file.write(
                f"{release_heading}{LINE_BREAK_CHARACTER}{LINE_BREAK_CHARACTER}"
            )

            for entry_type in changelog_entry_types.values():
                entries_of_type = entries.get(entry_type.type, [])

                if len(entries_of_type) == 0:
                    continue

                heading = entry_type().markdown_heading
                changelog_file.write(f"{heading}{LINE_BREAK_CHARACTER}")

                for entry in entries_of_type:
                    entry_markdown_string = entry_type.get_markdown_string(
                        entry["message"], entry["issue_number"]
                    )

                    changelog_file.write(
                        f"{entry_markdown_string}{LINE_BREAK_CHARACTER}"
                    )

                    for bullet_point in entry.get("bullet_points", []):
                        changelog_file.write(
                            f"{INDENT_CHARACTER}* {bullet_point}{LINE_BREAK_CHARACTER}"
                        )

                changelog_file.write(LINE_BREAK_CHARACTER)

            changelog_file.write(LINE_BREAK_CHARACTER)

        changelog_file.close()

    def move_entries_to_release_folder(
        self, name: Union[str, None] = None
    ) -> Optional[str]:
        release_name = name or datetime.now(tz=timezone.utc).strftime("%Y_%m_%d")

        try:
            os.rename(
                f"{self.entries_file_path}/unreleased",
                f"{self.entries_file_path}/{release_name}",
            )
            os.mkdir(f"{self.entries_file_path}/unreleased")
            return release_name
        except OSError:
            print(f'Release with name "{release_name}" already exists.')
            return None

    @staticmethod
    def generate_entry_file_name(
        message: str, issue_number: Optional[int] = None
    ) -> str:
        file_name = ""

        if issue_number is not None:
            file_name += f"{issue_number}_"

        # Sanitise message
        message = message.strip().replace(".", "").replace(" ", "_")
        message = "".join(
            e for e in message if e.isalnum() or e == "_"
        )  # Remove special chars
        message = message.lower()

        file_name += message[:MAXIMUM_FILE_NAME_MESSAGE_LENGTH]
        file_name += ".json"

        return file_name

    @staticmethod
    def get_issue_number() -> Union[int, None]:
        potential_issue_number = Repository(".").head.shorthand.split("-")[0]

        try:
            return int(potential_issue_number)
        except ValueError:
            return None

    @staticmethod
    def get_message() -> str:
        branch_name = Repository(".").head.shorthand
        branch_has_issue_number = ChangelogHandler.get_issue_number() is not None

        if branch_has_issue_number:
            message = " ".join(branch_name.split("-")[1:])
        else:
            message = branch_name

        return message.replace("-", " ")

    def write_release_meta_data(self, name: str):
        # Make sure the parent dirs exist
        path = Path(self.release_meta_data_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Make sure the file exists
        if not os.path.isfile(self.release_meta_data_file_path):
            open(self.release_meta_data_file_path, "a").close()

        with open(self.release_meta_data_file_path, "r+") as release_file:
            try:
                release_data = json.load(release_file)
            except JSONDecodeError:
                release_data = {}

            if "releases" not in release_data:
                release_data["releases"] = []

            release_data["releases"].insert(
                0,
                {
                    "name": name,
                    "created_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
                },
            )

            release_file.seek(0)
            json.dump(release_data, release_file, indent=4)
            release_file.truncate()

    def is_release_name_unique(self, name: str) -> bool:
        return name not in os.listdir(self.entries_file_path)
