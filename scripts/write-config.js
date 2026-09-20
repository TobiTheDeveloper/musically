const fs = require("fs");
const path = require("path");

const apiUrl = (process.env.MUSICALLY_API_URL || "").replace(/\/$/, "");
const out = path.join(__dirname, "..", "static", "config.js");

fs.writeFileSync(out, `window.MUSICALLY_API_URL = "${apiUrl}";\n`);
console.log(`Wrote config.js with API URL: ${apiUrl || "(same origin)"}`);
