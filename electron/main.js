"use strict";

const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("child_process");
const http = require("http");
const path = require("path");

const PORT = 8000;
let backendProcess = null;

// ---------------------------------------------------------------------------
// Locate the bundled PyInstaller binary
// ---------------------------------------------------------------------------

function getBackendExecutable() {
  const exeName =
    process.platform === "win32"
      ? "protein-purification-server.exe"
      : "protein-purification-server";

  if (app.isPackaged) {
    // When packaged by electron-builder, extraResources lands at process.resourcesPath/backend/
    return path.join(process.resourcesPath, "backend", exeName);
  }

  // Development: use the PyInstaller onedir output in dist/
  return path.join(
    __dirname,
    "..",
    "dist",
    "protein-purification-server",
    exeName,
  );
}

// ---------------------------------------------------------------------------
// Start the backend
// ---------------------------------------------------------------------------

function startBackend() {
  const exe = getBackendExecutable();
  backendProcess = spawn(exe, [], {
    stdio: ["ignore", "pipe", "pipe"],
  });

  backendProcess.stdout.on("data", (d) =>
    process.stdout.write("[backend] " + d),
  );
  backendProcess.stderr.on("data", (d) =>
    process.stderr.write("[backend] " + d),
  );
  backendProcess.on("exit", (code) => {
    if (code !== 0 && code !== null) {
      console.error(`Backend exited unexpectedly with code ${code}`);
    }
  });
}

// ---------------------------------------------------------------------------
// Poll the health endpoint until the backend is ready
// ---------------------------------------------------------------------------

function waitForBackend(maxAttempts = 40, intervalMs = 500) {
  return new Promise((resolve, reject) => {
    let attempts = 0;

    function check() {
      const req = http.get(
        `http://127.0.0.1:${PORT}/api/health`,
        (res) => {
          res.resume(); // discard body
          if (res.statusCode === 200) {
            resolve();
          } else {
            retry();
          }
        },
      );
      req.on("error", retry);
      req.setTimeout(1000, () => {
        req.destroy();
        retry();
      });
    }

    function retry() {
      if (++attempts >= maxAttempts) {
        reject(new Error("Backend did not become ready in time"));
      } else {
        setTimeout(check, intervalMs);
      }
    }

    check();
  });
}

// ---------------------------------------------------------------------------
// Create the main window
// ---------------------------------------------------------------------------

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    title: "Protein Purification",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  win.loadURL(`http://127.0.0.1:${PORT}`);
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
  startBackend();

  try {
    await waitForBackend();
  } catch (err) {
    dialog.showErrorBox(
      "Startup Error",
      `Failed to start the backend server.\n\n${err.message}\n\nMake sure the app was built correctly.`,
    );
    app.quit();
    return;
  }

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) backendProcess.kill();
});
