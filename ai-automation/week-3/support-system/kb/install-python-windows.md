# Installing Python on Windows
1. Download the latest Python 3 installer from python.org/downloads.
2. On the first screen, tick **Add python.exe to PATH**, then click Install Now.
3. Open a new Command Prompt and type `python --version`. You should see Python 3.12 or newer.

If Windows opens the Microsoft Store when you type `python`, turn off the "App execution aliases" for python.exe in Settings → Apps → Advanced app settings, then open a new Command Prompt.

If you see "'python' is not recognized as an internal or external command", PATH was not set: run the installer again, choose Modify, and tick "Add Python to environment variables".
