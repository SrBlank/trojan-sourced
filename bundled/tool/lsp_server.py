# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Implementation of tool support over LSP."""
from __future__ import annotations

import copy
import json
import os
import pathlib
import re
import sys
import sysconfig
import traceback
from typing import Any, Optional, Sequence, Callable, Dict, List, Union


# **********************************************************
# Update sys.path before importing any bundled libraries.
# **********************************************************
def update_sys_path(path_to_add: str, strategy: str) -> None:
    """Add given path to `sys.path`."""
    if path_to_add not in sys.path and os.path.isdir(path_to_add):
        if strategy == "useBundled":
            sys.path.insert(0, path_to_add)
        elif strategy == "fromEnvironment":
            sys.path.append(path_to_add)


# Ensure that we can import LSP libraries, and other bundled libraries.
update_sys_path(
    os.fspath(pathlib.Path(__file__).parent.parent / "libs"),
    os.getenv("LS_IMPORT_STRATEGY", "useBundled"),
)

# **********************************************************
# Imports needed for the language server goes below this.
# **********************************************************
# pylint: disable=wrong-import-position,import-error
import lsp_jsonrpc as jsonrpc
import lsp_utils as utils
import lsprotocol.types as lsp
from pygls import server, uris, workspace

WORKSPACE_SETTINGS = {}
GLOBAL_SETTINGS = {}
RUNNER = pathlib.Path(__file__).parent / "lsp_runner.py"

MAX_WORKERS = 5
# TODO: Update the language server name and version.
LSP_SERVER = server.LanguageServer(
    name="TrojanSourceFinder", version="<server version>", max_workers=MAX_WORKERS
)


# **********************************************************
# Tool specific code goes below this.
# **********************************************************

# Reference:
#  LS Protocol:
#  https://microsoft.github.io/language-server-protocol/specifications/specification-3-16/
#
#  Sample implementations:
#  Pylint: https://github.com/microsoft/vscode-pylint/blob/main/bundled/tool
#  Black: https://github.com/microsoft/vscode-black-formatter/blob/main/bundled/tool
#  isort: https://github.com/microsoft/vscode-isort/blob/main/bundled/tool

TOOL_MODULE = "unisource"

TOOL_DISPLAY = "TrojanSourceFinder"

TOOL_ARGS = []  # default arguments always passed to your tool.


# **********************************************************
# Linting features start here
# **********************************************************

#  See `pylint` implementation for a full featured linter extension:
#  Pylint: https://github.com/microsoft/vscode-pylint/blob/main/bundled/tool


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: lsp.DidOpenTextDocumentParams) -> None:
    """LSP handler for textDocument/didOpen request."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)
    diagnostics: list[lsp.Diagnostic] = _linting_helper(document)
    LSP_SERVER.publish_diagnostics(document.uri, diagnostics)


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
def did_save(params: lsp.DidSaveTextDocumentParams) -> None:
    """LSP handler for textDocument/didSave request."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)
    diagnostics: list[lsp.Diagnostic] = _linting_helper(document)
    LSP_SERVER.publish_diagnostics(document.uri, diagnostics)


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def did_close(params: lsp.DidCloseTextDocumentParams) -> None:
    """LSP handler for textDocument/didClose request."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)
    # Publishing empty diagnostics to clear the entries for this file.
    LSP_SERVER.publish_diagnostics(document.uri, [])


"""
COMPUTER SYSTEMS SECURITY RELEVANT PORTION

