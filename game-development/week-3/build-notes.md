# Build notes: Android test build and iOS steps

## Android test build: **not produced**
The assignment asks for an Android test build. None was made, because building an APK or app bundle needs the Android SDK and a Java build toolchain, and this Mac has neither set up for Android, and the Unity editor is not installed. Nothing here claims otherwise.

**What does exist instead is an installable web app (PWA):** `manifest.webmanifest`, `icon-192.png`, `icon-512.png` and `sw.js` make the game installable from Chrome on Android ("Add to Home screen"), where it runs full screen in landscape and works offline once cached. It must be served over HTTPS (or `localhost`). This is a stand-in for a test build, not an APK, and I could not verify the install flow on a device. `node --test sw.test.js` checks the service worker's logic and that every pre-cached file exists, but the browser I had refused to register service workers at all, so offline behavior itself was not confirmed.

### How to make a real Android build from this code
1. Install Android Studio (it brings the Android SDK) and Node.
2. In a new folder: `npm init -y && npm i @capacitor/core @capacitor/cli @capacitor/android`
3. `npx cap init "Gem Run" in.skillnexis.gemrun --web-dir=www`, then copy `index.html`, `style.css`, `core.js`, `audio.js`, `game.js`, `manifest.webmanifest` and the icons into `www/`.
4. `npx cap add android && npx cap sync android && npx cap open android`
5. In Android Studio choose Build, then Build Bundle(s) / APK(s), then Build APK(s). A debug APK is signed with the debug key and is only for testing.
6. Install on a device with USB debugging on: `adb install app-debug.apk`.
For a Play Store release you create your own upload key, build a signed Android App Bundle (`.aab`), and use a Play Console internal-testing track.

## iOS build steps (documented, not performed)
iOS builds need a Mac with Xcode and, for a real device or TestFlight, an Apple Developer account, none of which were used here.
1. With the same Capacitor project: `npm i @capacitor/ios && npx cap add ios && npx cap sync ios && npx cap open ios`.
2. In Xcode select the App target, Signing & Capabilities, choose your Team and a unique Bundle Identifier. Automatic signing creates the provisioning profile.
3. Choose a simulator and press Run to test. For a device, enable Developer Mode on it and pick it as the run destination.
4. For TestFlight: Product, Archive, Distribute App, App Store Connect, then add testers in App Store Connect.
5. Before review: an app icon set, a privacy policy URL, and the App Privacy answers (this game collects nothing and stores only a save file on the device).

## Permissions and privacy
The game asks for no device permissions. It stores a small save (unlocked levels, scores, volume) in the browser's local storage on the device and sends nothing anywhere.
