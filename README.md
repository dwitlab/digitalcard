# Digital Visiting Card — APK Package

A self-contained Android APK that displays a digital visiting card with a QR code. The card UI is bundled inside the APK — it works **offline**, no internet needed to display the card.

The build pipeline is available in **three languages** — pick whichever you prefer:
- **Python** — `scripts/build_apk.py`
- **Node.js** — `scripts/build_apk.mjs`
- **Bash** — `scripts/build_apk.sh`

All three produce identical APKs.

---

## 📦 What's inside

```
├── README.md                          ← this file
├── digital-visiting-card.apk          ← PREBUILT APK — install on Android now
├── card-preview.html                  ← open in any browser to preview the card
├── android-app/                       ← APK source code
│   ├── AndroidManifest.xml
│   ├── assets/card.html               ← the self-contained card UI (HTML+CSS+JS inline)
│   ├── src/com/techflow/visitingcard/MainActivity.java
│   └── res/                           ← launcher icons, strings, styles, network config
└── scripts/
    ├── build_card_asset.py            ← regenerate card.html (edit card data here)
    ├── gen_android_icons.py           ← regenerate launcher icons
    ├── build_apk.py                   ← BUILD SCRIPT (Python)
    ├── build_apk.mjs                  ← BUILD SCRIPT (Node.js)
    └── build_apk.sh                   ← BUILD SCRIPT (Bash)
```

---

## 🚀 Install the APK on Android

1. Copy `digital-visiting-card.apk` to your phone
2. **Settings → Apps → Special access → Install unknown apps** → enable for your file manager
3. Tap the APK → **Install** (if Play Protect warns, tap "Install anyway")
4. Open "Digital Visiting Card" — the card displays immediately (works offline)

---

## 🛠 Rebuild the APK — three options

### Prerequisites (all three options)
- **JDK 17+** with `javac` (set `JAVA_HOME`)
- **Android SDK** with `build-tools;34.0.0` and `platforms;android-34` (set `ANDROID_HOME`)
- **Python 3.8+** with `qrcode` and `Pillow` (for regenerating the card HTML / icons):
  ```bash
  pip install qrcode Pillow
  ```

### Option 1: Python
```bash
python3 scripts/build_card_asset.py        # regenerate card HTML (edit data first)
python3 scripts/gen_android_icons.py       # (optional) regenerate launcher icons
python3 scripts/build_apk.py               # build the signed APK
# or: python3 scripts/build_apk.py --android-home /path/to/sdk --java-home /path/to/jdk
```

### Option 2: Node.js
```bash
python3 scripts/build_card_asset.py        # regenerate card HTML (uses Python)
python3 scripts/gen_android_icons.py       # regenerate launcher icons
node scripts/build_apk.mjs                 # build the signed APK
# or: node scripts/build_apk.mjs --android-home /path/to/sdk --java-home /path/to/jdk
```

### Option 3: Bash
```bash
export ANDROID_HOME=/path/to/android-sdk
export JAVA_HOME=/path/to/jdk-21
python3 scripts/build_card_asset.py
python3 scripts/gen_android_icons.py
bash scripts/build_apk.sh
```

---

## ✏️ Customize the card

Edit `scripts/build_card_asset.py` — change the `CARD` dictionary and `SHARE_URL` at the top:
```python
CARD = {
    "firstName": "Your",
    "lastName": "Name",
    "name": "Your Name",
    "title": "Your Title",
    "company": "Your Company",
    "phone": "+91XXXXXXXXXX",
    "whatsapp": "91XXXXXXXXXX",
    "website": "https://your-site.com",
    "linkedin": "https://linkedin.com/in/you",
    "email": "you@your-site.com",
    "location": "Your City",
}
SHARE_URL = "https://your-card-url.com"  # QR code points here
```

Then regenerate and rebuild with any of the three build options above.

---

## 🔧 Troubleshooting

### "App not installed"
Settings → Apps → Special access → Install unknown apps → enable for your file manager.

### Google Play Protect blocks installation
Tap "More details" → "Install anyway". Safe — the APK only requests INTERNET permission.

### App shows blank screen
The current version (v1.2) bundles the card HTML inside the APK and works 100% offline. Make sure you're installing the latest APK (~88 KB, version 1.2).

### "There was a problem parsing the package"
- APK corrupted — re-download
- Android < 7.0 — APK requires API 24+
- APK modified after signing — rebuild from source

### Build error: "javac: command not found"
You need a full JDK (not just JRE). On Ubuntu/Debian: `apt install openjdk-21-jdk`. On other systems, download Temurin JDK from https://adoptium.net/

### Build error: "build-tools not found"
Install via sdkmanager:
```bash
sdkmanager "build-tools;34.0.0" "platforms;android-34"
```

---

## 🔐 APK signing
Signed with a self-signed debug keystore (10000-day validity). For Play Store distribution:
```bash
keytool -genkeypair -keystore release.keystore -alias release \
  -keyalg RSA -keysize 2048 -validity 10000
# Edit the build script to use release.keystore instead of debug.keystore
```

---

## 🛠 Tech stack
- **Card UI:** HTML5 + CSS3 + vanilla JS (bundled as Android asset, works offline)
- **QR code:** Pre-generated as base64 PNG using Python `qrcode` library
- **APK:** Android WebView (Java), built with aapt2 + d8 + zipalign + apksigner (no Gradle)
- **Build scripts:** Python 3, Node.js 18+, and Bash — all produce identical APKs
- **Min Android:** 7.0 (API 24) · **Target:** Android 14 (API 34)
- **APK size:** ~88 KB
