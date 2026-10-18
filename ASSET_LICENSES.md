# Asset licenses

Shadow Caravan ships with **no third-party art, models, textures, music or sound samples**.

| Asset | Where | Origin | License |
|---|---|---|---|
| Source code (GDScript, scenes, project files) | `scripts/`, `scenes/`, `project.godot`, `tests/`, `tools/`, `.github/` | Written for this project | MIT (see `LICENSE`) |
| 3D world, characters, enemies, boss, props, sky | built at runtime by code (`scripts/world/*.gd`) | Procedural geometry and shaders, original | MIT |
| UI icons, ornaments, runes, portrait, splash emblem | drawn at runtime by code (`scripts/ui/icons.gd`, `ornament.gd`, `intro.gd`, `splash.gd`) | Procedural vector drawing, original | MIT |
| `icon.svg` (launcher icon) | project root | Original | MIT |
| Sound effects, ambience and music loops (36 WAV files) | `assets/audio/` | Synthesised from scratch (sine / noise synthesis, no samples) by `tools/generate_audio.py` | MIT |
| STIX General (regular + bold) fonts | `assets/fonts/` | STIX Fonts by the Science and Technology Information Exchange (STIX) Fonts project, as redistributed with matplotlib (converted from OTF to TTF) | SIL Open Font License 1.1 - full text in `assets/fonts/LICENSE_STIX.txt` |
| Godot Engine 4.3 (not stored in this repository; downloaded by CI and linked into the exported APK) | - | godotengine.org | MIT - https://godotengine.org/license |

Body text that is not set in STIX General uses Godot's built-in default font, which is bundled inside the engine and covered by Godot's own third-party notices (https://godotengine.org/license).

## Regenerating the audio

```
pip install numpy
python3 tools/generate_audio.py
```

The generator is deterministic (fixed random seed), so the same files are produced every time.

## If you add assets

Keep this table up to date. Only add material you made yourself or that carries a license allowing redistribution inside a game, and put the license text next to the asset.
