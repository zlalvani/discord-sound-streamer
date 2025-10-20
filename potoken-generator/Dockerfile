# One-shot: prints { visitorData, poToken, expiresAt, contentBinding } then exits.

# ---------- build ----------
FROM node:20-bookworm-slim AS build

# CA bundle + build deps for the BgUtils provider (uses node-canvas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git python3 build-essential pkg-config \
    libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pin the provider repository (adjust tag when updating)
RUN git clone --single-branch --branch 1.2.2 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git .

WORKDIR /app/server
RUN npm ci && npx tsc

# ---------- runtime ----------
FROM node:20-bookworm-slim

# Runtime libs for node-canvas
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libcairo2 libpango-1.0-0 libjpeg62-turbo libgif7 librsvg2-2 \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production
WORKDIR /app

# Provider build artifacts
COPY --from=build /app/server/build ./provider-build
COPY --from=build /app/server/package.json ./provider-package.json
COPY --from=build /app/server/package-lock.json ./provider-package-lock.json

# Install runtime deps for the provider only
RUN cp provider-package.json package.json && cp provider-package-lock.json package-lock.json \
    && npm ci --omit=dev

# Tiny runner that:
# 1) fetches https://www.youtube.com/ and parses ytcfg VISITOR_DATA
# 2) spawns the provider's generate_once script to mint a poToken
# 3) merges both into one JSON payload and prints to stdout
ADD <<'EOF' /app/run.js
import { spawn } from 'node:child_process';

async function getVisitorData() {
    // Fetch YouTube homepage with realistic headers; parse ytcfg for VISITOR_DATA
    const res = await fetch('https://www.youtube.com/', {
    headers: {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    }
    });
    const html = await res.text();

    // Look for ytcfg.set({...}) then extract VISITOR_DATA field robustly
    // Matches "VISITOR_DATA":"<value>"
    const m = html.match(/"VISITOR_DATA"\s*:\s*"([^"]+)"/);
    if (m && m[1]) return m[1];

    // Fallback: try responseContext.visitorData embedded in initial data chunks
    const m2 = html.match(/"visitorData"\s*:\s*"([^"]+)"/);
    if (m2 && m2[1]) return m2[1];

    throw new Error('Could not find VISITOR_DATA on homepage');
}

function getPoTokenOnce() {
    return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ['/app/provider-build/generate_once.js'], { stdio: ['ignore', 'pipe', 'inherit'] });
    let out = '';
    child.stdout.on('data', d => out += d);
    child.on('close', (code) => {
        if (code !== 0) return reject(new Error('generate_once.js exited with code ' + code));
        try {
        resolve(JSON.parse(out));
        } catch (e) {
        reject(new Error('Failed to parse poToken JSON: ' + e.message));
        }
    });
    });
}

(async () => {
    try {
    const [visitorData, pot] = await Promise.all([getVisitorData(), getPoTokenOnce()]);
    // pot typically has { poToken, contentBinding, expiresAt }
    const payload = {
        visitorData,
        ...pot
    };
    process.stdout.write(JSON.stringify(payload) + '\n');
    } catch (err) {
    console.error(err.stack || String(err));
    process.exit(1);
    }
})();
EOF

# Default entrypoint: run once, print JSON, exit
ENTRYPOINT ["node", "/app/run.js"]
