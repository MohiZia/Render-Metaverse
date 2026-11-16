# Metaverse renderer workflows

This public repository contains workflow configuration and generic contract tests only.
Application code remains in the private `MohiZia/Metaverse` repository.

## Rendering controls

Manual or `render-metaverse` repository dispatch runs accept:

| Input / payload key | Default | Purpose |
| --- | --- | --- |
| `batch` | `3` | 1–6 claimed videos per batch |
| `budget_minutes` | `45` | 10, 20, 30 or 45 minute claiming budget |
| `content_id` | empty | Optional canonical content UUID; claims only that eligible content |
| `max_videos` | empty | Optional total claimed-video cap, 1–100; empty preserves budget-based processing |
| `render_profile` | `balanced` | `balanced`, `cinematic`, `expressive`, `reduced_motion` |
| `narration_style` | `per_video` | Story narration fallback: `narrative`, `funny`, `quote`, `poetry`, `romance`, `sad` |

Profiles control story transitions, camera movement, caption entrance and particles.
Reduced motion disables transitions, camera animation and caption entrances; title/portrait
idle motion is also disabled. Explicit per-video settings take priority.
Existing non-story/HTML rendering paths remain unchanged. Voice profiles adjust
supported rate/pitch, not provider emotion models; fallback TTS may sound different.

Each accepted MP4 carries measured ffprobe duration to the Worker so the admin
panel can sum actual video minutes. Older assets without measured duration remain
unknown, not estimated. Approval and publishing remain Worker-controlled; this
workflow never auto-approves a video or posts directly to a platform.

Code pushes validate workflows but never start a render. Existing scheduled,
manual and repository-dispatch rendering remains available. Merging is not deployment.
The private source must include `scripts/render_profiles.py` before enabling a run.

## Runtime diagnostics

When work exists, the workflow checks out private `main` and includes the exact
source revision in its job summary. A syntax check **and real import preflight**
run before the renderer can claim a video; new private helper imports must also
be added to the sparse-checkout list. Python output is unbuffered so failures
retain useful timing rather than appearing together only at process exit.

A scene-image HTTP failure is a Worker/provider response, not evidence that the
public workflow is missing a module. The private renderer owns safe error details
and bounded transient retries. This workflow deliberately does not retry the
entire render job or replay failed content. A workflow-only merge cannot repair a
Worker endpoint: the private source/endpoint contract must be released separately.

## Bounded smoke runs

For a deliberately authorized one-video smoke run, pass `content_id` and
`max_videos: "1"` (along with any normal controls). `batch: "1"` alone is **not**
a one-video limit: normal runs keep claiming until the budget expires or the
eligible queue empties. The total cap counts claimed attempts, including failures.
The content filter does not requeue ineligible/failed content or bypass claim
leases, approval, publishing rules, or retry limits.

These optional controls require the private renderer to forward the content
filter to `/api/runner/claim` and enforce the total cap, and the Worker to apply
the filter to claim selection and its pending-to-rendering CAS. Merge/release
those coordinated private changes before relying on a bounded smoke dispatch.
Leaving both controls empty preserves existing scheduled-run behavior.
