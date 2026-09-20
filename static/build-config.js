const fs = require("fs");
const apiUrl = (process.env.MUSICALLY_API_URL || "").replace(/\/$/, "");
fs.writeFileSync("config.js", `window.MUSICALLY_API_URL = "${apiUrl}";\n`);
console.log(`Wrote config.js with API URL: ${apiUrl || "(same origin)"}`);
