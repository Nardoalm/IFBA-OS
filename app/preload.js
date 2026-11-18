const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('ifbaOS', {
  getProfile: () => ipcRenderer.invoke('ifba-os:profile')
});
