# YouTube Monitor

This workflow checks selected YouTube channels every 12 hours and writes a
Chinese Markdown digest when a new public video appears.

## Setup

1. Open the repository settings.
2. Go to `Secrets and variables` -> `Actions`.
3. Add `YOUTUBE_API_KEY`.
4. Add `GEMINI_API_KEY`.
5. Open `Actions` -> `YouTube Monitor` -> `Run workflow`.

The first run creates a baseline only. It does not summarize older videos.
Later runs add new Markdown files under `../../outputs/youtube/digests/YYYY-MM-DD/`.

## Notes

- Channel IDs are resolved from the handles in `channels.json` with the
  YouTube Data API, then cached in `state.json`.
- Gemini analyzes the public YouTube URL directly.
- Private and unlisted videos cannot be summarized.
- If summarization fails, the video is not marked as processed. A later run
  retries it.
