# Audio Splitter Pro

Local Windows 10 desktop app — split any audio file into equal-length
clips (10s / 15s / 20s / anything), with a dark ocean-blue UI, waveform
preview, and play button.

---

## ⚠️ Important — read this first

I built the full app for you, but I run in a Linux environment and
**cannot compile a Windows `.exe` directly**. So you have two options:

### Option A — Run it directly with Python (fastest, works today)
1. Install **Python 3.10+** from https://python.org (check "Add to PATH" during install)
2. Install **FFmpeg** (needed to read mp3/m4a/etc):
   - Download from https://www.gyan.dev/ffmpeg/builds/ (get the "essentials" build)
   - Unzip it, add the `bin` folder to your Windows PATH
   - Test: open cmd → type `ffmpeg -version` → should show version info
3. Open cmd in this folder and run:
   ```
   pip install -r requirements.txt
   python main.py
   ```
4. App opens — select audio, dial the split interval, click OK, click Export.

### Option B — Build your own standalone `.exe` (one-time, then just double-click forever)
1. Do steps 1–3 from Option A (Python + FFmpeg + pip install)
2. Double-click **`build_exe.bat`** in this folder
3. Wait ~1 minute — it will create `dist\AudioSplitterPro.exe`
4. Copy that `.exe` anywhere and double-click to run — no Python needed after this,
   just keep FFmpeg on PATH.

---

## How to use the app

1. App opens with a splash screen showing the app name, then the main window.
2. Click **📂 Select Audio File** → pick your 1/2/3-minute audio from file explorer.
3. Waveform appears on the right. Click **▶** to preview/play the audio
   (playhead moves across the waveform live).
4. Turn the **dial** (or type in the box next to it) to set your split
   size — 10 sec, 15 sec, 20 sec, or literally anything from 5 to 600 sec.
5. Click **OK — Preview Split** → it tells you how many clips will be made.
6. Pick your **export format** from the dropdown — wav / mp3 / m4a / flac / ogg
7. Click **⬆ Export Clips** (top-right corner) → a Windows folder browser
   opens → choose your destination folder → clips save automatically as:
   ```
   yourfile_part001.mp3
   yourfile_part002.mp3
   yourfile_part003.mp3
   ...
   ```
   (extension matches whatever format you picked)

`.wav` needs no extra setup. `.mp3` / `.m4a` / `.ogg` need FFmpeg with
its encoder libraries installed (the standard "essentials" FFmpeg build
already includes these).

**No length limit** — a 10-minute audio at a 10-second split will
correctly produce 60 clips, a 1-hour file at 15-second split produces
240 clips, etc. The last clip just contains whatever remains (won't be
cut off or dropped).

---

## Files in this folder

| File | Purpose |
|---|---|
| `main.py` | The full application source code |
| `requirements.txt` | Python packages needed |
| `build_exe.bat` | One-click script to turn this into a standalone `.exe` |
| `README.md` | This file |

---

## Option C — Make it a REAL installer (Start Menu + Desktop shortcut + Uninstaller)

This is what you want if you'll use the app regularly and want it to open
straight from the Start Menu like any normal Windows app.

1. First finish **Option B** above (so `dist\AudioSplitterPro.exe` exists)
2. Download & install **Inno Setup** (free): https://jrsoftware.org/isdl.php
3. Open `installer.iss` (in this folder) by double-clicking it — it opens in Inno Setup
4. Click **Build → Compile** (or press `Ctrl+F9`)
5. It creates `installer_output\AudioSplitterPro_Setup.exe`
6. Double-click **that** file — a normal Windows install wizard runs:
   - Installs the app properly under Program Files
   - Adds a **Start Menu** entry
   - Optionally adds a **Desktop icon** (checkbox during install)
   - Adds a proper **Uninstaller** (shows up in "Add or Remove Programs")

After this, you just search "Audio Splitter Pro" in the Start Menu (or
double-click the desktop icon) and it opens directly — no Python, no
terminal, nothing. Only requirement: keep FFmpeg installed on the PC
(one-time setup from Option A, step 2).

---

## Option D — No terminal at all (build the .exe using a free website — GitHub)

This is the easiest way if the terminal / Python setup is giving you
trouble. You never touch a command prompt — everything happens by
clicking on a website, and a free Microsoft-owned cloud computer builds
your `.exe` for you.

1. Go to https://github.com and create a **free account** (just email + password)
2. Once logged in, click the **green "New"** button (or the `+` icon top-right → "New repository")
3. Give it any name, e.g. `audio-splitter` → tick **"Public"** → click **"Create repository"**
4. On the new repo page, click **"uploading an existing file"** (a blue link
   in the middle of the page)
5. Now **drag and drop the entire contents of this folder** (or use "choose your files")
   — select `main.py`, `requirements.txt`, `build_exe.bat`, `installer.iss`,
   `README.md`, and the whole `.github` folder — into the upload box

   ⚠️ The `.github` folder starts with a dot, so Windows may hide it by
   default. To see it: open File Explorer → **View tab** → tick
   **"Hidden items"**. Then it'll show up and you can drag it in too.
6. Scroll down, click green **"Commit changes"**
7. Click the **"Actions"** tab at the top of your repo
8. You'll see a build running automatically (yellow dot → green tick
   once done, takes ~2-3 minutes)
9. Click on that finished run → scroll down to **"Artifacts"** →
   click **"AudioSplitterPro-Windows-EXE"** to download a zip
10. Unzip it — inside is your **`AudioSplitterPro.exe`**, ready to run
    on any Windows 10 PC. No Python needed to run it (FFmpeg still
    needed for mp3/m4a, same as before).

Every time you (or I) update `main.py` in the future, just re-upload
the changed file the same way — GitHub automatically rebuilds a fresh
`.exe` for you, no terminal, ever.

---

## Notes / things you can ask me to change next
- Add drag-and-drop file support
- Add "silence-based" smart splitting (instead of fixed seconds)
- Add batch mode (split multiple files at once)
- Add app icon + proper installer (.msi) instead of a plain .exe
