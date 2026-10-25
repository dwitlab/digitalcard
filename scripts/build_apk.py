#!/usr/bin/env python3
"""build_apk.py — Build the Digital Visiting Card APK using Python."""
from __future__ import annotations
import argparse, os, shutil, subprocess, sys
from pathlib import Path

BASE = Path("/home/z/my-project")
APP_DIR = BASE / "android-app"
ASSETS_DIR = APP_DIR / "assets"
RES_DIR = APP_DIR / "res"
SRC_DIR = APP_DIR / "src"
MANIFEST = APP_DIR / "AndroidManifest.xml"
WORK = APP_DIR / "build"; GEN = APP_DIR / "gen"; OBJ = APP_DIR / "obj"
OUT_DIR = BASE / "download"
FINAL_APK = OUT_DIR / "digital-visiting-card.apk"
KEYSTORE = APP_DIR / "debug.keystore"

def info(m): print(f"\033[1;34m==> {m}\033[0m")
def ok(m):   print(f"\033[1;32m  ✓ {m}\033[0m")
def die(m, code=1):
    print(f"\033[1;31mERROR: {m}\033[0m", file=sys.stderr); sys.exit(code)

def run(cmd, cwd=None, capture=False):
    if capture:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout, end=""); print(r.stderr, file=sys.stderr, end="")
            die(f"Command failed: {' '.join(str(c) for c in cmd)}")
        return r.stdout
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0: die(f"Command failed: {' '.join(str(c) for c in cmd)}")
    return ""

def discover_android_home(cli):
    if cli:
        p = Path(cli).resolve()
        if not p.exists(): die(f"--android-home not found: {p}")
        return p
    for env in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        v = os.environ.get(env)
        if v and Path(v).exists(): return Path(v)
    d = BASE / "android-sdk"
    if d.exists(): return d
    die("Android SDK not found. Set ANDROID_HOME or pass --android-home.")

def discover_java_home(cli):
    if cli:
        p = Path(cli).resolve()
        if not p.exists(): die(f"--java-home not found: {p}")
        return p
    v = os.environ.get("JAVA_HOME")
    if v and Path(v).exists(): return Path(v)
    d = BASE / "jdk"
    if d.exists():
        c = list(d.glob("jdk-21*"))
        if c: return c[0]
    if shutil.which("javac"): return Path(shutil.which("javac")).parent.parent
    die("JDK not found. Set JAVA_HOME or pass --java-home.")

def step1(aapt2):
    info("[1/6] Compiling resources with aapt2")
    if WORK.exists(): shutil.rmtree(WORK)
    WORK.mkdir(parents=True, exist_ok=True)
    run([str(aapt2), "compile", "--dir", str(RES_DIR), "-o", str(WORK / "resources.zip")])
    ok("resources.zip")

def step2(aapt2, pj):
    info("[2/6] Linking resources + manifest + assets into base APK")
    if GEN.exists(): shutil.rmtree(GEN)
    GEN.mkdir(parents=True, exist_ok=True)
    run([str(aapt2), "link", "-I", str(pj), "--manifest", str(MANIFEST), "-A", str(ASSETS_DIR),
         "-R", str(WORK / "resources.zip"), "--java", str(GEN),
         "--min-sdk-version", "24", "--target-sdk-version", "34", "--auto-add-overlay",
         "-o", str(WORK / "app-base.apk")])
    ok(f"app-base.apk ({(WORK / 'app-base.apk').stat().st_size} bytes)")

def step3(javac, pj):
    info("[3/6] Compiling Java sources with javac")
    if OBJ.exists(): shutil.rmtree(OBJ)
    OBJ.mkdir(parents=True, exist_ok=True)
    rj = next(GEN.rglob("R.java"), None)
    if rj is None: die("R.java not generated")
    mj = SRC_DIR / "com" / "techflow" / "visitingcard" / "MainActivity.java"
    out = run([str(javac), "-source", "11", "-target", "11", "-classpath", str(pj), "-d", str(OBJ), str(mj), str(rj)], capture=True)
    if out.strip(): print(out, end="")
    ok(f"{len(list(OBJ.rglob('*.class')))} .class files compiled")

