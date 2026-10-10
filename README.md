# release-watch-runner

Fetches two release pages that refuse requests from Cloudflare Workers (Perplexity changelog, xAI news)
using a Chrome TLS fingerprint, and posts the items to the release-watch Worker, which decides what is
new and sends the alerts. Runs every 10 minutes on GitHub Actions. Secret: `RW_INGEST_KEY`.
