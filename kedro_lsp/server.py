"""Kedro Language Server."""
import re
from typing import List, Optional

import yaml
from kedro.framework.startup import ProjectMetadata, _get_project_metadata
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
from yaml.composer import Composer

RE_START_WORD = re.compile("[A-Za-z_0-9:]*$")
RE_END_WORD = re.compile("^[A-Za-z_0-9:]*")


class KedroLanguageServerProtocol(LanguageServerProtocol):
    """Populate the language server with Kedro-specific information upon init."""

    def bf_initialize(self, params: InitializeParams) -> InitializeResult:
        """Override the default bf_initialize to add Kedro project_metadata."""
        server: KedroLanguageServer = self._server
        res = super().bf_initialize(params)
        try:
            project_metadata = _get_project_metadata(server.workspace.root_path)
        except RuntimeError:
            project_metadata = None
        finally:
            server.project_metadata = project_metadata
        return res


class KedroLanguageServer(LanguageServer):
    """Store Kedro-specific information in the language server."""

    project_metadata: Optional[ProjectMetadata]

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
    parameters_conf = yaml.load(parameters_path.read_text(), Loader=SafeLineLoader)
    print(parameters_conf)
    print(param)

    if param not in parameters_conf:
        return None

    line = parameters_conf[param]["__line__"]
    location = Location(
        uri=f"file://{parameters_path}",
        range=Range(
            start=Position(line=line - 1, character=0),
            end=Position(
                line=line,
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

    catalog_path = server.project_metadata.project_path / "conf" / "base" / "catalog.yml"
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
        return [location]

    return None
