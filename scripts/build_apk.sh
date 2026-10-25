#!/usr/bin/env bash
# build_apk.sh — Bash version of the APK build pipeline.
set -euo pipefail

APP_DIR="/home/z/my-project/android-app"
ANDROID_HOME="${ANDROID_HOME:-/home/z/my-project/android-sdk}"
BUILD_TOOLS="$ANDROID_HOME/build-tools/34.0.0"
PLATFORM_JAR="$ANDROID_HOME/platforms/android-34/android.jar"
OUT_DIR="/home/z/my-project/download"

export JAVA_HOME="${JAVA_HOME:-$(ls -d /home/z/my-project/jdk/jdk-21* 2>/dev/null || echo $JAVA_HOME)}"
export PATH="$JAVA_HOME/bin:$PATH"

AAPT2="$BUILD_TOOLS/aapt2"
D8="$BUILD_TOOLS/d8"
ZIPALIGN="$BUILD_TOOLS/zipalign"
APKSIGNER="$BUILD_TOOLS/apksigner"

WORK="$APP_DIR/build"; GEN="$APP_DIR/gen"; OBJ="$APP_DIR/obj"
mkdir -p "$WORK" "$GEN" "$OBJ" "$OUT_DIR"

echo "==> [1/6] Compiling resources with aapt2..."
"$AAPT2" compile --dir "$APP_DIR/res" -o "$WORK/resources.zip"

echo "==> [2/6] Linking resources + manifest + assets into base APK..."
"$AAPT2" link -I "$PLATFORM_JAR" --manifest "$APP_DIR/AndroidManifest.xml" -A "$APP_DIR/assets" -R "$WORK/resources.zip" --java "$GEN" --min-sdk-version 24 --target-sdk-version 34 --auto-add-overlay -o "$WORK/app-base.apk"

echo "==> [3/6] Compiling Java sources with javac..."
rm -rf "$OBJ"/*
R_JAVA=$(find "$GEN" -name "R.java" | head -1)
javac -source 11 -target 11 -classpath "$PLATFORM_JAR" -d "$OBJ" "$APP_DIR/src/com/techflow/visitingcard/MainActivity.java" "$R_JAVA"

echo "==> [4/6] Converting .class to DEX with d8..."
CLASS_FILES=$(find "$OBJ" -name "*.class")
"$D8" --min-api 24 --lib "$PLATFORM_JAR" --output "$WORK" $CLASS_FILES

echo "==> [5/6] Adding DEX to APK and zipaligning..."
cp "$WORK/app-base.apk" "$WORK/app-unsigned.apk"
( cd "$WORK" && zip -j -q app-unsigned.apk classes.dex )
"$ZIPALIGN" -f -p 4 "$WORK/app-unsigned.apk" "$WORK/app-aligned.apk"

echo "==> [6/6] Signing APK with debug keystore..."
KEYSTORE="$APP_DIR/debug.keystore"
if [ ! -f "$KEYSTORE" ]; then
  keytool -genkeypair -v -keystore "$KEYSTORE" -alias androiddebugkey -dname "CN=Digital Visiting Card, OU=Mobile, O=TechFlow Solutions, L=Bengaluru, ST=Karnataka, C=IN" -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000
fi

FINAL_APK="$OUT_DIR/digital-visiting-card.apk"
"$APKSIGNER" sign --ks "$KEYSTORE" --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out "$FINAL_APK" "$WORK/app-aligned.apk"

echo ""
echo "========================================"
echo "  APK BUILD SUCCESSFUL (Bash)"
echo "========================================"
ls -lh "$FINAL_APK"
"$APKSIGNER" verify --verbose "$FINAL_APK" 2>&1 | head -4
echo "APK path: $FINAL_APK"
