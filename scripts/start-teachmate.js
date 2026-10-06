// Starts the TeachMate FastAPI service with the project's Python virtual environment: `npm run dev:ai`.
// Works on Windows (.venv/Scripts/python.exe) and macOS/Linux (.venv/bin/python).
//
// Pass --reload to restart automatically when files in teachmate/app change. This script does the
// watching itself instead of using uvicorn's --reload: on Windows uvicorn stops its worker with a
// Ctrl+C signal, which never arrives when there is no console window, so the old code kept running.
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const root = path.join(__dirname, "..");
const venv = path.join(root, "teachmate", ".venv");
const python = process.platform === "win32" ? path.join(venv, "Scripts", "python.exe") : path.join(venv, "bin", "python");

if (!fs.existsSync(python)) {
  console.error("TeachMate's Python environment is missing (teachmate/.venv). Run `npm run setup` first.");
  process.exit(1);
}

// Fail with a short, clear message instead of a Python traceback when the Gemini key is missing.
function geminiKey() {
  if (process.env.GEMINI_API_KEY) return process.env.GEMINI_API_KEY.trim();
  const envFile = path.join(root, ".env");
  if (!fs.existsSync(envFile)) return "";
  const match = fs.readFileSync(envFile, "utf8").match(/^\s*GEMINI_API_KEY\s*=\s*"?([^"\r\n]*)"?/m);
  return match ? match[1].trim() : "";
}
const key = geminiKey();
if (!key || key.startsWith("<")) {
  console.error(
    [
      "",
      "TeachMate (the AI chat) is NOT running: GEMINI_API_KEY is missing in the .env file.",
      "  1. Create a free key at https://aistudio.google.com/apikey",
      "  2. Open .env in the project folder and set:  GEMINI_API_KEY=your-key-here",
      "  3. Stop with Ctrl+C and run  npm run dev  again.",
      "The website and dashboard still work without it; only the chat needs the key.",
      "",
    ].join("\n")
  );
  process.exit(1);
}

const port = process.env.TEACHMATE_PORT || "8000";
const args = ["-m", "uvicorn", "app.main:app", "--app-dir", "teachmate", "--port", port, "--timeout-graceful-shutdown", "5"];
const reload = process.argv.includes("--reload");

let child = null;
let restarting = false;

function start() {
  child = spawn(python, args, { cwd: root, stdio: "inherit" });
  child.on("exit", (code) => {
    child = null;
    if (restarting) {
      restarting = false;
      start();
    } else if (!reload) {
      process.exit(code || 0);
    } else if (code) {
      console.error("[teachmate] stopped with an error; fix the code and save, and it will restart.");
    }
  });
}

function restart(file) {
  console.log(`[teachmate] ${file} changed, restarting...`);
  if (child) {
    restarting = true;
    child.kill();
  } else {
    start();
  }
}

if (reload) {
  const crypto = require("crypto");
  const fingerprints = new Map(); // file -> hash of its content
  const fingerprint = (file) => {
    try {
      return crypto.createHash("sha1").update(fs.readFileSync(file)).digest("hex");
    } catch (e) {
      return null; // deleted or being written
    }
  };
  const dirs = [path.join(root, "teachmate", "app"), path.join(root, "teachmate", "app", "prompts")];
  dirs.forEach((dir) =>
    fs.readdirSync(dir).filter((f) => /\.(py|md)$/.test(f)).forEach((f) => fingerprints.set(path.join(dir, f), fingerprint(path.join(dir, f))))
  );

  let timer = null;
  const pending = new Set();
  // Watch the app folder and its prompts (non-recursive watching works on every platform). Restart only when a
  // file's content really changed: sync tools such as OneDrive touch files without changing them.
  for (const dir of dirs) {
    fs.watch(dir, (_, filename) => {
      if (!filename || !/\.(py|md)$/.test(filename)) return;
      pending.add(path.join(dir, filename));
      clearTimeout(timer);
      timer = setTimeout(() => {
        const changed = [...pending].filter((file) => {
          const current = fingerprint(file);
          if (current === fingerprints.get(file)) return false;
          fingerprints.set(file, current);
          return true;
        });
        pending.clear();
        if (changed.length) restart(changed.map((file) => path.basename(file)).join(", "));
      }, 300);
    });
  }
}

const stop = () => {
  if (child) child.kill();
  process.exit(0);
};
process.on("SIGINT", stop);
process.on("SIGTERM", stop);

start();