TODO Figure out how to ouput the original code with Bidi Characters removed to the user
TODO Maybe figure out what the stuff above does like OPEN CLOSE and SAVE
TODO Publish this extension publically before the due date that would be a flex for the prof and for recruiters 
"""
BIDI_UNICODE_CHARS = {
    "\u202A": "LRE",
    "\u202B": "RLE",
    "\u202D": "LRO",
    "\u202E": "RLO",
    "\u2066": "LRI",
    "\u2067": "RLI",
    "\u2068": "FSI",
    "\u202C": "PDF",
    "\u2069": "PDI",
}

INVISIBLE_UNICODE_CHARS = {
    "\u200B": "Zero-Width Space ZWSP)",
    "\u200C": "Zero-Width Non-Joiner (ZWNJ)",
    "\u200D": "Zero-Width Joiner (ZWJ)",
    "\uFEFF": "Zero-Width Non-Breaking Space (ZWNBSP)",
    "\u00AD": "Soft Hyphen (SHY)",
    "\u200E": "Left-To-Right Mark (LTRM)",
    "\u200F": "Right-To-Left Mark (RTLM)",
    "\u2060": "Word Joiner (WJ)",
    "\u2061": "Function Application (FAP)",
    "\u2063": "Invisible Separator (IS)",
    "\u2064": "Invisible Plus (IP)",
    "\u2062": "Invisible Times (IT)"
}

HOMOGLYPH_UNICODE_CHARS = {
    # Greek Alphabet
    "\u037F": "Greek Capital Letter Yot",
    "\u0391": "Greek Capital Letter Alpha",
    "\u0392": "Greek Capital Letter Beta",
    "\u0395": "Greek Capital Letter Epsilon",
    "\u0396": "Greek Capital Letter Zeta",
    "\u0397": "Greek Capital Letter Eta",
    "\u0399": "Greek Capital Letter Iota",
    "\u039A": "Greek Capital Letter Kappa",
    "\u039C": "Greek Capital Letter Mu",
    "\u039D": "Greek Capital Letter Nu",
    "\u039F": "Greek Capital Letter Omicron",
    "\u03A1": "Greek Capital Letter Rho",
    "\u03A4": "Greek Capital Letter Tau",
    "\u03A5": "Greek Capital Letter Upsilon",
    "\u03A7": "Greek Capital Letter Chi",
    "\u03F2": "Greek Lunate Sigma Symbol",
    "\u03F3": "Greek Letter Yot",
    "\u03F9": "Greek Capital Lunate Sigma Symbol",
    # Cyrillic Alphabet
    "\u0405": "Cyrillic Capital Letter Dze",
    "\u0406": "Cyrillic Capital Letter Byelorussian-Ukrainian I",
    "\u0408": "Cyrillic Capital Letter Je",
    "\u0410": "Cyrillic Capital Letter A",
    "\u0412": "Cyrillic Capital Letter Ve",
    "\u0415": "Cyrillic Capital Letter Ie",
    "\u0417": "Cyrillic Capital Letter Ze",
    "\u041D": "Cyrillic Capital Letter En",
    "\u041E": "Cyrillic Capital Letter O",
    "\u0420": "Cyrillic Capital Letter Er",
    "\u0421": "Cyrillic Capital Letter Es",
    "\u0422": "Cyrillic Capital Letter Te",
    "\u0425": "Cyrillic Capital Letter Ha",
    "\u04AE": "Cyrillic Capital Letter Straight U",
    "\u04C0": "Cyrillic Letter Palochka",
    "\u04CF": "Cyrillic Small Letter Palochka",
}

def _check_bidi_unicode(line: str, line_num: int) -> list[lsp.Diagnostic]:
    """Checks for Unicode characters defined above"""
    diagnostics = []
    for char, name in BIDI_UNICODE_CHARS.items():
        index = line.find(char)
        while index != -1:
            # Check what kind of attack 
            single_comment_index = line.find('#')
            return_index = line.find("return")
            multi_comment_index = line.find("\'\'\'")
            if single_comment_index != -1 or multi_comment_index != -1:
                msg = f"Trojan Source Comment Out Attack Detected.\nBidi Unicode Chracter {name} detected. An attacker has introduced a Bidirectional Unicode character to comment code and disturb logic."
            elif return_index != -1:
                msg = f"Trojan Source Early Return Attack Detected.\nBidi Unicode Character {name} detected. An attacker has introduced a Bidirectional Unicode character to return your code early."
            else:
                msg = f"Bidi Unicode Character {name} detected.\nAn attacker as introduced a Bidirectional Unicode Character to disturb code logic."

            # Create diagnostic
            position = lsp.Position(line=line_num, character=index)
            diagnostic = lsp.Diagnostic(
                range=lsp.Range(start=position, end=position),
                message=msg,
                severity=lsp.DiagnosticSeverity.Error,
                source=TOOL_MODULE
            )
            diagnostics.append(diagnostic)
            index = line.find(char, index + 1) 

    return diagnostics


def _check_invisible_unicode_(line: str, line_num: int) -> list[lsp.Diagnostic]:
    """Checks for Unicode characters defined above"""
    diagnostics = []
    for char, name in INVISIBLE_UNICODE_CHARS.items():
        index = line.find(char)
        while index != -1:
            position = lsp.Position(line=line_num, character=index)
            diagnostic = lsp.Diagnostic(
                range=lsp.Range(start=position, end=position),
                message=f"Trojan Source Invisible Attack Detected\nUnicode Character {name} detected. An attacker may be trying to disturb code logic.",
                severity=lsp.DiagnosticSeverity.Warning,
                source=TOOL_MODULE
            )
            diagnostics.append(diagnostic)
            index = line.find(char, index + 1) 

    # Return the list of diagnostics for this line
    return diagnostics


def _check_homoglyph_unicode(line: str, line_num: int) -> list[lsp.Diagnostic]:
    """Checks for Homoglyph Unicode characters defined above"""
    diagnostics = []
    for char, name in HOMOGLYPH_UNICODE_CHARS.items():
        index = line.find(char)
        while index != -1:
            # Check what kind of attack 
            single_comment_index = line.find('#')
            return_index = line.find("return")
            multi_comment_index = line.find("\'\'\'")
            if single_comment_index != -1 or multi_comment_index != -1:
                msg = f"Trojan Source Comment Out Attack Detected.\nHomoglyph Unicode Chracter {name} detected. An attacker has introduced a Homoglyph Unicode character to comment code and disturb logic."
            elif return_index != -1:
                msg = f"Trojan Source Early Return Attack Detected.\nHomoglyph Unicode Character {name} detected. An attacker has introduced a Homoglyph Unicode character to return your code early."
            else:
                msg = f"Homoglyph Unicode Character {name} detected.\nAn attacker as introduced a Homoglyph Unicode Character to disturb code logic."

            # Create diagnostic
            position = lsp.Position(line=line_num, character=index)
            diagnostic = lsp.Diagnostic(
                range=lsp.Range(start=position, end=position),
                message=msg,
                severity=lsp.DiagnosticSeverity.Error,
                source=TOOL_MODULE
            )
            diagnostics.append(diagnostic)
            index = line.find(char, index + 1) 

    return diagnostics


def _linting_helper(document: workspace.Document) -> list[lsp.Diagnostic]:
    # diagnostics are the messages that appear they are objects that are put into a list and returned at the end here
    diagnostics: list[lsp.Diagnostic] = []
    # get the lines of the document
    lines = document.lines
    for i, line in enumerate(lines):
        diagnostics.extend(_check_bidi_unicode(line, i))
        diagnostics.extend(_check_invisible_unicode_(line, i))
        diagnostics.extend(_check_homoglyph_unicode(line, i)) 

    # return the list
    return diagnostics



# **********************************************************
# Required Language Server Initialization and Exit handlers.
# **********************************************************
@LSP_SERVER.feature(lsp.INITIALIZE)
def initialize(params: lsp.InitializeParams) -> None:
    """LSP handler for initialize request."""
    log_to_output(f"CWD Server: {os.getcwd()}")

    paths = "\r\n   ".join(sys.path)
    log_to_output(f"sys.path used to run Server:\r\n   {paths}")

    GLOBAL_SETTINGS.update(**params.initialization_options.get("globalSettings", {}))

    settings = params.initialization_options["settings"]
    _update_workspace_settings(settings)
    log_to_output(
        f"Settings used to run Server:\r\n{json.dumps(settings, indent=4, ensure_ascii=False)}\r\n"
    )
    log_to_output(
        f"Global settings:\r\n{json.dumps(GLOBAL_SETTINGS, indent=4, ensure_ascii=False)}\r\n"
    )


@LSP_SERVER.feature(lsp.EXIT)
def on_exit(_params: Optional[Any] = None) -> None:
    """Handle clean up on exit."""
    jsonrpc.shutdown_json_rpc()


@LSP_SERVER.feature(lsp.SHUTDOWN)
def on_shutdown(_params: Optional[Any] = None) -> None:
    """Handle clean up on shutdown."""
    jsonrpc.shutdown_json_rpc()


def _get_global_defaults():
    return {
        "path": GLOBAL_SETTINGS.get("path", []),
        "interpreter": GLOBAL_SETTINGS.get("interpreter", [sys.executable]),
        "args": GLOBAL_SETTINGS.get("args", []),
        "importStrategy": GLOBAL_SETTINGS.get("importStrategy", "useBundled"),
        "showNotifications": GLOBAL_SETTINGS.get("showNotifications", "off"),
    }


def _update_workspace_settings(settings):
    if not settings:
        key = os.getcwd()
        WORKSPACE_SETTINGS[key] = {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }
        return

    for setting in settings:
        key = uris.to_fs_path(setting["workspace"])
        WORKSPACE_SETTINGS[key] = {
            "cwd": key,
            **setting,
            "workspaceFS": key,
        }


def _get_settings_by_path(file_path: pathlib.Path):
    workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

    while file_path != file_path.parent:
        str_file_path = str(file_path)
        if str_file_path in workspaces:
            return WORKSPACE_SETTINGS[str_file_path]
        file_path = file_path.parent

    setting_values = list(WORKSPACE_SETTINGS.values())
    return setting_values[0]


def _get_document_key(document: workspace.Document):
    if WORKSPACE_SETTINGS:
        document_workspace = pathlib.Path(document.path)
        workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

        # Find workspace settings for the given file.
        while document_workspace != document_workspace.parent:
            if str(document_workspace) in workspaces:
                return str(document_workspace)
            document_workspace = document_workspace.parent

    return None


def _get_settings_by_document(document: workspace.Document | None):
    if document is None or document.path is None:
        return list(WORKSPACE_SETTINGS.values())[0]

    key = _get_document_key(document)
    if key is None:
        # This is either a non-workspace file or there is no workspace.
        key = os.fspath(pathlib.Path(document.path).parent)
        return {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }

    return WORKSPACE_SETTINGS[str(key)]


# *****************************************************
# Internal execution APIs.
# *****************************************************
def _run_tool_on_document(
    document: workspace.Document,
    use_stdin: bool = False,
    extra_args: Optional[Sequence[str]] = None,
) -> utils.RunResult | None:
    """Runs tool on the given document.

    if use_stdin is true then contents of the document is passed to the
    tool via stdin.
    """
    if extra_args is None:
        extra_args = []
    if str(document.uri).startswith("vscode-notebook-cell"):
        return None

    if utils.is_stdlib_file(document.path):
        return None

    # deep copy here to prevent accidentally updating global settings.
    settings = copy.deepcopy(_get_settings_by_document(document))

    code_workspace = settings["workspaceFS"]
    cwd = settings["cwd"]

    use_path = False
    use_rpc = False
    if settings["path"]:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif settings["interpreter"] and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use JSON-RPC to the subprocess
        # running under that interpreter.
        argv = [TOOL_MODULE]
        use_rpc = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [TOOL_MODULE]

    argv += TOOL_ARGS + settings["args"] + extra_args

    if use_stdin:
        # TODO: update these to pass the appropriate arguments to provide document contents
        # to tool via stdin.
        # For example, for pylint args for stdin looks like this:
        #     pylint --from-stdin <path>
        # Here `--from-stdin` path is used by pylint to make decisions on the file contents
        # that are being processed. Like, applying exclusion rules.
        # It should look like this when you pass it:
        #     argv += ["--from-stdin", document.path]
        # Read up on how your tool handles contents via stdin. If stdin is not supported use
        # set use_stdin to False, or provide path, what ever is appropriate for your tool.
        argv += []
    else:
        argv += [document.path]

    if use_path:
        # This mode is used when running executables.
        log_to_output(" ".join(argv))
        log_to_output(f"CWD Server: {cwd}")
        result = utils.run_path(
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source.replace("\r\n", "\n"),
        )
        if result.stderr:
            log_to_output(result.stderr)
    elif use_rpc:
        # This mode is used if the interpreter running this server is different from
        # the interpreter used for running this server.
        log_to_output(" ".join(settings["interpreter"] + ["-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")

        result = jsonrpc.run_over_json_rpc(
            workspace=code_workspace,
            interpreter=settings["interpreter"],
            module=TOOL_MODULE,
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source,
        )
        if result.exception:
            log_error(result.exception)
            result = utils.RunResult(result.stdout, result.stderr)
        elif result.stderr:
            log_to_output(result.stderr)
    else:
        # In this mode the tool is run as a module in the same process as the language server.
        log_to_output(" ".join([sys.executable, "-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")
        # This is needed to preserve sys.path, in cases where the tool modifies
        # sys.path and that might not work for this scenario next time around.
        with utils.substitute_attr(sys, "path", sys.path[:]):
            try:
                # TODO: `utils.run_module` is equivalent to running `python -m unisource`.
                # If your tool supports a programmatic API then replace the function below
                # with code for your tool. You can also use `utils.run_api` helper, which
                # handles changing working directories, managing io streams, etc.
                # Also update `_run_tool` function and `utils.run_module` in `lsp_runner.py`.
                result = utils.run_module(
                    module=TOOL_MODULE,
                    argv=argv,
                    use_stdin=use_stdin,
                    cwd=cwd,
                    source=document.source,
                )
            except Exception:
                log_error(traceback.format_exc(chain=True))
                raise
        if result.stderr:
            log_to_output(result.stderr)

    log_to_output(f"{document.uri} :\r\n{result.stdout}")
    return result


def _run_tool(extra_args: Sequence[str]) -> utils.RunResult:
    """Runs tool."""
    # deep copy here to prevent accidentally updating global settings.
    settings = copy.deepcopy(_get_settings_by_document(None))

    code_workspace = settings["workspaceFS"]
    cwd = settings["workspaceFS"]

    use_path = False
    use_rpc = False
    if len(settings["path"]) > 0:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif len(settings["interpreter"]) > 0 and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use JSON-RPC to the subprocess
        # running under that interpreter.
        argv = [TOOL_MODULE]
        use_rpc = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [TOOL_MODULE]

    argv += extra_args

    if use_path:
        # This mode is used when running executables.
        log_to_output(" ".join(argv))
        log_to_output(f"CWD Server: {cwd}")
        result = utils.run_path(argv=argv, use_stdin=True, cwd=cwd)
        if result.stderr:
            log_to_output(result.stderr)
    elif use_rpc:
        # This mode is used if the interpreter running this server is different from
        # the interpreter used for running this server.
        log_to_output(" ".join(settings["interpreter"] + ["-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")
        result = jsonrpc.run_over_json_rpc(
            workspace=code_workspace,
            interpreter=settings["interpreter"],
            module=TOOL_MODULE,
            argv=argv,
            use_stdin=True,
            cwd=cwd,
        )
        if result.exception:
            log_error(result.exception)
            result = utils.RunResult(result.stdout, result.stderr)
        elif result.stderr:
            log_to_output(result.stderr)
    else:
        # In this mode the tool is run as a module in the same process as the language server.
        log_to_output(" ".join([sys.executable, "-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")
        # This is needed to preserve sys.path, in cases where the tool modifies
        # sys.path and that might not work for this scenario next time around.
        with utils.substitute_attr(sys, "path", sys.path[:]):
            try:
                # TODO: `utils.run_module` is equivalent to running `python -m unisource`.
                # If your tool supports a programmatic API then replace the function below
                # with code for your tool. You can also use `utils.run_api` helper, which
                # handles changing working directories, managing io streams, etc.
                # Also update `_run_tool_on_document` function and `utils.run_module` in `lsp_runner.py`.
                result = utils.run_module(
                    module=TOOL_MODULE, argv=argv, use_stdin=True, cwd=cwd
                )
            except Exception:
                log_error(traceback.format_exc(chain=True))
                raise
        if result.stderr:
            log_to_output(result.stderr)

    log_to_output(f"\r\n{result.stdout}\r\n")
    return result


# *****************************************************
# Logging and notification.
# *****************************************************
def log_to_output(
    message: str, msg_type: lsp.MessageType = lsp.MessageType.Log
) -> None:
    LSP_SERVER.show_message_log(message, msg_type)


def log_error(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Error)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onError", "onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Error)


def log_warning(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Warning)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Warning)


def log_always(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Info)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Info)


# *****************************************************
# Start the server.
# *****************************************************
if __name__ == "__main__":
    LSP_SERVER.start_io()
