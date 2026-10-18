# Shadow Caravan

A compact third-person dark-fantasy desert adventure for Android, built with **Godot 4.3** (GDScript, GL Compatibility renderer). Package id: `com.zafronix.shadowcaravan`. Landscape, offline, arm64-v8a, no ads, no sign-in, no paid SDKs.

You play Rahil, last guard of a vanished caravan. Explore ruins and a temple, solve the rune puzzle, fight scarabs and wraiths, open the Ancient Gate with three relic fragments and defeat the Hollow Warden to finish the quest *The Lost Caravan*.

> **Read this first - what has and has not been verified**
>
> This project was written and checked in a cloud sandbox that has **no Android SDK and no Android device**.
>
> | Verified here | Not verified here |
> |---|---|
> | All 48 scripts and 4 scenes compile and load in Godot 4.3 (`tests/validate.gd`: 109 items, 0 failures). | **A real GitHub Actions run.** The workflow has never been executed on GitHub. Its shell steps were run locally against the real Godot 4.3 binary and templates with the Android SDK tools replaced by stand-ins. |
> | A headless playthrough (`tests/smoke_playthrough.gd`) drives the real game code through the quest chain, puzzle, combat, boss, save/load, pause and death/respawn: 68 checks, 68 pass. | **Running on a phone or tablet.** Touch controls, frame rate, battery, thermals, memory and audio output were never tested on hardware. No frame-rate figures are claimed. |
> | A real Godot 4.3 Android export (official export templates, arm64) produced a ~30 MB APK containing all game scripts, the correct package name and arm64 native libraries. That APK was then signed and zip-aligned with a third-party signer and its v1/v2/v3 signatures verified. | The official Android SDK `apksigner` / `zipalign` (used by CI), installing the APK, and launching it. |
> | The look of every menu, HUD and panel, from rendered screenshots at 1280x720. | Other aspect ratios and very small phone screens. |
> | The 36 audio files exist and load. | **Nobody has listened to them.** They are synthesised; mix and taste are unknown. |
>
> If the first CI run fails, see [Troubleshooting](#troubleshooting) - the most likely causes are listed there.

## Screenshots

Rendered from the desktop build in a headless Linux sandbox with software OpenGL - **not** captured on a phone. Some shots use a save state set up by a test script (character level, items).

| | |
|---|---|
| ![Main menu](docs/screenshots/01-main-menu.jpg) | ![Camp and HUD](docs/screenshots/02-camp-hud.jpg) |
| ![Temple of Echoes](docs/screenshots/03-temple.jpg) | ![Hollow Warden](docs/screenshots/04-hollow-warden.jpg) |
| ![Inventory](docs/screenshots/05-inventory.jpg) | ![Rune puzzle](docs/screenshots/06-rune-puzzle.jpg) |

---

## 1. Build the APK with GitHub Actions

You need a free GitHub account. You do not need Godot, Android Studio or any secret.

1. **Create an empty repository** on GitHub (e.g. `shadow-caravan`). Do not tick "Add a README" - the repo must start empty.
2. **Unzip `ShadowCaravan.zip`.** It contains one folder, `ShadowCaravan/`. The files **inside** that folder (`project.godot`, `.github/`, `scripts/`, ...) must end up at the **root** of the repository.
3. **Upload from a terminal** (recommended - it keeps the hidden `.github` folder):
   ```bash
   cd ShadowCaravan
   git init -b main
   git add .
   git commit -m "Shadow Caravan"
   git remote add origin https://github.com/<your-user>/shadow-caravan.git
   git push -u origin main
   ```
   *Web upload alternative:* on the empty repo page choose "uploading an existing file" and drag in the **contents** of the `ShadowCaravan` folder. On macOS press Cmd+Shift+. in Finder first so `.github` is visible; on Windows tick "Hidden items". If `.github/workflows/android-build.yml` is not in the repo afterwards, the Actions tab will show nothing.
4. Pushing to `main` starts the build automatically. To start it by hand: **Actions** tab -> **Android Build** -> **Run workflow** (tick *Also run the headless gameplay smoke test* if you want the extra 5-minute check).
5. Wait for the run to finish (expect roughly 8-15 minutes the first time, less when the Godot download cache is warm).
6. Open the finished run. Under **Artifacts** download **ShadowCaravan-debug-apk**. It is a zip containing `ShadowCaravan.apk`. The run summary shows the APK size and SHA-256.

If a run fails, open the failed step and read its log; the *export-log* artifact is attached to failed runs.

### What the workflow does (`.github/workflows/android-build.yml`)

1. Checks out the repo, installs Temurin JDK 17.
2. Downloads Godot 4.3-stable (Linux) and the official export templates, **verifying SHA-512 checksums** published with the 4.3-stable release; only the Android templates are kept and cached.
3. Installs the Android SDK pieces Godot needs (platform-tools, build-tools 34.0.0, platform 34) using the SDK that GitHub's `ubuntu-24.04` runners already include.
4. Generates a throw-away **debug keystore** (`keytool`) and writes Godot's editor settings so it can find the SDK, JDK and keystore.
5. `godot --headless --import`, then `tests/validate.gd` (compiles every script and scene; fails the build on any error).
6. Optionally runs the smoke test (manual runs only).
7. `godot --headless --export-debug "Android" build/ShadowCaravan.apk`.
8. Verifies the APK: non-empty, larger than 10 MB, valid zip, contains the manifest, the arm64 engine library and the package name, and passes `apksigner verify`.
9. Uploads `build/ShadowCaravan.apk` as an artifact (30 days).

Actions are pinned to exact release tags (`actions/checkout@v4.2.2`, `actions/setup-java@v4.7.1`, `actions/cache@v4.2.3`, `actions/upload-artifact@v4.6.2`) and the runner image to `ubuntu-24.04`. For stricter supply-chain hygiene you can replace each tag with the full commit SHA it points to.

### Secrets and signing

- **No secrets are required.** The APK is signed with a debug keystore generated fresh on every run (password `android`, which is the Android convention for debug keys and protects nothing).
- Because the key changes every run, **an update built by a later run will not install over an earlier one** - uninstall the old build first (or install with `adb install -r` after uninstalling). Save data is stored inside the app and is lost on uninstall.
- This is a **debug build for testing and sideloading**. It is not ready for Google Play. A store release needs your own release keystore (kept in GitHub *Secrets*, never committed), a release export and, for new Play apps, an AAB. The repository's `.gitignore` already excludes `*.keystore`, `*.jks` and `export_credentials.cfg`.

## 2. Install on a phone

1. Copy `ShadowCaravan.apk` to the device (or open the artifact download link on it).
2. Allow "install unknown apps" for the app you opened it from (Android Settings -> Apps -> Special access).
3. Tap the APK and install. The game starts in landscape.

With a USB cable and `adb`: `adb install ShadowCaravan.apk`.

## 3. Open and run in the Godot editor

1. Install **Godot 4.3** (standard build, not .NET) from godotengine.org.
2. Import `project.godot` and press **F5**.
3. On a desktop the game works with mouse and keyboard (touch is emulated from the mouse).

Command-line checks (Godot on your `PATH`):

```bash
godot --headless --import --path .                        # first run only, builds the import cache
godot --headless --path . -s tests/validate.gd            # compile check, exit code 1 on failure
godot --headless --path . -s tests/smoke_playthrough.gd   # ~5 min gameplay test, prints PASS/FAIL
```

The headless renderer prints many harmless `mesh_get_surface_count ... Parameter "m" is null` lines; ignore them.

To build locally instead of on GitHub you need the Android SDK, JDK 17, a debug keystore and the Godot 4.3 export templates configured in *Editor -> Editor Settings -> Export -> Android*; then `godot --headless --path . --export-debug "Android" build/ShadowCaravan.apk`.

## 4. Controls

| Action | Touch | Keyboard / mouse |
|---|---|---|
| Move (walk, push to the rim to run) | Floating joystick, left half | WASD or arrows |
| Look | Drag the right half of the screen | Hold right mouse button and drag |
| Sword attack | Sword button | J or F |
| Dodge roll (short invulnerability) | Roll button | K or Ctrl |
| Jump | Jump button | Space |
| Sprint | Lightning button (hold) | Shift |
| Interact (talk, open, rest, activate) | Appears near things you can use | E |
| Pause / Inventory / Journal / Map | Buttons at the top right | Esc or P / I or Tab / Q / M |

Android's Back button closes the open panel, or opens the pause menu.

## 5. How to play (contains spoilers)

<details>
<summary>Quest walkthrough</summary>

1. Talk to **Elder Sahir** by the fire in the Caravan Camp (south-west corner). Follow the compass diamond and the objective tracker.
2. Collect **three relic fragments**:
   - **Hidden Alcove** - a boulder ring north of the Broken Court. The way in is a gap on its north-west side; glowing cairns lead to it.
   - **Temple of Echoes** (east) - read the carved **Weeping Stone** first for the clue, then set the three rune pillars in the temple (*Moon, Eye, Sun*) and press **Attune**. The result is saved.
   - **Wraith Hollow** (west plateau) - defeat the wraith guardians; keep moving, their orbs can be dodged by rolling.
3. At the **Ancient Gate** (north) activate the gate; it consumes the fragments and opens.
4. Beyond it, the **Hollow Warden** sleeps. It wakes when you approach. Attacks are telegraphed: a ground ring for the slam (jump or roll through it), a lane for the charge (sidestep; if it hits a wall it is dazed and takes more damage), fans of fire bolts, and summoned scarabs at 70% and 35% health. It gets faster below half health.
5. Take the relic from the altar to complete the quest (250 coins, Caravan Blade, XP).

Also in the world: five chests, waystones (fast travel and checkpoints, shown on the map), a moon well, and a camp where you can **rest** (full heal and save), **craft** potions and gear, **upgrade** health / blade / stamina and **store** items.
</details>

Death returns you to your last checkpoint with your belongings. Enemies you defeated come back after a rest.

## 6. Project layout

```
ShadowCaravan/                 <- repository root
  project.godot  export_presets.cfg  icon.svg
  .github/workflows/android-build.yml
  assets/audio/                36 procedurally generated WAVs
  assets/fonts/                STIX General (SIL OFL)
  scenes/                      splash, main_menu, intro, game (thin; content is built in code)
  scripts/autoload/            GameState (save, quest, inventory), Controls, AudioMgr, Router
  scripts/data/                items, recipes, locations, palette
  scripts/world/               terrain, world builder, areas, player, enemies, boss, camera, props
  scripts/ui/                  HUD, touch controls, menus and panels
  scripts/game.gd              gameplay controller
  tests/                       validate.gd, smoke_playthrough.gd, screenshot and probe tools
  docs/screenshots/            rendered screenshots used by this README
  tools/generate_audio.py      regenerates assets/audio
  build/                       APK output (git-ignored)
```

Save data lives in `user://shadow_caravan_save.json` (JSON with a SHA-256 integrity field, written atomically with a `.bak` copy; invalid or corrupted files are rejected and the backup is tried) and settings in `user://shadow_caravan_settings.cfg`. *Settings -> Reset Save Data* deletes the save; the main menu offers Continue / Play (new game, with confirmation if a save exists).

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| No "Android Build" workflow in the Actions tab | `.github/workflows/android-build.yml` is not at the repository root (often because the `ShadowCaravan` folder itself was uploaded, or the hidden `.github` folder was skipped). Re-upload the folder *contents*. |
| Workflow does not start on push | It only runs for the `main` branch. Rename your branch or use **Run workflow**. Also check Actions are enabled for the repo (Settings -> Actions). |
| "Install Android SDK components" fails | The job expects GitHub's hosted `ubuntu-24.04` runner with the preinstalled SDK in `$ANDROID_HOME`. Self-hosted runners need the SDK installed and `ANDROID_HOME` set. If a package version is gone, change `ANDROID_BUILD_TOOLS` / `ANDROID_PLATFORM` at the top of the workflow. |
| Export step: "Cannot export project ... configuration errors" | The message names the missing piece (templates, SDK path, debug keystore, `apksigner`). It should not happen with the workflow as shipped; check the preceding steps' logs. |
| Download or checksum step fails | A network blip (re-run) or the Godot release assets moved. The checksum values in the workflow come from the official `SHA512-SUMS.txt` of release 4.3-stable. |
| Verify step: "APK is suspiciously small" | Export produced a stub. Read the *export-log* artifact. |
| APK will not install: "App not installed" | An older build signed with a different debug key is installed - uninstall it. Or the phone is 32-bit only (this build is arm64-v8a only). |
| Installs but crashes at start | Not tested on devices - please capture `adb logcat -s godot` and open an issue. Try quality *Low* in Settings if it is a memory or GPU problem (you must reach the menu for that). |
| Touch controls feel off | Camera sensitivity, invert-Y and vibration are in Settings. Button sizes and positions are in `scripts/ui/touch_controls.gd`. |
| No sound | Audio is optional: the game plays without it. Check the Music/Effects sliders and the device's media volume. |

## Known limitations

- No real-device testing of any kind (see the table at the top). Performance is unmeasured; the three quality levels (Low / Medium / High) change MSAA, render scale, shadows, glow, particle counts, dynamic lights and view distance, but their effect on frame rate has not been profiled.
- Debug-signed sideload build only; no release/AAB pipeline.
- Small world (about 200 m x 200 m playable square, one level, one quest, one boss). The "level transition" is the gate into the Warden's arena and fast travel between waystones, not a separate scene.
- Art is deliberately low-poly and procedural; characters use a simple code-driven rig rather than authored animation clips. Audio is synthesised and unreviewed by ear.
- English only. Landscape only. Controller and tablet-specific layouts are not implemented.
- The headless smoke test checks game rules, not feel; it cannot tell you whether the fights are fun or the controls comfortable.

## License

Code and original assets: MIT - see [LICENSE](LICENSE). Fonts and other notices: [ASSET_LICENSES.md](ASSET_LICENSES.md). Built with [Godot Engine](https://godotengine.org) (MIT).
