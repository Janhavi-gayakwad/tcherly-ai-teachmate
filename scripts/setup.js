/**
 * One-command setup for a fresh copy of the project: `npm run setup`
 *
 *   1. Checks Node.js (18+) and Python (3.10+)
 *   2. Creates .env and client/.env from the examples, with fresh random secrets
 *   3. Installs the Node.js packages for the server and the React client (Yarn 1 via npx, exact lockfile versions)
 *   4. Creates TeachMate's Python environment (teachmate/.venv) and installs its packages
 *   5. Loads the demo data into MongoDB (when MongoDB is running)
 *
 * Safe to run again: existing .env files and environments are kept.
 * Options: --skip-install (no package installs)  --skip-seed (don't touch the database)
 */
const fs = require("fs");
const path = require("path");
const net = require("net");
const crypto = require("crypto");
const { spawnSync } = require("child_process");

const root = path.join(__dirname, "..");
const args = process.argv.slice(2);
const isWin = process.platform === "win32";
const results = [];

const log = (msg = "") => console.log(msg);
const step = (title) => log(`\n=== ${title} ===`);
const ok = (msg) => {
  results.push(["ok", msg]);
  log(`[ok] ${msg}`);
};
const warn = (msg) => {
  results.push(["!!", msg]);
  log(`[!!] ${msg}`);
};
const fail = (msg) => {
  log(`\n[xx] ${msg}`);
  process.exit(1);
};

function run(command, cwd = root) {
  log(`> ${command}`);
  return spawnSync(command, { cwd, stdio: "inherit", shell: true }).status === 0;
}

function capture(command) {
  const res = spawnSync(command, { cwd: root, shell: true, encoding: "utf8" });
  return res.status === 0 ? (res.stdout || "").trim() : null;
}

function readEnvValue(name) {
  const file = path.join(root, ".env");
  if (!fs.existsSync(file)) return "";
  const match = fs.readFileSync(file, "utf8").match(new RegExp(`^\\s*${name}\\s*=\\s*"?([^"\\r\\n]*)"?`, "m"));
  return match ? match[1].trim() : "";
}

function createEnvFile(target, example, transform) {
  const targetPath = path.join(root, target);
  if (fs.existsSync(targetPath)) return ok(`${target} already exists (kept as it is)`);
  fs.writeFileSync(targetPath, transform(fs.readFileSync(path.join(root, example), "utf8")));
  ok(`Created ${target}`);
}

function findPython() {
  const candidates = isWin ? ["py -3", "python", "python3"] : ["python3", "python"];
  for (const cmd of candidates) {
    const out = capture(`${cmd} -c "import sys; print(sys.version_info[0], sys.version_info[1])"`);
    if (!out) continue;
    const [major, minor] = out.split(/\s+/).map(Number);
    if (major === 3 && minor >= 10) return { cmd, version: `${major}.${minor}` };
  }
  return null;
}

// Resolves true/false when MongoDB's port answers, or null for URIs a socket can't check (e.g. mongodb+srv on Atlas).
function mongoReachable(uri) {
  const match = uri.match(/^mongodb:\/\/(?:[^@/]*@)?([^/:,?]+)(?::(\d+))?/);
  if (!match) return Promise.resolve(null);
  const port = Number(match[2] || 27017);
  // "localhost" may resolve to IPv6 first while MongoDB listens on IPv4 only, so try both.
  const hosts = match[1] === "localhost" ? ["127.0.0.1", "::1"] : [match[1]];
  const tryHost = (host) =>
    new Promise((resolve) => {
      const socket = net.connect({ host, port });
      const done = (result) => {
        socket.destroy();
        resolve(result);
      };
      socket.setTimeout(2000, () => done(false));
      socket.once("connect", () => done(true));
      socket.once("error", () => done(false));
    });
  return Promise.all(hosts.map(tryHost)).then((answers) => answers.some(Boolean));
}

