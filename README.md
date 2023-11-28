# Instructions for setting up and testing extension

## Minimum Requirements
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
The functions performing malicious code detection are implemented in `bundle/tool/lsp_server.py` between lines 111 and 270. 
There are three detecting functions:
1.  `_check_bidi_unicode` detects characters that change the direction of a certain text string.
2.  `_check_invisible_unicode_` detects characters that are invisible to the human eye but are read by the compiler.
3.  `_check_homoglph_unicode` detects characters that look almost identical to regular letter characters but have different Unicode values.

Additionally, `_linting_helper` passes each line in open documents in the current workspace into the above functions, then return a list of lsp.Diagnostic objects, informing the user what the malicious code is trying to do. 


