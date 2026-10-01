// Starts the TeachMate FastAPI service with the project's Python virtual environment: `npm run dev:ai`.
// Works on Windows (.venv/Scripts/python.exe) and macOS/Linux (.venv/bin/python).
// Pass --reload to restart automatically when teachmate/app changes.
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
const args = ["-m", "uvicorn", "app.main:app", "--app-dir", "teachmate", "--port", port];
if (process.argv.includes("--reload")) args.push("--reload", "--reload-dir", path.join("teachmate", "app"));

const child = spawn(python, args, { cwd: root, stdio: "inherit" });
child.on("exit", (code) => process.exit(code || 0));
