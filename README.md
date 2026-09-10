# toskinstaller_deepseek
# TOSKINSTALLER

**Portable Windows app packager — turn any project into an installer or a portable executable.**

Developed by **ToskeraLAB ART/TECH House**

---

## What is TOSKINSTALLER?

TOSKINSTALLER is a portable Windows application that takes the files of a finished software project, converts it into a standalone executable, and packages it into a distributable final format — a traditional installer (`.EXE` / `.MSI`) or a portable decompressor.

It is both a **compiler wrapper** and a **packager**: the user drops in a project, TOSKINSTALLER detects the language, uses the appropriate external build tool to produce a `.exe`, and then wraps that `.exe` into a fully customizable Setup Wizard or portable package.

---

## What it does

TOSKINSTALLER performs two stages:

### Stage 1 — Project → Executable
- Accepts the raw files of a project (e.g. a Python project, or an AI-generated "vibe code" project).
- Automatically detects the project language.
- Selects and runs the correct external build tool (PyInstaller, Nuitka, cx_Freeze for Python; pkg, electron-builder for Node; and so on).
- If the required tool is not installed, TOSKINSTALLER guides the user step by step until it is ready, then continues.

### Stage 2 — Executable → Final Package
- Wraps the generated executable into the final distributable format chosen by the user:
  - `.EXE` installer
  - `.MSI` installer
  - Portable decompressor (extracts the app to a folder and produces an executable entry point)
- Lets the user fully customize the Setup Wizard before building:
  - Logo
  - License text
  - Animated banners
  - Optional installation of partner apps (installed separately, not bundled with the main app)
  - Color themes
  - Install progress animation (at least 3 styles)
  - Start Menu and Desktop shortcuts
  - Target folder and decompression options
  - Digital signature (optional)
  - Architecture and compatibility
  - PT-BR / EN localization

Every option above is **configurable at runtime** — nothing is hard-coded.

---

## What it delivers

- **TOSKINSTALLER itself**: a portable Windows executable, ideally distributed as a single file.
- **The final package**: a single executable when the chosen format allows it, containing only the user's app and the configured install/decompression resources. TOSKINSTALLER is **never** embedded into the generated package.

When the generated package runs on the end user's machine, it will either:
- Install the app on the system, or
- Open guided windows to choose a target folder, decompress the portable app, and create Start Menu / Desktop shortcuts, and
- Optionally install configured partner apps, separately from the main app.

---

## Key principles

- **Portable** — no installation required to run TOSKINSTALLER.
- **Offline-first** — works without an internet connection, except when it needs to guide the user through installing a required build tool.
- **Configurable** — every wizard page, theme, animation, and packaging option is chosen by the user at runtime.
- **Reproducible** — builds are deterministic and scriptable.
- **GitHub-ready** — organized repository structure, clear folder conventions, commit-friendly.

---

## Status

This project is part of an open comparison test between multiple code AIs. Each AI produces its own version of TOSKINSTALLER in its own public repository, so results can be compared side by side.

---

## Brand

**ToskeraLAB ART/TECH House**

---

## License

To be defined by ToskeraLAB ART/TECH House.

---
---

nir pela ToskeraLAB ART/TECH House.