def step4(d8, pj):
    info("[4/6] Converting .class to DEX with d8")
    cf = [str(p) for p in OBJ.rglob("*.class")]
    if not cf: die("No .class files to dex")
    run([str(d8), "--min-api", "24", "--lib", str(pj), "--output", str(WORK), *cf])
    if not (WORK / "classes.dex").exists(): die("classes.dex not produced")
    ok(f"classes.dex ({(WORK / 'classes.dex').stat().st_size} bytes)")

def step5(za):
    info("[5/6] Adding DEX to APK and zipaligning")
    u = WORK / "app-unsigned.apk"
    shutil.copy(WORK / "app-base.apk", u)
    run(["zip", "-j", "-q", str(u), str(WORK / "classes.dex")], cwd=WORK)
    a = WORK / "app-aligned.apk"
    run([str(za), "-f", "-p", "4", str(u), str(a)])
    ok(f"app-aligned.apk ({a.stat().st_size} bytes)")

def step6(apksigner, keytool):
    info("[6/6] Signing APK")
    if not KEYSTORE.exists():
        run([str(keytool), "-genkeypair", "-v", "-keystore", str(KEYSTORE), "-alias", "androiddebugkey",
             "-dname", "CN=Digital Visiting Card, OU=Mobile, O=TechFlow Solutions, L=Bengaluru, ST=Karnataka, C=IN",
             "-storepass", "android", "-keypass", "android", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000"], capture=True)
        ok(f"Generated keystore: {KEYSTORE}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if FINAL_APK.exists(): FINAL_APK.unlink()
    run([str(apksigner), "sign", "--ks", str(KEYSTORE), "--ks-key-alias", "androiddebugkey",
         "--ks-pass", "pass:android", "--key-pass", "pass:android", "--out", str(FINAL_APK), str(WORK / "app-aligned.apk")])
    ok(f"Signed APK: {FINAL_APK} ({FINAL_APK.stat().st_size} bytes)")

def verify(apksigner):
    info("Verifying signature")
    out = run([str(apksigner), "verify", "--verbose", str(FINAL_APK)], capture=True)
    for line in out.splitlines()[:5]: print(f"  {line}")
    info("Verifying card.html asset is bundled")
    out = run(["unzip", "-l", str(FINAL_APK)], capture=True)
    for line in out.splitlines():
        if "card.html" in line or "classes.dex" in line or "AndroidManifest" in line: print(f"  {line.strip()}")

def main():
    ap = argparse.ArgumentParser(description="Build the Digital Visiting Card APK (Python)")
    ap.add_argument("--android-home"); ap.add_argument("--java-home"); ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()
    ah = discover_android_home(args.android_home); jh = discover_java_home(args.java_home)
    bt = ah / "build-tools" / "34.0.0"; pj = ah / "platforms" / "android-34" / "android.jar"
    if not bt.exists(): die(f"build-tools;34.0.0 not found at {bt}")
    if not pj.exists(): die(f"platforms;android-34 not found at {pj}")
    aapt2 = bt / "aapt2"; d8 = bt / "d8"; za = bt / "zipalign"; apksigner = bt / "apksigner"
    javac = jh / "bin" / "javac"; keytool = jh / "bin" / "keytool"
    print(f"\033[1;36m=== Build Configuration ===\033[0m")
    print(f"  ANDROID_HOME : {ah}\n  JAVA_HOME    : {jh}\n  build-tools  : {bt}\n  platform-jar : {pj}\n")
    if args.clean and WORK.exists(): shutil.rmtree(WORK); ok("--clean: wiped build/")
    step1(aapt2); step2(aapt2, pj); step3(javac, pj); step4(d8, pj); step5(za); step6(apksigner, keytool); verify(apksigner)
    print(f"\n\033[1;32m========================================\033[0m")
    print(f"\033[1;32m  APK BUILD SUCCESSFUL (Python)\033[0m")
    print(f"\033[1;32m========================================\033[0m")
    print(f"  Output: {FINAL_APK}\n  Size  : {FINAL_APK.stat().st_size:,} bytes")

if __name__ == "__main__": main()
