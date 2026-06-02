#!/usr/bin/env python3
import datetime as dt
import html
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
CHANNELS_PATH = ROOT / "channels.json"
STATE_PATH = ROOT / "state.json"
DIGESTS_PATH = ROOT / "digests"
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
GEMINI_TIMEOUT = int(os.environ.get("GEMINI_TIMEOUT", "180"))
GEMINI_RETRIES = int(os.environ.get("GEMINI_RETRIES", "2"))
ATOM = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def request_json(url, *, method="GET", headers=None, body=None, timeout=60):
    request = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def resolve_channel_id(handle):
    query = urllib.parse.urlencode(
        {"part": "id", "forHandle": handle.lstrip("@"), "key": YOUTUBE_API_KEY}
    )
    data = request_json(f"https://www.googleapis.com/youtube/v3/channels?{query}")
    items = data.get("items", [])
    if not items:
        raise RuntimeError(f"Could not resolve YouTube handle: {handle}")
    return items[0]["id"]


def fetch_feed(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    request = urllib.request.Request(url, headers={"User-Agent": "youtube-monitor/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        root = ET.parse(response).getroot()

    videos = []
    for entry in root.findall("atom:entry", ATOM):
        videos.append(
            {
                "video_id": entry.findtext("yt:videoId", default="", namespaces=ATOM),
                "title": entry.findtext("atom:title", default="", namespaces=ATOM),
                "published": entry.findtext("atom:published", default="", namespaces=ATOM),
                "url": entry.find("atom:link", ATOM).attrib["href"],
            }
        )
    return url, videos


def fetch_channel_feed(handle, channel_state):
    channel_id = channel_state.get("channel_id") or resolve_channel_id(handle)
    try:
        rss_url, videos = fetch_feed(channel_id)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        refreshed_channel_id = resolve_channel_id(handle)
        if refreshed_channel_id == channel_id:
            print(
                f"WARNING: Skipping unavailable YouTube feed: {handle} ({channel_id})",
                file=sys.stderr,
            )
            return None
        channel_id = refreshed_channel_id
        try:
            rss_url, videos = fetch_feed(channel_id)
        except urllib.error.HTTPError as retry_error:
            if retry_error.code != 404:
                raise
            print(
                f"WARNING: Skipping unavailable YouTube feed: {handle} ({channel_id})",
                file=sys.stderr,
            )
            return None

    channel_state["channel_id"] = channel_id
    channel_state["rss_url"] = rss_url
    return rss_url, videos


def summarize(video, channel_name):
    prompt = f"""请用中文总结这个 YouTube 视频。

频道：{channel_name}
标题：{video["title"]}
发布时间：{video["published"]}

严格按照以下 Markdown 结构输出，不要添加一级标题：

## 一句话摘要

## 主要内容

## 核心观点

## 重要时间点

## 与宏观投资的关系

## 值得进一步研究的问题

如果视频与宏观投资无关，请在对应章节明确说明。重要时间点尽量使用 MM:SS 或 HH:MM:SS。"""
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"file_data": {"file_uri": video["url"]}},
                ]
            }
        ]
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    data = request_json(
        url,
        method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY},
        body=body,
        timeout=GEMINI_TIMEOUT,
    )
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as error:
        raise RuntimeError(f"Gemini returned no summary: {data}") from error


def summarize_with_retries(video, channel_name):
    for attempt in range(1, GEMINI_RETRIES + 1):
        try:
            return summarize(video, channel_name)
        except TimeoutError:
            print(
                f"WARNING: Gemini summary timed out for {video['url']} "
                f"(attempt {attempt}/{GEMINI_RETRIES})",
                file=sys.stderr,
            )
    print(f"WARNING: Skipping video after Gemini timeouts: {video['url']}", file=sys.stderr)
    return None


def write_digest(channel_name, rss_url, video, summary):
    date = video["published"][:10] or dt.date.today().isoformat()
    path = DIGESTS_PATH / date / f'{video["video_id"]}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# {html.escape(video["title"])}

- 频道：{channel_name}
- 发布时间：{video["published"]}
- 视频链接：{video["url"]}
- RSS 地址：{rss_url}

{summary.strip()}
"""
    path.write_text(content, encoding="utf-8")


def save_state(state):
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main():
    if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY and GEMINI_API_KEY are required")

    channels = json.loads(CHANNELS_PATH.read_text(encoding="utf-8"))
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    original_state = json.dumps(state, ensure_ascii=False, sort_keys=True)
    baseline_only = not state.get("initialized", False)

    for channel in channels:
        handle = channel["handle"]
        channel_state = state["channels"].setdefault(handle, {"seen_video_ids": []})
        feed = fetch_channel_feed(handle, channel_state)
        if feed is None:
            continue
        rss_url, videos = feed

        seen = set(channel_state["seen_video_ids"])
        if baseline_only:
            seen.update(video["video_id"] for video in videos)
        else:
            for video in reversed(videos):
                if video["video_id"] in seen:
                    continue
                print(f'Summarizing {channel["name"]}: {video["title"]}')
                summary = summarize_with_retries(video, channel["name"])
                if summary is None:
                    continue
                write_digest(channel["name"], rss_url, video, summary)
                seen.add(video["video_id"])

        channel_state["seen_video_ids"] = sorted(seen)

    state["initialized"] = True
    if json.dumps(state, ensure_ascii=False, sort_keys=True) != original_state:
        state["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        save_state(state)
    print("Baseline created." if baseline_only else "Check complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
