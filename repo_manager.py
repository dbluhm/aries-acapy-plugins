import os
import re
import shutil
import sys
from copy import deepcopy
from enum import Enum
from typing import Optional

GLOBAL_PLUGIN_DIR = "plugin_globals"


class PluginInfo:
    def __init__(
        self,
        name: str,
        version: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.version = version
        self.description = description


class MangagedPoetrySections(str, Enum):
    META = "[tool.poetry]"
    DEPS = "[tool.poetry.dependencies]"
    DEV_DEPS = "[tool.poetry.dev-dependencies]"
    INT_DEPS = "[tool.poetry.group.integration.dependencies]"
    RUFF = "[tool.ruff]"
    RUFF_LINT = "[tool.ruff.lint]"
    RUFF_FILES = "[tool.ruff.per-file-ignores]"
    PYTEST = "[tool.pytest.ini_options]"
    COVERAGE = "[tool.coverage.run]"
    COVERAGE_REPORT = "[tool.coverage.report]"
    COVERAGE_XML = "[tool.coverage.xml]"
    BUILD = "[build-system]"
    EXTRAS = "[tool.poetry.extras]"


sections = {
    "META": [],
    "DEPS": [],
    "DEV_DEPS": [],
    "INT_DEPS": [],
    "RUFF": [],
    "RUFF_LINT": [],
    "RUFF_FILES": [],
    "PYTEST": [],
    "COVERAGE": [],
    "COVERAGE_REPORT": [],
    "COVERAGE_XML": [],
    "BUILD": [],
    "EXTRAS": [],
}


class NEW_PLUGIN_FOLDERS(Enum):
    DOCKER = "docker"
    INTEGRATION = "integration"
    DEVCONTAINER = ".devcontainer"
    VSCODE = ".vscode"


class NEW_PLUGIN_FILES(Enum):
    PYPROJECT = "pyproject.toml"
    README = "README.md"
    DEFINITION = "definition.py"


class TAGGED_FILES(Enum):
    DOCKER_DEFAULT = "docker/default.yml"
    DOCKERFILE = "docker/Dockerfile"
    DOCKER_INTEGRATION = "docker/integration.yml"
    PYPROJECT = "pyproject.toml"
    PYPROJECT_INTEGRATION = "integration/pyproject.toml"
    DEVCONTAINER = ".devcontainer/devcontainer.json"
    VSCODE = ".vscode/launch.json"


def replace_plugin_tag(path: str, info: PluginInfo):
    with open(path, "r") as file:
        filedata = file.read()
    filedata = filedata.replace(GLOBAL_PLUGIN_DIR, info.name)
    with open(path, "w") as file:
        file.write(filedata)


def copy_all_common_files_for_new_plugin(info: PluginInfo) -> None:
    for folder in list(NEW_PLUGIN_FOLDERS):
        shutil.copytree(
            f"./{GLOBAL_PLUGIN_DIR}/{folder.value}", f"./{info.name}/{folder.value}"
        )
    for file in list(NEW_PLUGIN_FILES):
        file_location = (
            f"./{info.name}/{file.value}"
            if not file == NEW_PLUGIN_FILES.DEFINITION
            else f"./{info.name}/{info.name}/{file.value}"
        )
        shutil.copyfile(f"./{GLOBAL_PLUGIN_DIR}/{file.value}", file_location)
    for file in list(TAGGED_FILES):
        replace_plugin_tag(f"./{info.name}/{file.value}", info)


def combine_dependenices(plugin_dependencies, global_dependencies) -> None:
    """Add the plugin dependencies to the global dependencies if they are plugin specific."""
    for p_dep in plugin_dependencies:
        if p_dep.split("=")[0].strip() not in [
            g_dep.split("=")[0].strip() for g_dep in global_dependencies
        ]:
            global_dependencies.append(p_dep)


def is_end_of_section(line: str, current_section: str) -> bool:
    str_line = line.strip()
    return (
        str_line in [section.value for section in MangagedPoetrySections]
        and str_line != current_section
    )


def get_section(i: int, filedata: list, arr: list, current_section: str) -> int:
    """Put the section into the array and return the number of lines in the section."""
    j = i
    while j < len(filedata) and not is_end_of_section(filedata[j], current_section):
        arr.append(filedata[j])
        j += 1
    # Remove the last empty line
    if arr[-1] == "":
        arr.pop()
    return j - i


def extract_common_sections(filedata: str, sections: dict) -> None:
    """Go through the file by line and extract the section into the sections object."""
    filedata = filedata.split("\n")
    for i in range(len(filedata)):
        line = filedata[i]
        for section in MangagedPoetrySections:
            if line.startswith(section.value):
                i += get_section(i + 1, filedata, sections[section.name], section.value)


def get_section_output(
    i: int, content: list, output: list, section: list, current_section: str
) -> int:
    """
    Get a config section based off of an empty line of length of file.
    Args:
        i: The current line number
        content: The file content
        output: The output list
        section: The section to process

    Returns: The number of lines in the section
    """
    j = i
    output.append(content[j])
    while j < len(content) - 1 and not is_end_of_section(content[j], current_section):
        j += 1
    while len(section) > 0:
        output.append(section.pop(0) + "\n")
    output.append("\n")
    return j - i


def get_and_combine_main_poetry_sections(name: str) -> (dict, dict):
    """Get the global main sections and combine them with the plugin specific sections."""
    global_sections = deepcopy(sections)
    plugin_sections = deepcopy(sections)

    with open(f"./{GLOBAL_PLUGIN_DIR}/{TAGGED_FILES.PYPROJECT.value}", "r") as file:
        filedata = file.read()
        extract_common_sections(filedata, global_sections)

    with open(f"./{name}/{TAGGED_FILES.PYPROJECT.value}", "r") as file:
        filedata = file.read()
        extract_common_sections(filedata, plugin_sections)

    combine_dependenices(plugin_sections["DEPS"], global_sections["DEPS"])
    combine_dependenices(plugin_sections["DEV_DEPS"], global_sections["DEV_DEPS"])
    combine_dependenices(plugin_sections["INT_DEPS"], global_sections["INT_DEPS"])
    return global_sections, plugin_sections


def process_main_config_sections(
    name: str, plugin_sections: dict, global_sections: dict
) -> None:
    """Process the main config sections and write them to the plugins pyproject.toml file."""
    with open(f"./{GLOBAL_PLUGIN_DIR}/{TAGGED_FILES.PYPROJECT.value}", "r") as in_file:
        content = in_file.readlines()

    sections = [section.value for section in MangagedPoetrySections]

    output = []
    with open(f"./{name}/{TAGGED_FILES.PYPROJECT.value}", "w") as out_file:
        i = 0
        while i < len(content):
            if content[i].startswith(MangagedPoetrySections.META.value):
                output.append(MangagedPoetrySections.META.value + "\n")
                [output.append(line + "\n") for line in plugin_sections["META"]]
                output.append("\n")
                i += 1

            for section in sections:
                if content[i].startswith(section):
                    i += get_section_output(
                        i,
                        content,
                        output,
                        global_sections[
                            MangagedPoetrySections(content[i].strip()).name
                        ],
                        content[i],
                    )
            else:
                i += 1
        out_file.writelines(output)
    replace_plugin_tag(f"./{name}/{TAGGED_FILES.PYPROJECT.value}", PluginInfo(name))


def get_and_combine_integration_poetry_sections(name: str) -> tuple[dict, dict]:
    """Get the global integration sections and combine them with the plugin specific sections."""
    global_sections = deepcopy(sections)
    plugin_sections = deepcopy(sections)
    with open(
        f"./{GLOBAL_PLUGIN_DIR}/{TAGGED_FILES.PYPROJECT_INTEGRATION.value}", "r"
    ) as file:
        filedata = file.read()
    extract_common_sections(filedata, global_sections)

    with open(f"./{name}/{TAGGED_FILES.PYPROJECT_INTEGRATION.value}", "r") as file:
        filedata = file.read()

    extract_common_sections(filedata, plugin_sections)
    combine_dependenices(plugin_sections["DEPS"], global_sections["DEPS"])
    combine_dependenices(plugin_sections["DEV_DEPS"], global_sections["DEV_DEPS"])

    return global_sections, plugin_sections


def process_integration_config_sections(
    name: str, plugin_sections: dict, global_sections: dict
) -> None:
    """Process the integration test config sections and write them to the plugins intergqtion/pyproject.toml file."""
    with open(
        f"./{GLOBAL_PLUGIN_DIR}/{TAGGED_FILES.PYPROJECT_INTEGRATION.value}", "r"
    ) as in_file:
        content = in_file.readlines()

    sections = [section.value for section in MangagedPoetrySections]

    output = []
    with open(f"./{name}/{TAGGED_FILES.PYPROJECT_INTEGRATION.value}", "w") as out_file:
        i = 0
        while i < len(content):
            if content[i].startswith(MangagedPoetrySections.META.value):
                output.append(MangagedPoetrySections.META.value + "\n")
                [output.append(line + "\n") for line in plugin_sections["META"]]
                i += 1
                output.append("\n")

            for section in sections:
                if content[i].startswith(section):
                    i += get_section_output(
                        i,
                        content,
                        output,
                        global_sections[
                            MangagedPoetrySections(content[i].strip()).name
                        ],
                        content[i],
                    )
            else:
                i += 1
        out_file.writelines(output)


def replace_global_sections(name: str) -> None:
    """
    Combine the global sections with the plugin specific sections and write them to the plugins pyproject.toml file
    with the global dependencies overriding the plugin dependencies.
    """
    global_sections, plugin_sections = get_and_combine_main_poetry_sections(name)
    process_main_config_sections(name, plugin_sections, global_sections)
    global_sections, plugin_sections = get_and_combine_integration_poetry_sections(name)
    process_integration_config_sections(name, plugin_sections, global_sections)


def is_plugin_directory(plugin_name: str) -> bool:
    # If there is a drirectory which is not a plugin it should be ignored here
    return (
        os.path.isdir(plugin_name)
        and plugin_name != GLOBAL_PLUGIN_DIR
        and not plugin_name.startswith(".")
    )


def main(arg_1=None):

    options = """
        What would you like to do? 
        (1) Create a new plugin
        (2) Update all plugin common poetry sections 
        (3) Upgrade plugin_global dependencies 
        (4) Update plugins description with supported aries-cloudagent version
        (5) Get the plugins that upgraded since last release
        (6) Exit \n\nInput:  """

    if arg_1:
        selection = arg_1
    else:
        selection = input(options)

    if selection != "4" and selection != "5":
        print("Checking poetry is available...")
        response = os.system("which poetry")
        if response == "":
            print("Poetry is not available. Please install poetry.")
            exit(1)

    if selection == "1":
        # Create a new plugin
        msg = """Creating a new plugin: This will create a blank plugin with all the common files and folders needed to get started developing and testing."""
        print(msg)
        name = input("Enter the plugin name (recommended to use snake_case): ")
        if name == "":
            print("You must enter a plugin name")
            exit(1)
        version = str(input("Enter the plugin version (default is 0.1.0): ") or "0.1.0")
        description = input("Enter the plugin description (default is ''): ") or ""

        plugin_info = PluginInfo(name, version, description)
        os.makedirs(f"./{name}/{name}/v1_0")
        copy_all_common_files_for_new_plugin(plugin_info)

        os.system(f"cd {name} && poetry install --all-extras")

    elif selection == "2":
        # Update common poetry sections
        msg = """Updating all plugin common poetry sections: This will take the global sections from the plugin_globals and combine them with the plugin specific sections, and install and update the lock file \n"""
        print(msg)
        for plugin_name in os.listdir("./"):
            if is_plugin_directory(plugin_name):
                print(f"Updating common poetry sections in {plugin_name}\n")
                replace_global_sections(plugin_name)
                os.system(f"cd {plugin_name} && rm poetry.lock && poetry lock")
                os.system(
                    f"cd {plugin_name}/integration && rm poetry.lock && poetry lock"
                )

    elif selection == "3":
        # Upgrade plugin globals lock file
        msg = """Upgrade plugin_global dependencies \n"""
        print(msg)
        os.system("cd plugin_globals && poetry lock")

    # Update plugins description with supported aries-cloudagent version
    elif selection == "4":
        """
        1. Update the description of each plugin with the supported aries-cloudagent version.
        2. Output text for the release notes in markdown form.
        """

        # Get the aries-cloudagent version from the global poetry.lock file
        with open("./plugin_globals/poetry.lock", "r") as file:
            for line in file:
                if 'name = "aries-cloudagent"' in line:
                    next_line = next(file, None)
                    global_version = re.findall(r'"([^"]*)"', next_line)
                    break
        # Create and output the markdown release notes
        msg = f"""### Release v{global_version[0]}\n##### The latest supported versions of aries-cloudagent for each plugin are as follows:\n"""
        print(msg)
        # Markdown table header
        print("| Plugin Name | Supported aries-cloudagent version |")
        print("| --- | --- |")
        for plugin_name in sorted(os.listdir("./")):
            if is_plugin_directory(plugin_name):
                # Plugin specific aries-cloudagent version
                with open(f"./{plugin_name}/poetry.lock", "r") as file:
                    for line in file:
                        if 'name = "aries-cloudagent"' in line:
                            next_line = next(file, None)
                            version = re.findall(r'"([^"]*)"', next_line)
                            break
                # Extract the description from the pyproject.toml file
                with open(f"./{plugin_name}/pyproject.toml", "r") as file:
                    filedata = file.read()
                    linedata = filedata.split("\n")
                    for i in range(len(linedata)):
                        line = linedata[i]
                        if "description = " in line:
                            description = re.findall(r'"([^"]*)"', line)
                            description_line = line
                            break

                # Replace the description with the supported aries-cloudagent version at the end
                if description[0].find("Supported aries-cloudagent version") != -1:
                    description[0] = description[0].split(
                        " (Supported aries-cloudagent version"
                    )[0]

                filedata = filedata.replace(
                    description_line,
                    f'description = "{description[0]} (Supported aries-cloudagent version: {version[0]}) "',
                )

                with open(f"./{plugin_name}/pyproject.toml", "w") as file:
                    file.write(filedata)
                print(f"|{plugin_name} | {version[0]}|")

        print("***")
        print(" - ")

    elif selection == "5":
        """
        Extact the plugins from the RELEASES.md and determine which plugins which can be
        upgraded or are new based off of the global aries-cloudagent version.
        """

        # All the pugins. Used to determine which plugins are new.
        all_plugins = [
            plugin for plugin in os.listdir("./") if is_plugin_directory(plugin)
        ]

        # Get the aries-cloudagent version from the global poetry.lock file
        with open("./plugin_globals/poetry.lock", "r") as file:
            for line in file:
                if 'name = "aries-cloudagent"' in line:
                    next_line = next(file, None)
                    global_version = re.findall(r'"([^"]*)"', next_line)
                    break

        # Extract the plugins and versions from the last release in the RELEASES.md file
        with open("RELEASES.md", "r") as file:
            last_releases = []
            for line in file:
                if f"### Release v{global_version[0]}" in line:
                    line = next(file)
                    line = next(file)
                    line = next(file)
                    while "***" not in line:
                        if (
                            line
                            != "| Plugin Name | Supported aries-cloudagent version |\n"
                            and line != "| --- | --- |\n"
                        ):
                            last_releases.append(line.strip())
                        line = next(file)
                    break

        # All plugins that have been released on the last release. Used to determine which plugins can be upgraded.
        plugins_on_old_release = []
        # All plugins that have been released. Used to determine which plugins are new.
        released_plugins = []

        # Get all released plugins and the plugins not on the global version
        for item in last_releases:
            released_plugins.append(item.split("|")[1].strip())
            if item.split("|")[2].strip() == global_version[0]:
                plugins_on_old_release.append(item.split("|")[1].strip())

        # If there is releases in the RELEASES.md file then look for new plugins and add them to plugins on old release
        if last_releases:
            new_plugins = [
                plugin for plugin in all_plugins if plugin not in released_plugins
            ]
            for plugin in new_plugins:
                plugins_on_old_release.append(plugin)
        output = ""
        for plugin in plugins_on_old_release:
            output += f"{plugin} "

        print(output)
    elif selection == "6":
        print("Exiting...")
        exit(0)
    else:
        print("Invalid selection. Please try again.")
        main()


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except Exception:
        main()
