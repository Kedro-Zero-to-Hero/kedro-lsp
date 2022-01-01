"""Kedro Language Server."""
import logging
import re
from typing import List, Optional

import yaml
from kedro.config.config import _path_lookup
from kedro.framework.startup import ProjectMetadata, bootstrap_project
from kedro.framework.project import _ProjectSettings, settings
from pygls.lsp.methods import DEFINITION, WORKSPACE_DID_CHANGE_CONFIGURATION
from pygls.lsp.types import (
    DidChangeConfigurationParams,
    InitializeParams,
    InitializeResult,
    Location,
    Position,
    Range,
    TextDocumentPositionParams,
)
from pygls.protocol import LanguageServerProtocol
from pygls.server import LanguageServer
from pygls.workspace import Document
from yaml.loader import SafeLoader

RE_START_WORD = re.compile("[A-Za-z_0-9:]*$")
RE_END_WORD = re.compile("^[A-Za-z_0-9:]*")


class KedroLanguageServerProtocol(LanguageServerProtocol):
    """Populate the language server with Kedro-specific information upon init."""

    def bf_initialize(self, params: InitializeParams) -> InitializeResult:
        """Override the default bf_initialize to add Kedro project_metadata."""
        server: KedroLanguageServer = self._server
        res = super().bf_initialize(params)
        try:
            project_metadata = bootstrap_project(server.workspace.root_path)
        except RuntimeError:
            project_metadata = None
        finally:
            server.project_metadata = project_metadata
            server.project_settings = settings
        return res


class KedroLanguageServer(LanguageServer):
    """Store Kedro-specific information in the language server."""

    project_metadata: Optional[ProjectMetadata]
    project_settings: Optional[_ProjectSettings]

    def is_kedro_project(self) -> bool:
        """Returns whether the current workspace is a kedro project."""
        return self.project_metadata is not None


SERVER = KedroLanguageServer(protocol_cls=KedroLanguageServerProtocol)


class SafeLineLoader(SafeLoader):  # pylint: disable=too-many-ancestors
    """A YAML loader that annotates loaded nodes with line number."""

    def construct_mapping(self, node, deep=False):
        mapping = super().construct_mapping(node, deep=deep)
        mapping["__line__"] = node.start_mark.line
        return mapping


@SERVER.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
def did_change_configuration(
    server: KedroLanguageServer,  # pylint: disable=unused-argument
    params: DidChangeConfigurationParams,  # pylint: disable=unused-argument
) -> None:
    """Implement event for workspace/didChangeConfiguration.
    Currently does nothing, but necessary for pygls.
    """


def _word_at_position(position: Position, document: Document) -> str:
    """Get the word under the cursor returning the start and end positions."""
    if position.line >= len(document.lines):
        return ""

    line = document.lines[position.line]
    i = position.character
    # Split word in two
    start = line[:i]
    end = line[i:]

    # Take end of start and start of end to find word
    # These are guaranteed to match, even if they match the empty string
    m_start = RE_START_WORD.findall(start)
    m_end = RE_END_WORD.findall(end)

    return m_start[0] + m_end[-1]


def _get_param_location(project_metadata: ProjectMetadata, word: str) -> Optional[Location]:
    param = word.split("params:")[-1]
    parameters_path = project_metadata.project_path / "conf" / "base" / "parameters.yml"
    # TODO: cache -- we shouldn't have to re-read the file on every request
    parameters_file = open(parameters_path, "r")
    param_line_no = None
    for line_no, line in enumerate(parameters_file, 1):
        if line.startswith(param):
            param_line_no = line_no
            break
    parameters_file.close()

    if param_line_no is None:
        return

    location = Location(
        uri=f"file://{parameters_path}",
        range=Range(
            start=Position(line=param_line_no - 1, character=0),
            end=Position(
                line=param_line_no,
                character=0,
            ),
        ),
    )
    return location


@SERVER.feature(DEFINITION)
def definition(server: KedroLanguageServer, params: TextDocumentPositionParams) -> Optional[List[Location]]:
    """Support Goto Definition for a dataset or parameter.
    Currently only support catalog defined in `conf/base`
    """
    if not server.is_kedro_project():
        return None

    document = server.workspace.get_document(params.text_document.uri)
    word = _word_at_position(params.position, document)

    if word.startswith("params:"):
        param_location = _get_param_location(server.project_metadata, word)
        if param_location:
            return [param_location]

    catalog_paths = _path_lookup(
        conf_path=server.project_metadata.project_path / server.project_settings.CONF_ROOT,
        patterns=["catalog*", "**/catalog*/**", "**/catalog*"],
    )
    locations = []

    for catalog_path in catalog_paths:
        catalog_conf = yaml.load(catalog_path.read_text(), Loader=SafeLineLoader)

        if word in catalog_conf:
            line = catalog_conf[word]["__line__"]
            location = Location(
                uri=f"file://{catalog_path}",
                range=Range(
                    start=Position(line=line - 1, character=0),
                    end=Position(
                        line=line,
                        character=0,
                    ),
                ),
            )
            locations.append(location)
    
    return locations or None


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2087)
    args = parser.parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    SERVER.start_tcp(args.host, args.port)
