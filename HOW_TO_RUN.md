# How to run Tcherly + TeachMate on your computer

This guide takes you from the zip file to a running project, step by step. You don't need to know Node.js, Python or MongoDB beforehand.

- **First time:** about 30–45 minutes (mostly installing tools and downloading packages).
- **Every time after that:** one command, about 1 minute.

When everything runs, you have four things working together on your computer:

| Part | What it is | Address |
| --- | --- | --- |
| Website | What the teacher sees (React) | http://localhost:8080 |
| Tcherly server | Stores lessons and clicks, computes the dashboard (Node.js) | http://localhost:3000 |
| TeachMate | The AI assistant service (Python + FastAPI, uses Google Gemini) | http://localhost:8000 |
| Database | Where everything is saved (MongoDB) | localhost:27017 |

## Contents

1. [Install the tools (one time)](#step-1--install-the-tools-one-time)
2. [Unzip the project](#step-2--unzip-the-project)
3. [Open a terminal in the project folder](#step-3--open-a-terminal-in-the-project-folder)
4. [Run the setup (one command)](#step-4--run-the-setup-one-command)
5. [Add your own Gemini API key](#step-5--add-your-own-gemini-api-key)
6. [Start everything](#step-6--start-everything)
7. [Log in and try it](#step-7--log-in-and-try-it)
- [Everyday use](#everyday-use)
- [Manual setup (if the setup command fails)](#manual-setup-if-the-setup-command-fails)
- [Troubleshooting](#troubleshooting)
- [Security rules for the team](#security-rules-for-the-team)
- [Quick reference card](#quick-reference-card)

---

## What is in the zip, and what is not

**Included:** all the source code, this guide, and two *template* settings files (`.env.example` and `client/.env.example`).

**Not included, on purpose.** You create these yourself in step 4:

| Left out | Why |
| --- | --- |
| `node_modules/` folders (about 550 MB of libraries) | They are downloaded for your exact computer and operating system. |
| `teachmate/.venv/` (Python libraries) | A Python environment only works on the computer that created it. |
| `.env` and `client/.env` (settings) | They contain secret keys and each person's own Gemini API key. They must never be shared. |

---

## Step 1 — Install the tools (one time)

You need three programs. Install them first, then **close and reopen** any terminal windows so they are found.

| Tool | Version | Used for |
| --- | --- | --- |
| **Node.js** | 20, 22 or 24 (LTS). Tested with 24. | The Tcherly server and the website |
| **Python** | 3.10 to 3.14. Tested with 3.14. | TeachMate (the AI assistant) |
| **MongoDB Community Server** | 7 or 8 | The database |

A code editor is recommended: **Visual Studio Code** (https://code.visualstudio.com).

### Windows

1. **Node.js:** go to https://nodejs.org, download the **LTS** "Windows Installer (.msi)" and click *Next* through the installer (keep the defaults).
2. **Python:** go to https://www.python.org/downloads/ and download the Windows installer. On the **first screen, tick "Add python.exe to PATH"**, then click *Install Now*.
3. **MongoDB:** go to https://www.mongodb.com/try/download/community, choose *Windows* / *msi*, and run it. Choose **Complete**, and keep **"Install MongoD as a Service"** ticked, so MongoDB starts automatically with Windows. *MongoDB Compass* (a viewer for the data) is optional.
4. **Restart your terminal** (or restart the computer if unsure).

### macOS

Install Homebrew first if you don't have it (https://brew.sh), then in Terminal:

```bash
brew install node python
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
xcode-select --install
```

The last line installs Apple's build tools, which one library needs. If it says they are already installed, that's fine.

### Linux (Ubuntu/Debian)

- **Node.js LTS:** install it with nvm (https://github.com/nvm-sh/nvm) or NodeSource. The version in `apt` is often too old.
- **Python:** usually already installed. You also need the `venv` module:

  ```bash
  sudo apt install python3 python3-venv
  ```

- **MongoDB:** follow the official guide at https://www.mongodb.com/docs/manual/administration/install-on-linux/, then start it:

  ```bash
  sudo systemctl start mongod
  ```

### Can't install MongoDB? Use MongoDB Atlas (free, in the cloud)

1. Create a free account and a free **M0** cluster at https://www.mongodb.com/atlas.
2. Create a database user (username and password), and under *Network Access* allow your IP address.
3. Click *Connect → Drivers* and copy the connection string. It looks like `mongodb+srv://user:password@cluster0.xxxxx.mongodb.net/`.
4. After step 4, open `.env` and set `DB_URI="mongodb+srv://user:password@cluster0.xxxxx.mongodb.net/debe"`. Then run `npm run seed`.

### Check that the tools are installed

Open a **new** terminal and type these commands one by one:

```bash
node -v
```

This should print `v20...` or newer.

```bash
npm -v
```

This should print a version number.

```bash
py --version
```

That's the Windows command. On macOS or Linux, type `python3 --version` instead. It should print `Python 3.10` or newer.

To check MongoDB on Windows, open the **Services** app (press Start and type "Services") and look for **MongoDB Server**: it should say *Running*. You can also skip this check, because the setup in step 4 checks it for you.

---

## Step 2 — Unzip the project

1. Right-click the zip file → **Extract All…**
2. Choose a short folder that is **not** inside OneDrive, Google Drive or Dropbox, for example `C:\Projects\` on Windows or `~/Projects/` on macOS/Linux.
   - Why: the setup downloads tens of thousands of small files. Cloud-sync folders make this very slow and can lock files, which causes random errors.
3. You now have a folder called **`Tcherly-TeachMate`** that contains `package.json`, `client`, `teachmate`, `HOW_TO_RUN.md`, and so on.

---

## Step 3 — Open a terminal in the project folder

A *terminal* is a window where you type commands. All commands in this guide are typed **inside the `Tcherly-TeachMate` folder**.

- **Windows (easiest):** open the `Tcherly-TeachMate` folder in File Explorer, click the address bar at the top, type `cmd` and press **Enter**. A Command Prompt opens in the right folder.
- **VS Code (any system):** *File → Open Folder…* → choose `Tcherly-TeachMate` → *Terminal → New Terminal*.
- **macOS:** right-click the folder in Finder → *New Terminal at Folder*. (If you don't see it, enable it in *System Settings → Keyboard → Keyboard Shortcuts → Services*.)
- **Linux:** right-click inside the folder → *Open in Terminal*.

To check you are in the right place, type `dir` on Windows or `ls` on macOS/Linux. You should see `package.json` and `HOW_TO_RUN.md` in the list.

---

## Step 4 — Run the setup (one command)

Make sure MongoDB is running (step 1), then type:

```bash
npm run setup
```

This does everything for you:

1. Checks that Node.js (18 or newer) and Python (3.10 or newer) are installed.
2. Creates your settings files `.env` and `client/.env` from the templates, with new random secret keys.
3. Downloads the libraries for the server and the website (using the exact versions from the lockfiles).
4. Creates TeachMate's Python environment (`teachmate/.venv`) and installs its libraries.
5. Loads the **demo data** into MongoDB: a demo teacher, a course with 3 lessons, 90 students and their feedback.

It takes about **3–10 minutes**, depending on your internet speed. You will see a lot of text scrolling past. Messages saying `warning ... has unmet peer dependency` are normal and can be ignored.

**A successful run ends like this:**

```
=== Summary ===
[ok] Node.js 24.15.0
[ok] Python 3.14 (command: py -3)
[ok] Created .env
[ok] Created client\.env
[!!] GEMINI_API_KEY is not set in .env yet. The AI chat (TeachMate) won't start until you add it (HOW_TO_RUN.md, step 5).
[ok] Server packages installed
[ok] Website packages installed
[ok] TeachMate Python environment ready (teachmate/.venv)
[ok] Demo data loaded (teacher login: demo.teacher@tcherly.local / Demo@1234)

Next: fix the [!!] items above, then run  npm run dev  and open http://localhost:8080
```

How to read it:

- **`[ok]`** means it worked.
- **`[!!]`** means something is still to do. The Gemini key line is expected on the first run: that's step 5. If it says *MongoDB is not running*, start MongoDB (see [Troubleshooting](#troubleshooting)), then run `npm run seed`.
- **`[xx]`** means an error stopped the setup. Read the message just above it, and look it up in [Troubleshooting](#troubleshooting).

You can run `npm run setup` again at any time. It keeps your existing settings files and only redoes what's needed.

---

## Step 5 — Add your own Gemini API key

TeachMate uses Google's Gemini AI through its **free** tier. Each team member creates **their own** key. It's free, and sharing one key makes everyone hit the free limits sooner.

1. Go to **https://aistudio.google.com/apikey** and sign in with a Google account.
2. Click **Create API key**. If it asks for a Google Cloud project, let it create one. No credit card is needed.
3. Copy the key. It is a long string of letters and numbers.
4. Open the file **`.env`** in the `Tcherly-TeachMate` folder with a text editor:
   - VS Code: click `.env` in the file list.
   - Windows Notepad: right-click `.env` → *Open with* → *Notepad*.
   - macOS: `.env` is hidden in Finder. Press **Cmd + Shift + .** to show hidden files, or open it from VS Code.
5. Near the bottom, find this line:

   ```
   GEMINI_API_KEY="<replace_with_gemini_api_key>"
   ```

   Replace the part inside the quotes with your key:

   ```
   GEMINI_API_KEY="paste-your-key-here"
   ```

6. **Save** the file.

Never send your key to anyone or paste it into a group chat, and don't upload `.env` anywhere.

---

## Step 6 — Start everything

In the terminal (still inside the project folder), type:

```bash
npm run dev
```

This starts all three programs in the same terminal. Every line starts with the name of the program that printed it:

| Prefix | Program | It's ready when you see |
| --- | --- | --- |
| `[api]` | Tcherly server | `Connected to MongoDB successfully` and `Express server running on http://localhost:3000` |
| `[web]` | Website | `Compiled successfully!` (the first time this takes about 30–90 seconds) |
| `[ai]` | TeachMate | `Application startup complete.` |

Your browser should open **http://localhost:8080** by itself. If not, open it yourself.

- **Keep this terminal open** while you use the app. Closing it stops everything.
- **To stop:** click inside the terminal and press **Ctrl + C**. On Windows, if it asks `Terminate batch job (Y/N)?`, type `Y` and press Enter.
- If `[ai]` says *TeachMate (the AI chat) is NOT running: GEMINI_API_KEY is missing*, do step 5, stop with Ctrl + C and run `npm run dev` again. The website works without the key; only the chat needs it.

---

## Step 7 — Log in and try it

1. Open **http://localhost:8080** and click **Login**.
2. Log in with the demo teacher:
   - Email: `demo.teacher@tcherly.local`
   - Password: `Demo@1234`
3. On your dashboard, open the course **"CS201 - Programming & Systems (Demo)"**.
4. Next to the lesson **"Demonstration of Java Programs"**, click the small **Teacher Dashboard** button. Hover over the buttons to see their names. The dashboard opens in a new tab. The direct address is http://localhost:8080/l/demonstration-of-java-programs-demo1/dashboard.
5. Look at the line chart: the green line (engagement) dips around minute 20 while the red line (difficulty) peaks.
6. Click **Ask TeachMate** (bottom right) → click **"Why did engagement drop?"**. The answer takes about 10–30 seconds. You'll see status lines like "Looking closely at min 17-23…" while it works.
7. Click an evidence chip such as **E11** in the answer to see the data behind it.
8. Type as if you were the teacher, for example: *"I think I went too fast there. Next time I'll trace the loop step by step. Can you save that?"* A reflection card appears. Click **Save to bookmarks**, and the bookmark shows up in the dashboard's *Your bookmarks* panel.

**To see the student side:** open http://localhost:8080/l/demonstration-of-java-programs-demo1 in a private/incognito window and log in as a demo student (`student01@demo-student.tcherly.local` to `student90@...`, password `Student@1234`). You can also sign up as a new student. Click the Difficult / Easy / Boring / Engaging buttons while the video plays.

**To reset the demo data** (for example before a presentation), run:

```bash
npm run seed
```

This recreates the demo course and removes the demo teacher's chats and saved bookmarks.

---

## Everyday use

After the first setup, you only need:

1. Make sure MongoDB is running. On Windows it starts by itself.
2. Open a terminal in the `Tcherly-TeachMate` folder.
3. Run `npm run dev`.
4. Open http://localhost:8080.

Useful commands (always typed in the project folder):

| Command | What it does |
| --- | --- |
| `npm run dev` | Start everything (website, server and TeachMate) |
| `npm run dev:s` | Start only the Tcherly server |
| `npm run dev:c` | Start only the website |
| `npm run dev:ai` | Start only TeachMate |
| `npm run seed` | Reset the demo data |
| `npm run setup` | Check and repair the setup |
| `python scripts/make_zip.py` (Windows: `py scripts\make_zip.py`) | Make a clean zip to share, with no secrets and no libraries |

**TeachMate from the terminal**, without the website (handy for testing):

On Windows:

```
cd teachmate
.venv\Scripts\python cli.py "Why did engagement drop?"
```

On macOS/Linux:

```bash
cd teachmate
.venv/bin/python cli.py "Why did engagement drop?"
```

**TeachMate's API page** (try its endpoints in the browser): http://localhost:8000/docs

When you edit code while `npm run dev` is running, the server and TeachMate restart automatically and the website reloads by itself.

---

## Manual setup (if the setup command fails)

These steps do the same as `npm run setup`, one by one. Run them in the project folder.

**1. Settings files.** Copy the templates.

On Windows (Command Prompt):

```
copy .env.example .env
copy client\.env.example client\.env
```

On macOS/Linux:

```bash
cp .env.example .env
cp client/.env.example client/.env
```

Then open `.env` and replace these two placeholders with any long random text:

- `<replace_with_a_strong_session_secret>`
- `<replace_with_a_strong_JWT_session_secret>`

This command prints a good random value:

```bash
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
```

Also add your Gemini key (step 5). In `client/.env`, set `REACT_APP_MOBILE_API_URL="http://localhost:3000/api"`.

**2. Server libraries.** Run this in the project folder:

```bash
npx yarn@1.22.22 install --frozen-lockfile
```

**3. Website libraries.**

```bash
cd client
npx yarn@1.22.22 install --frozen-lockfile
cd ..
```

**4. TeachMate's Python environment.**

On Windows:

```
py -3 -m venv teachmate\.venv
teachmate\.venv\Scripts\python -m pip install -r teachmate\requirements.txt
```

On macOS/Linux:

```bash
python3 -m venv teachmate/.venv
teachmate/.venv/bin/python -m pip install -r teachmate/requirements.txt
```

**5. Demo data.** MongoDB must be running.

```bash
npm run seed
```

**6. Start.**

```bash
npm run dev
```

---

## Troubleshooting

Find the message you see in the left column.

| What you see | What it means | How to fix it |
| --- | --- | --- |
| `'node' is not recognized…` or `command not found: npm` | Node.js isn't installed, or the terminal was opened before installing it | Install Node.js (step 1), then close and reopen the terminal |
| PowerShell: `npm.ps1 cannot be loaded because running scripts is disabled on this system` | Windows PowerShell blocks scripts by default | Use **Command Prompt** instead (step 3), or run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once in PowerShell and reopen it |
| `[xx] Python 3.10 or newer was not found` | Python is missing, too old, or not on PATH | Install Python (step 1). On Windows tick "Add python.exe to PATH". Reopen the terminal and run `npm run setup` again |
| Typing `python` opens the Microsoft Store | Windows' fake "python" shortcut | Install Python from python.org. The setup uses the `py` command, which avoids this. You can also turn off *Settings → Apps → Advanced app settings → App execution aliases → python.exe* |
| Linux: `ensurepip is not available` / venv creation fails | The Python venv module is missing | `sudo apt install python3-venv`, delete the `teachmate/.venv` folder, run `npm run setup` again |
| `[!!] MongoDB is not running` or `MongooseServerSelectionError: connect ECONNREFUSED 127.0.0.1:27017` | The database isn't started | **Windows:** Services app → *MongoDB Server* → *Start* (or, in an Administrator Command Prompt: `net start MongoDB`). **macOS:** `brew services start mongodb-community`. **Linux:** `sudo systemctl start mongod`. Then run `npm run seed` |
| Can't log in as `demo.teacher@tcherly.local` | The demo data wasn't loaded | Start MongoDB, then run `npm run seed` |
| `EADDRINUSE: address already in use :::3000`, or `Something is already running on port 8080`, or port 8000 in use | The app is already running (maybe in another terminal), or another program uses that port | Stop the other copy (Ctrl + C in its terminal) or restart the computer. **Windows:** `netstat -ano \| findstr :3000` shows the process number (PID); `taskkill /PID <number> /F` stops it. **macOS/Linux:** `lsof -i :3000` then `kill <PID>` |
| `error:0308010C:digital envelope routines::unsupported` | The website was started some other way (e.g. `npm start` inside `client`) | Start it with `npm run dev` or `npm run dev:c` from the project folder. These add the setting that new Node versions need |
| `[ai] TeachMate (the AI chat) is NOT running: GEMINI_API_KEY is missing` | No Gemini key in `.env` | Do step 5, then stop (Ctrl + C) and run `npm run dev` again |
| Chat: *"Can't reach TeachMate. Is the TeachMate service running on http://localhost:8000?"* | The `[ai]` program isn't running | Look in the terminal for the `[ai]` error message and fix that (usually the key) |
| Chat: *"All Gemini models are busy or rate-limited right now"* | Google's free tier is busy, or you hit the free limit | Wait a minute and ask again. If it never works, check the key for typos or create a new one |
| Chat: *"Your session expired. Please refresh the page."* | Your login pass expired | Refresh the page (F5) |
| The chat fails but the website works, and the address bar shows `127.0.0.1:8080` | TeachMate only accepts the website at `localhost` | Open **http://localhost:8080** instead |
| Installing fails with `bcrypt`, `node-gyp` or `gyp ERR!` | One library needs build tools on some computers | **Windows:** install *Visual Studio Build Tools* with the "Desktop development with C++" option. **macOS:** `xcode-select --install`. **Linux:** `sudo apt install build-essential`. Then run `npm run setup` again |
| `ETIMEDOUT`, `ECONNRESET`, `network` errors, or pip `ReadTimeoutError` | Internet problem, or a college network blocking downloads | Try again on a stable connection (a mobile hotspot often works), then run `npm run setup` again |
| Install is extremely slow, or `EPERM` / `EBUSY` errors on Windows | The folder is inside OneDrive/Dropbox, or antivirus is scanning | Move the project to `C:\Projects\` and run `npm run setup` again |
| A lesson's dashboard shows nothing or "Not Found" | You're logged in as a different teacher. Each teacher only sees their own lessons (this is a security feature) | Log in as the demo teacher, or attach the demo course to your own account: `node data/seed-demo.js --teacher your@email` |
| Anything else strange | Something half-installed | Run `npm run setup` again. If still stuck, send the **last 20 lines** of the terminal output to the team, but never your `.env` |

---

## Security rules for the team

- **Never share your `.env` file or your Gemini key**: not on WhatsApp, not in the zip, not on GitHub. If a key leaks, delete it at https://aistudio.google.com/apikey and create a new one.
- The demo passwords (`Demo@1234`, `Student@1234`) only exist in your local demo data. Don't reuse them for anything real.
- Only fake demo data is sent to Gemini. Don't load real students' data: the free tier may use prompts to improve Google's products.
- To share the project again, use `python scripts/make_zip.py` (Windows: `py scripts\make_zip.py`). It automatically leaves out `.env`, `node_modules` and `teachmate/.venv`.

---

## Quick reference card

**First time**

1. Install Node.js, Python and MongoDB (step 1).
2. Unzip to `C:\Projects\` (not OneDrive).
3. Open a terminal in the `Tcherly-TeachMate` folder.
4. Run `npm run setup`.
5. Put your Gemini key in `.env`: `GEMINI_API_KEY="..."`
6. Run `npm run dev`.
7. Open http://localhost:8080 and log in with `demo.teacher@tcherly.local` / `Demo@1234`.

**Every day**

1. Run `npm run dev` in the project folder.
2. Open http://localhost:8080.
3. Press Ctrl + C to stop.
