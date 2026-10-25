#!/usr/bin/env node
/**
 * build_apk.mjs — Build the Digital Visiting Card APK using Node.js.
 */
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, rmSync, copyFileSync, unlinkSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const BASE = '/home/z/my-project';
const APP_DIR = join(BASE, 'android-app');
const ASSETS_DIR = join(APP_DIR, 'assets');
const RES_DIR = join(APP_DIR, 'res');
const SRC_DIR = join(APP_DIR, 'src');
const MANIFEST = join(APP_DIR, 'AndroidManifest.xml');
const WORK = join(APP_DIR, 'build');
const GEN = join(APP_DIR, 'gen');
const OBJ = join(APP_DIR, 'obj');
const OUT_DIR = join(BASE, 'download');
const FINAL_APK = join(OUT_DIR, 'digital-visiting-card.apk');
const KEYSTORE = join(APP_DIR, 'debug.keystore');

const C = { reset: '\x1b[0m', cyan: '\x1b[1;36m', blue: '\x1b[1;34m', green: '\x1b[1;32m', red: '\x1b[1;31m' };
const info = (m) => console.log(`${C.blue}==> ${m}${C.reset}`);
const ok = (m) => console.log(`${C.green}  ✓ ${m}${C.reset}`);
const die = (m, code = 1) => { console.error(`${C.red}ERROR: ${m}${C.reset}`); process.exit(code); };

function parseArgs() {
  const args = { clean: false, androidHome: null, javaHome: null };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--clean') args.clean = true;
    else if (argv[i] === '--android-home') args.androidHome = argv[++i];
    else if (argv[i] === '--java-home') args.javaHome = argv[++i];
    else if (argv[i] === '-h' || argv[i] === '--help') {
      console.log('Usage: node build_apk.mjs [--android-home PATH] [--java-home PATH] [--clean]'); process.exit(0);
    }
  }
  return args;
}

function discoverAndroidHome(cli) {
  if (cli) { if (!existsSync(cli)) die(`--android-home not found: ${cli}`); return cli; }
  for (const env of ['ANDROID_HOME', 'ANDROID_SDK_ROOT']) {
    if (process.env[env] && existsSync(process.env[env])) return process.env[env];
  }
  const d = join(BASE, 'android-sdk');
  if (existsSync(d)) return d;
  die('Android SDK not found. Set ANDROID_HOME or pass --android-home.');
}

function discoverJavaHome(cli) {
  if (cli) { if (!existsSync(cli)) die(`--java-home not found: ${cli}`); return cli; }
  if (process.env.JAVA_HOME && existsSync(process.env.JAVA_HOME)) return process.env.JAVA_HOME;
  const d = join(BASE, 'jdk');
  if (existsSync(d)) {
    const dirs = readdirSync(d).filter(x => x.startsWith('jdk-21'));
    if (dirs.length) return join(d, dirs[0]);
  }
  const which = spawnSync('which', ['javac'], { encoding: 'utf8' });
  if (which.status === 0 && which.stdout.trim()) {
    return join(which.stdout.trim(), '..', '..');
  }
  die('JDK not found. Set JAVA_HOME or pass --java-home.');
}

function run(cmd, args, opts = {}) {
  const { cwd, capture = false } = opts;
  if (capture) {
    const r = spawnSync(cmd, args, { cwd, encoding: 'utf8' });
    if (r.status !== 0) {
      process.stdout.write(r.stdout || ''); process.stderr.write(r.stderr || '');
      die(`Command failed: ${cmd} ${args.join(' ')}`);
    }
    return r.stdout;
  }
  const r = spawnSync(cmd, args, { cwd, stdio: 'inherit' });
  if (r.status !== 0) die(`Command failed: ${cmd} ${args.join(' ')}`);
  return '';
}

function findRJava(genDir) {
  function walk(dir) {
    for (const e of readdirSync(dir)) {
      const full = join(dir, e);
      const st = statSync(full);
      if (st.isDirectory()) { const f = walk(full); if (f) return f; }
      else if (e === 'R.java') return full;
    }
    return null;
  }
  return walk(genDir);
}

function globClass(objDir) {
  const out = [];
  (function walk(dir) {
    for (const e of readdirSync(dir)) {
      const full = join(dir, e); const st = statSync(full);
      if (st.isDirectory()) walk(full);
      else if (e.endsWith('.class')) out.push(full);
    }
  })(objDir);
  return out;
}

function step1(aapt2) {
  info('[1/6] Compiling resources with aapt2');
  if (existsSync(WORK)) rmSync(WORK, { recursive: true, force: true });
  mkdirSync(WORK, { recursive: true });
  run(aapt2, ['compile', '--dir', RES_DIR, '-o', join(WORK, 'resources.zip')]);
  ok('resources.zip');
}

function step2(aapt2, pj) {
  info('[2/6] Linking resources + manifest + assets into base APK');
  if (existsSync(GEN)) rmSync(GEN, { recursive: true, force: true });
  mkdirSync(GEN, { recursive: true });
  run(aapt2, ['link', '-I', pj, '--manifest', MANIFEST, '-A', ASSETS_DIR,
    '-R', join(WORK, 'resources.zip'), '--java', GEN,
    '--min-sdk-version', '24', '--target-sdk-version', '34', '--auto-add-overlay',
    '-o', join(WORK, 'app-base.apk')]);
  ok(`app-base.apk (${statSync(join(WORK, 'app-base.apk')).size} bytes)`);
}

