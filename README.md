# Trojan Sourced
The `trojan-sourced` VSCode extension is dedicated to detecting malicious code manipulations caused by Unicode characters. These Unicode characters can be invisible, appear like normal characters, and manipulate code without the programmer being aware of the fact. These attacks have been deemed `Trojan Source` attacks from the paper `Trojan Source: Invisble Vulnerabilities` by Boucher, Nicholas and Ross Anderson [1]. Our VSCode extension proposes a solution by detecting each attack proposed in the paper and making the user aware of the fact. We further expand on the paper as well by expanding on the list of malicouous unicode characters.


## Requirements
1. VS Code 1.64.0
2. Python 3.8
3. node 14.19.0
4. npm 8.3.0
5. Python extension for VS Code
6. Typescript + Webpack Problem Matcher extension for VS Code
7. ESLint for VS Code

## Dependencies
1. For `lsp_server.py`:
lsprotocol, and all tool support over lsp (lines 4 - 14 in "lsp_server.py")
2. For `keylogger.py`:
pynput

## Instructions
1. Clone and open this project repository folder in VS Code
2. Install `nox`: `python -m pip install nox`
3. Install node packages using `npm install` in a terminal inside the project repository.
4. Go to `src/extension.ts`. Go to `Run and Debug`(Ctrl + Shift + D). Under the drop-down menu next to the green arrow on the top-left corner, make sure to select `Debug Extension and Python`. Click on the green arrow to start debugging (F5).
5. In the current window, the file `_debug_server.py` will open with a breakpoint. Click on the yellow arrow or press F5 to continue.
6. VS Code will also start a new window with the extension installed `[Extension Development Host]` as soon as you start debugging in step (4). With each python files under the folder  `demos` open, detected problems should display under `PROBLEMS` in the bottom panel, if the panel is not showing yet, press Ctrl + Shift + M.

These steps can also be done inside a virtual environment if conflict errors occur. 

## Project Functionality
The functions performing malicious code detection are implemented in `bundle/tool/lsp_server.py` between lines 107 and 295.
There are three detecting functions:
1.  `_check_bidi_unicode` detects Bidirectional Unicode characters. These characters will change the original lay out of text on runtime cauing program logic to change. In particular, there are two kinds of attacks this function detects:

    1. `Early Return Attack`: When a return statement is moved to be called early.
    1. `Comment Out Attack`: When a comment is moved to remove if statements or change code logic in general.
1.  `_check_invisible_unicode_` detects characters that are invisible to the human eye but are read by the compiler. This attack can cause functions that are not meant to be called, be called.
1.  `_check_homoglph_unicode` detects characters that look almost identical to regular letter characters but have different Unicode values. Similar to the invisible attack, functions that are not meant to be called can appear normal in the calling as it looks the same.

Additionally, `_linting_helper` passes each line in open documents in the current workspace into the above functions, then return a list of lsp.Diagnostic objects, informing the user what the malicious code is trying to do. 

The functions above are implemented and functional. Unfortuantely, the only porition of the project we were not able to accomplish was giving the end user the code with the attack removed. The attack is highlighted and an error is thrown along with a diagnostic message.

## References
[1] Boucher, Nicholas, and Ross Anderson. "Trojan Source:   Invisible Vulnerabilities." 32nd USENIX
Security Symposium (USENIX Security 23), 2023, Anaheim, CA, USENIX Association,
https://arxiv.org/abs/2111.00169.