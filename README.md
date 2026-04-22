 # Storage Cleaner

  A free, offline Windows app that shows what's taking up space on your drives and helps you clean up safely. Built for Windows 10
  and 11.

  ## Download

  Go to the [Releases](../../releases/latest) page and download one of:

  - **Storage Cleaner Portable.exe** — single file, just double-click.
  - **Storage-Cleaner-v1.0.zip** — same app as a folder (opens faster).

  Works out of the box. No install, no account, no internet needed.

  ## What it does

  - Lists every drive on your PC with live free-space bars.
  - Scans 14 cleanup categories: temp files, Recycle Bin, Chrome/Edge/Firefox/Brave caches, thumbnail cache, crash dumps, Delivery
  Optimization, Windows Update cache, Prefetch, old Downloads, Windows logs.
  - Color-codes each category as **SAFE** (green) or **CAUTION** (yellow) so you know what you're touching.
  - Finds your **top 20 biggest individual files** across the entire PC.
  - Deletes go to the **Recycle Bin** by default (recoverable). Permanent delete is opt-in.
  - One-click **Clean All SAFE** for instant cleanup of everything green.

  ## First launch

  Windows SmartScreen will show **"Windows protected your PC"** because the app isn't signed with a paid certificate. This is normal
  for any free/open-source app.

  Click **More info** → **Run anyway**. Windows remembers your choice, so it only happens once.

  ## Safety

  The app **never** touches:

  - `C:\Windows\System32`, `SysWOW64`, `WinSxS`, or any Windows system directories
  - `Program Files` or `Program Files (x86)`
  - Your `Documents`, `Pictures`, `Videos`, `Music`, `Desktop`, or `OneDrive` folders (during category cleans)
  - Drive roots, symlinks, or junctions

  All file paths are checked against two independent blocklists before any delete happens. Source code is in `src/` — feel free to
  review it.

  ## Build from source

  Requires Python 3.13. Then:

  ```
  py -m pip install -r requirements.txt
  build.bat
  ```

  Outputs land in `dist/`.

  ## License

  MIT — do what you want with it.