async function main() {
  log("Tcherly + TeachMate setup");

  step("Checking tools");
  const nodeMajor = parseInt(process.versions.node, 10);
  if (nodeMajor < 18) fail(`Node.js ${process.versions.node} is too old. Install Node.js 20 or newer (LTS) from https://nodejs.org, then run this again.`);
  ok(`Node.js ${process.versions.node}`);
  const python = findPython();
  if (!python) {
    fail(
      "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ " +
        "(on Windows, tick 'Add python.exe to PATH'), open a NEW terminal and run `npm run setup` again."
    );
  }
  ok(`Python ${python.version} (command: ${python.cmd})`);

  step("Creating settings files");
  createEnvFile(".env", ".env.example", (text) =>
    text
      .replace("<replace_with_a_strong_session_secret>", crypto.randomBytes(48).toString("hex"))
      .replace("<replace_with_a_strong_JWT_session_secret>", crypto.randomBytes(48).toString("hex"))
  );
  createEnvFile(path.join("client", ".env"), path.join("client", ".env.example"), (text) =>
    text.replace(/REACT_APP_MOBILE_API_URL=.*/, 'REACT_APP_MOBILE_API_URL="http://localhost:3000/api"')
  );
  const geminiKey = readEnvValue("GEMINI_API_KEY");
  if (!geminiKey || geminiKey.startsWith("<")) {
    warn("GEMINI_API_KEY is not set in .env yet. The AI chat (TeachMate) won't start until you add it (HOW_TO_RUN.md, step 5).");
  } else {
    ok("GEMINI_API_KEY found in .env");
  }

  const skipInstall = args.includes("--skip-install");
  if (!skipInstall) {
    step("Installing server packages (Node.js) - this can take a few minutes");
    if (!run("npx --yes yarn@1.22.22 install --frozen-lockfile")) fail("Installing the server packages failed. See the error above and HOW_TO_RUN.md > Troubleshooting.");
    ok("Server packages installed");

    step("Installing website packages (React) - this can take a few minutes");
    if (!run("npx --yes yarn@1.22.22 install --frozen-lockfile", path.join(root, "client"))) {
      fail("Installing the website packages failed. See the error above and HOW_TO_RUN.md > Troubleshooting.");
    }
    ok("Website packages installed");
  }

  step("Setting up TeachMate's Python environment");
  const venvDir = path.join(root, "teachmate", ".venv");
  const venvPython = isWin ? path.join(venvDir, "Scripts", "python.exe") : path.join(venvDir, "bin", "python");
  if (fs.existsSync(venvDir) && !capture(`"${venvPython}" -c "print(1)"`)) {
    log("The existing teachmate/.venv doesn't work on this computer (probably copied from another one). Recreating it.");
    fs.rmSync(venvDir, { recursive: true, force: true });
  }
  if (!fs.existsSync(venvPython) && !run(`${python.cmd} -m venv "${path.join("teachmate", ".venv")}"`)) {
    fail("Creating the Python virtual environment (teachmate/.venv) failed. See the error above.");
  }
  if (!skipInstall) {
    const requirements = path.join("teachmate", "requirements.txt");
    if (!run(`"${venvPython}" -m pip install --disable-pip-version-check -q -r "${requirements}"`)) {
      fail("Installing TeachMate's Python packages failed. See the error above and HOW_TO_RUN.md > Troubleshooting.");
    }
  }
  ok("TeachMate Python environment ready (teachmate/.venv)");

  if (!args.includes("--skip-seed")) {
    step("Loading demo data into MongoDB");
    const dbUri = process.env.DB_URI || readEnvValue("DB_URI") || "mongodb://localhost:27017/test-debe";
    const safeUri = dbUri.replace(/\/\/[^@/]*@/, "//***@"); // never print a password
    if ((await mongoReachable(dbUri)) === false) {
      warn(`MongoDB is not running at ${safeUri}. Start MongoDB (HOW_TO_RUN.md, step 1), then run: npm run seed`);
    } else if (run("node data/seed-demo.js")) {
      ok("Demo data loaded (teacher login: demo.teacher@tcherly.local / Demo@1234)");
    } else {
      warn("Loading the demo data failed. Check that MongoDB is running, then run: npm run seed");
    }
  }

  step("Summary");
  results.forEach(([status, msg]) => log(`[${status}] ${msg}`));
  const pending = results.some(([status]) => status === "!!");
  log(`\nNext: ${pending ? "fix the [!!] items above, then " : ""}run  npm run dev  and open http://localhost:8080`);
}

main().catch((error) => fail(error.stack || String(error)));
