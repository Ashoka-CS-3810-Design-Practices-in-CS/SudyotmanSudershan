# Build the Windows executable

1. On Windows, open this project folder (the one containing `backend`, `data`, and `frontend`).
2. Double-click `build_exe.bat`. Alternatively, run it from PowerShell with `./build_exe.bat`.
3. The script installs PyInstaller and bundles the Python app, `frontend/index.html`, and `data/metro_network.json`. Node.js is not needed.
4. When it finishes, run `dist\DelhiMetroPlanner\DelhiMetroPlanner.exe`. It should open the app in your default browser at `http://127.0.0.1:5000`. Keep the executable running while using the app. Close its console window to stop the local server.
5. To share it, ZIP the **entire** `dist\DelhiMetroPlanner` folder. Do not send only the `.exe`; the `_internal` folder is required.
6. Test the ZIP on another Windows computer. PyInstaller builds are OS-specific, so build on Windows. The app needs internet access for any map tiles loaded from external tile servers.

The app listens on localhost only and is intended to run on the user's own computer.