function step3(javac, pj) {
  info('[3/6] Compiling Java sources with javac');
  if (existsSync(OBJ)) rmSync(OBJ, { recursive: true, force: true });
  mkdirSync(OBJ, { recursive: true });
  const rj = findRJava(GEN);
  if (!rj) die('R.java not generated');
  const mj = join(SRC_DIR, 'com', 'techflow', 'visitingcard', 'MainActivity.java');
  const out = run(javac, ['-source', '11', '-target', '11', '-classpath', pj, '-d', OBJ, mj, rj], { capture: true });
  if (out.trim()) process.stdout.write(out);
  ok(`${globClass(OBJ).length} .class files compiled`);
}

function step4(d8, pj) {
  info('[4/6] Converting .class to DEX with d8');
  const cf = globClass(OBJ);
  if (!cf.length) die('No .class files to dex');
  run(d8, ['--min-api', '24', '--lib', pj, '--output', WORK, ...cf]);
  if (!existsSync(join(WORK, 'classes.dex'))) die('classes.dex not produced');
  ok(`classes.dex (${statSync(join(WORK, 'classes.dex')).size} bytes)`);
}

function step5(za) {
  info('[5/6] Adding DEX to APK and zipaligning');
  const u = join(WORK, 'app-unsigned.apk');
  copyFileSync(join(WORK, 'app-base.apk'), u);
  run('zip', ['-j', '-q', u, join(WORK, 'classes.dex')], { cwd: WORK });
  const a = join(WORK, 'app-aligned.apk');
  run(za, ['-f', '-p', '4', u, a]);
  ok(`app-aligned.apk (${statSync(a).size} bytes)`);
}

function step6(apksigner, keytool) {
  info('[6/6] Signing APK');
  if (!existsSync(KEYSTORE)) {
    run(keytool, ['-genkeypair', '-v', '-keystore', KEYSTORE, '-alias', 'androiddebugkey',
      '-dname', 'CN=Digital Visiting Card, OU=Mobile, O=TechFlow Solutions, L=Bengaluru, ST=Karnataka, C=IN',
      '-storepass', 'android', '-keypass', 'android', '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000'], { capture: true });
    ok(`Generated keystore: ${KEYSTORE}`);
  }
  mkdirSync(OUT_DIR, { recursive: true });
  if (existsSync(FINAL_APK)) unlinkSync(FINAL_APK);
  run(apksigner, ['sign', '--ks', KEYSTORE, '--ks-key-alias', 'androiddebugkey',
    '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', FINAL_APK, join(WORK, 'app-aligned.apk')]);
  ok(`Signed APK: ${FINAL_APK} (${statSync(FINAL_APK).size} bytes)`);
}

function verify(apksigner) {
  info('Verifying signature');
  const out = run(apksigner, ['verify', '--verbose', FINAL_APK], { capture: true });
  out.split('\n').slice(0, 5).forEach(line => line && console.log(`  ${line}`));
  info('Verifying card.html asset is bundled');
  const listing = run('unzip', ['-l', FINAL_APK], { capture: true });
  listing.split('\n').forEach(line => {
    if (line.includes('card.html') || line.includes('classes.dex') || line.includes('AndroidManifest'))
      console.log(`  ${line.trim()}`);
  });
}

function main() {
  const args = parseArgs();
  const ah = discoverAndroidHome(args.androidHome);
  const jh = discoverJavaHome(args.javaHome);
  const bt = join(ah, 'build-tools', '34.0.0');
  const pj = join(ah, 'platforms', 'android-34', 'android.jar');
  if (!existsSync(bt)) die(`build-tools;34.0.0 not found at ${bt}`);
  if (!existsSync(pj)) die(`platforms;android-34 not found at ${pj}`);
  const aapt2 = join(bt, 'aapt2'); const d8 = join(bt, 'd8');
  const za = join(bt, 'zipalign'); const apksigner = join(bt, 'apksigner');
  const javac = join(jh, 'bin', 'javac'); const keytool = join(jh, 'bin', 'keytool');
  console.log(`${C.cyan}=== Build Configuration ===${C.reset}`);
  console.log(`  ANDROID_HOME : ${ah}\n  JAVA_HOME    : ${jh}\n  build-tools  : ${bt}\n  platform-jar : ${pj}\n`);
  if (args.clean && existsSync(WORK)) { rmSync(WORK, { recursive: true, force: true }); ok('--clean: wiped build/'); }
  step1(aapt2); step2(aapt2, pj); step3(javac, pj); step4(d8, pj); step5(za); step6(apksigner, keytool); verify(apksigner);
  console.log(`\n${C.green}========================================${C.reset}`);
  console.log(`${C.green}  APK BUILD SUCCESSFUL (Node.js)${C.reset}`);
  console.log(`${C.green}========================================${C.reset}`);
  console.log(`  Output: ${FINAL_APK}\n  Size  : ${statSync(FINAL_APK).size.toLocaleString()} bytes`);
}

main();
