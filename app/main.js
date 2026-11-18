const { app, BrowserWindow, dialog, ipcMain, shell } = require('electron');
const os = require('node:os');
const path = require('node:path');

const academicHosts = new Set(['suap.ifba.edu.br', 'ava.ifba.edu.br']);

ipcMain.handle('ifba-os:profile', () => {
  try {
    const username = os.userInfo().username;
    if (!username || username === 'ubuntu') return { displayName: 'Estudante' };
    return { displayName: username.charAt(0).toLocaleUpperCase('pt-BR') + username.slice(1) };
  } catch {
    return { displayName: 'Estudante' };
  }
});

function openAcademicPortal(rawUrl) {
  try {
    const url = new URL(rawUrl);
    if (url.protocol !== 'https:' || !academicHosts.has(url.hostname)) return;
    shell.openExternal(url.href).catch(error => {
      dialog.showErrorBox('Não foi possível abrir o portal', error.message);
    });
  } catch {
    // Invalid or non-HTTPS URLs are ignored.
  }
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1480,
    height: 840,
    minWidth: 640,
    minHeight: 500,
    show: false,
    frame: false,
    autoHideMenuBar: true,
    backgroundColor: '#121414',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  window.webContents.setWindowOpenHandler(({ url }) => {
    openAcademicPortal(url);
    return { action: 'deny' };
  });
  window.webContents.on('will-navigate', event => event.preventDefault());
  window.loadFile(path.join(__dirname, 'index.html'));
  window.once('ready-to-show', () => {
    window.maximize();
    window.show();
  });
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
