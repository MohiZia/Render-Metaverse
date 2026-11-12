# Metaverse renderer workflows

This public repository contains workflow configuration and generic contract tests only.
Application code remains in the private `MohiZia/Metaverse` repository.

## Rendering controls

Manual or `render-metaverse` repository dispatch runs accept:

| Input / payload key | Default | Purpose |
| --- | --- | --- |
| `batch` | `3` | 1–6 claimed videos per batch |
| `budget_minutes` | `45` | 10, 20, 30 or 45 minute claiming budget |
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
