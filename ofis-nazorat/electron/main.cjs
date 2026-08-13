const { app, BrowserWindow, session } = require('electron')
const path = require('path')
const { pathToFileURL } = require('url')

const isDev = !app.isPackaged

function modelsDir() {
  if (isDev) {
    return path.join(__dirname, '..', 'public', 'models')
  }
  // extraResources → resources/models (asar tashqarisida)
  return path.join(process.resourcesPath, 'models')
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 960,
    minHeight: 680,
    title: 'Ofis nazorat',
    backgroundColor: '#0b1220',
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      // lokal model .bin fayllarini yuklash uchun
      webSecurity: false,
    },
  })

  session.defaultSession.setPermissionRequestHandler((_wc, permission, callback) => {
    if (permission === 'media' || permission === 'mediaKeySystem') {
      callback(true)
      return
    }
    callback(false)
  })

  if (isDev) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:5177')
  } else {
    const indexHtml = path.join(__dirname, '..', 'dist', 'index.html')
    const modelsUrl = pathToFileURL(modelsDir()).href.replace(/\/?$/, '/')
    win.loadFile(indexHtml, {
      query: { models: modelsUrl },
    })
  }
}

app.whenReady().then(() => {
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
