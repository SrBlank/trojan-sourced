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
lsp, lsprotocol, and all tool support over lsp (lines 4 - 14 in "lsp_server.py")
2. For `keylogger.py`:
pynput.keyboard

## Instructions
1. Clone and open this project repository folder in VS Code
2. Install `nox`: `python -m pip install nox`
3. Install node packages using `npm install`. If the below steps do not work, run `npm install` in a terminal inside the project repository.
4. Go to `src/extension.ts`. Go to `Run and Debug`(Ctrl + Shift + D). Under the drop-down menu next to the green arrow on the top-left corner, make sure to select `Debug Extension and Python`. Click on the green arrow to start debugging (F5).
5. In the current window, the file `_debug_server.py` will open with a breakpoint. Click on the yellow arrow or press F5 to continue
6. VS Code will also start a new window with the extension installed `[Extension Development Host]` as soon as you start debugging in step (4). Go to `demos` and check each python files, detected problems should display under `Problems` in the bottom panel, if the panel is not showing yet, press Ctrl + Shift + M.

These steps can also be done inside a virtual environment if conflict errors occur. 

