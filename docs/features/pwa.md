# Progressive Web App (PWA)

Streaklet is a Progressive Web App, meaning you can install it on your device and use it like a native application.

## Features

- **Installable** - Add to home screen on mobile or desktop
- **Offline Support** - Service worker caching for offline access
- **App-like Experience** - Runs in standalone mode without browser chrome
- **Fast Loading** - Cached assets load instantly

## Installing on Mobile

### iOS (iPhone/iPad)

1. Open Streaklet in **Safari**
2. Tap the **Share** button (square with arrow)
3. Scroll down and tap **"Add to Home Screen"**
4. Name it "Streaklet" (or your preference)
5. Tap **Add**

The app icon will appear on your home screen.

### Android

1. Open Streaklet in **Chrome**
2. Tap the **menu** (three dots) in the top-right
3. Tap **"Add to Home screen"** or **"Install app"**
4. Name it "Streaklet" (or your preference)
5. Tap **Add**

The app icon will appear on your home screen or app drawer.

## Installing on Desktop

### Chrome, Edge, or Brave

1. Open Streaklet in the browser
2. Look for the **install icon** (⊕ or monitor icon) in the address bar
3. Click it and select **Install**
4. The app will open in a standalone window

Alternatively:
- Chrome: Menu → **More Tools** → **Create Shortcut** → Check "Open as window"
- Edge: Menu → **Apps** → **Install this site as an app**

### Firefox

Firefox doesn't support PWA installation directly, but you can create a desktop shortcut:
1. Visit Streaklet
2. Click the **menu** (three bars)
3. Select **"Pin to Taskbar"** or **"Pin to Start"**

## Offline Support

Streaklet caches key assets for offline use:

- **Static files** - HTML, CSS, JavaScript
- **Images** - Icons, logos
- **Fonts** - Typography assets

### What Works Offline

- Viewing the interface
- Navigating between pages
- Viewing cached data

### What Requires Internet

- Loading new data from the server
- Syncing Fitbit data
- Creating/updating tasks
- Checking off tasks (unless cached)

## Service Worker

The service worker provides offline functionality and caching:

- **Cache-first strategy** - Static assets load from cache
- **Network-first for API** - API calls attempt network first, fall back to cache
- **Automatic updates** - Service worker updates automatically when new versions are deployed

### Clearing Cache

If you experience issues, clear the cache:

1. Open browser DevTools (F12)
2. Go to **Application** → **Storage**
3. Click **"Clear site data"**
4. Reload the page

## App Manifest

Streaklet includes a web app manifest (`manifest.json`) that defines:

- App name and icons
- Display mode (standalone)
- Theme colors
- Start URL

### Customizing

You can customize the manifest by editing `app/static/manifest.json` in your deployment.

## Benefits of PWA

### Mobile Experience

- **No App Store** - Install directly from browser
- **Instant Updates** - Always get latest version
- **Less Storage** - Smaller than native apps
- **Cross-Platform** - Same app on iOS and Android

### Desktop Experience

- **Quick Access** - Launch from desktop or taskbar
- **Distraction-Free** - No browser tabs or address bar
- **Native Feel** - Looks and behaves like a desktop app

## Browser Support

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Install | ✅ | ⚠️ Limited | ✅ | ✅ |
| Offline | ✅ | ✅ | ✅ | ✅ |
| Push Notifications | ✅ | ✅ | ❌ | ✅ |

Note: Streaklet doesn't currently use push notifications.

## Uninstalling

### Mobile

Uninstall like any other app:
- **iOS**: Long-press the icon → **Remove App**
- **Android**: Long-press the icon → **Uninstall** or drag to **Uninstall**

### Desktop

- **Chrome/Edge**: Click the app icon in the address bar → **Uninstall**
- **Or**: OS app settings → Find "Streaklet" → Uninstall

## Troubleshooting

### Installation button not showing

- Ensure you're using HTTPS (or localhost)
- Clear browser cache and reload
- Check if already installed (may hide the button)

### Offline mode not working

- Check if service worker is registered: DevTools → Application → Service Workers
- Verify cache storage: DevTools → Application → Cache Storage
- Clear cache and reload to re-register service worker

### App not updating

- Close all instances of the app
- Clear cache and reload
- Uninstall and reinstall the PWA

## Learn More

- [Progressive Web Apps (MDN)](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [Service Workers (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web App Manifest (MDN)](https://developer.mozilla.org/en-US/docs/Web/Manifest)
