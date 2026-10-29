# Render Metaverse

Public workflow-only repository for rendering queued Metaverse videos.

This repository intentionally contains no application source, internal data, publishing logic, or credentials. The workflow checks out only three renderer modules from the private `MohiZia/Metaverse` repository at runtime, renders queued jobs, and uploads the resulting video assets to the Worker. It never publishes to Instagram or YouTube.

## Required repository configuration

Add these as encrypted **Actions secrets** in `MohiZia/Render-Metaverse`:

- `MV_RUNNER_TOKEN` — the Worker render token.
- `RENDER_SOURCE_TOKEN` — a GitHub token with read-only access to the private `MohiZia/Metaverse` repository.

Optional repository variable:

- `MV_API` — Worker URL. Defaults to `https://metaverse-autopilot.zyyabot.workers.dev`.

Run manually from **Actions → Render Metaverse backlog → Run workflow**. Scheduled runs exit without a render when the Worker reports no claimable jobs.
