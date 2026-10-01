// Starts the React (CRA 4) dev server from the repo root: `npm run dev:c`.
// CRA 4 uses webpack 4, which needs OpenSSL's legacy provider on Node 17+,
// so the flag is added here instead of asking every developer to set it in their shell.
const path = require("path");
const { spawn } = require("child_process");

const clientDir = path.join(__dirname, "..", "client");
const reactScripts = path.join(clientDir, "node_modules", "react-scripts", "bin", "react-scripts.js");

const env = { ...process.env };
const nodeMajor = parseInt(process.versions.node, 10);
if (nodeMajor >= 17 && !(env.NODE_OPTIONS || "").includes("--openssl-legacy-provider")) {
  env.NODE_OPTIONS = `${env.NODE_OPTIONS || ""} --openssl-legacy-provider`.trim();
}

const child = spawn(process.execPath, [reactScripts, "start"], { cwd: clientDir, stdio: "inherit", env });
child.on("exit", (code) => process.exit(code || 0));
