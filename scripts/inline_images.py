#!/usr/bin/env python3
"""把公众号 HTML 里的图片处理成可复制的形态：本地/失效图内嵌 base64。

策略（与 references/wechat-spec-compliance.md 一致）：
    素材库 / 图床 https URL  >  base64  >  本地路径（禁止）

- 默认：本地图片（相对路径、绝对路径、file://）内嵌为 base64，http(s) 原样保留；
- `--inline-remote`：把 http(s) 图片也抓下来内嵌，用于图床防盗链、链接失效、
  或粘进后台才发现是破图的场景；
- 产物里只要还有本地路径就拒绝写出（本地路径粘进公众号必定破图）。

用法:
    python3 inline_images.py article.html
    python3 inline_images.py article.html --out article_内嵌.html
    python3 inline_images.py article.html --inline-remote
    python3 inline_images.py article.html --max-mb 6
    python3 inline_images.py article.html --check

规则:
- 缺 `data-w` 时按图片真实像素宽补齐（官方规范 #1.4 的宽度检测需要它）；
- 样式缺 `max-width` / `height` 时自动补，不改已有宽度声明；
- 默认单文件上限 10MB，超限拒绝写出，可用 --max-mb 调整；
- 远程抓取失败只告警并保留原 URL——本地抓不到不代表微信抓不到（UA、防盗链不同），
  以粘贴后的实际效果为准；
- `--check` 只体检不写文件，退出码 1 表示有缺失图或本地残留。

注意：base64 只是「复制载体」。公众号发布后图片仍应落在 mmbiz.qpic.cn，
粘完必须在后台确认图片已转存；未转存时改用素材库 URL。
"""

import argparse
import base64
import mimetypes
import os
import re
import struct
import sys
import urllib.parse
import urllib.request

IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
SRC_ATTR = re.compile(r"""(\ssrc\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
DATA_W_ATTR = re.compile(r"""\sdata-w\s*=\s*(["']).*?\1""", re.I)
STYLE_ATTR = re.compile(r"""(\sstyle\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
REMOTE_RE = re.compile(r"^https?://", re.I)
UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
BASE_STYLE = "max-width: 100%; height: auto; display: block; margin: 0 auto"


def image_size(data):
    """返回 (width, height)，失败返回 None。只解析常见格式头。"""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24])
            return w, h
        if data[:6] in (b"GIF87a", b"GIF89a"):
            w, h = struct.unpack("<HH", data[6:10])
            return w, h
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            chunk = data[12:16]
            if chunk == b"VP8X":
                w = int.from_bytes(data[24:27], "little") + 1
                h = int.from_bytes(data[27:30], "little") + 1
                return w, h
            if chunk == b"VP8L":
                bits = int.from_bytes(data[21:25], "little")
                return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
            if chunk == b"VP8 ":
                w, h = struct.unpack("<HH", data[26:30])
                return w & 0x3FFF, h & 0x3FFF
        if data[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                length = struct.unpack(">H", data[i + 2:i + 4])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", data[i + 5:i + 9])
                    return w, h
                i += 2 + length
    except (struct.error, IndexError, ValueError):
        return None
    return None


def resolve_local(src, base_dir):
    raw = src.strip()
    if raw.startswith("file://"):
        raw = urllib.parse.unquote(urllib.parse.urlparse(raw).path)
    elif re.match(r"^[a-zA-Z]:[\\/]", raw):
        pass  # Windows 盘符路径按本地文件处理
    elif re.match(r"^[a-zA-Z]+:", raw):
        return None
    else:
        raw = urllib.parse.unquote(raw.split("?")[0].split("#")[0])
    path = raw if os.path.isabs(raw) else os.path.join(base_dir, raw)
    return os.path.normpath(path)


def fetch_remote(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://mp.weixin.qq.com/"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    return data, ctype


def patch_tag(tag, data, mime, total):
    """写入 data URI，补 data-w 与自适应样式。"""
    payload = base64.b64encode(data).decode("ascii")
    uri = f"data:{mime};base64,{payload}"
    m = SRC_ATTR.search(tag)
    if not m:
        return tag
    tag = tag[: m.start(3)] + uri + tag[m.end(3):]

    size = image_size(data)
    if size and not DATA_W_ATTR.search(tag):
        closing = "/>" if tag.rstrip().endswith("/>") else ">"
        body = tag.rstrip()[: -len(closing)]
        tag = f'{body} data-w="{size[0]}"{closing}'

    sm = STYLE_ATTR.search(tag)
    if sm:
        style = sm.group(3)
        patch = []
        if "max-width" not in style and "width:" not in style:
            patch.append("max-width: 100%")
        if "height" not in style:
            patch.append("height: auto")
        if patch:
            new_style = style.rstrip("; ") + "; " + "; ".join(patch) + ";"
            tag = tag[: sm.start(3)] + new_style + tag[sm.end(3):]
    else:
        closing = "/>" if tag.rstrip().endswith("/>") else ">"
        body = tag.rstrip()[: -len(closing)]
        tag = f'{body} style="{BASE_STYLE}"{closing}'

    total[0] += len(uri)
    return tag


def main():
    ap = argparse.ArgumentParser(description="本地/失效图片内嵌为 base64，生成可直接复制的单文件")
    ap.add_argument("html")
    ap.add_argument("--out", help="输出文件，默认 <name>_内嵌.html")
    ap.add_argument("--max-mb", type=float, default=10.0, help="输出体积上限（MB），默认 10")
    ap.add_argument("--inline-remote", action="store_true", help="把 http(s) 图片也抓下来内嵌")
    ap.add_argument("--check", action="store_true", help="只检查缺失图片，不写文件")
    ap.add_argument(
        "--allow-local",
        action="store_true",
        help="允许产物里残留本地路径（默认拒绝：粘到公众号一定破图）",
    )
    args = ap.parse_args()

    src_path = os.path.abspath(args.html)
    if not os.path.isfile(src_path):
        sys.exit(f"✗ 找不到文件: {args.html}")
    base_dir = os.path.dirname(src_path)
    html = open(src_path, encoding="utf-8").read()

    missing, failed_remote, total = [], [], [0]
    count = 0

    def repl(m):
        nonlocal count
        tag = m.group(0)
        sm = SRC_ATTR.search(tag)
        if not sm:
            return tag
        src = sm.group(3).strip()
        if src.startswith("data:"):
            return tag

        if REMOTE_RE.match(src):
            if not args.inline_remote:
                return tag
            try:
                data, ctype = fetch_remote(src)
                mime = ctype if ctype.startswith("image/") else (
                    mimetypes.guess_type(urllib.parse.urlparse(src).path)[0] or "application/octet-stream"
                )
                count += 1
                return patch_tag(tag, data, mime, total)
            except Exception as exc:  # 抓不到不代表微信抓不到
                failed_remote.append((src, str(exc)))
                return tag

        path = resolve_local(src, base_dir)
        if path is None or not os.path.isfile(path):
            missing.append(src)
            return tag
        data = open(path, "rb").read()
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        count += 1
        return patch_tag(tag, data, mime, total)

    out = IMG_TAG.sub(repl, html)

    leftover = []
    for tag in IMG_TAG.findall(out):
        sm = SRC_ATTR.search(tag)
        if not sm:
            continue
        src = sm.group(3).strip()
        if src.startswith("data:") or REMOTE_RE.match(src):
            continue
        leftover.append(src)

    if args.check:
        print(f"可内嵌: {count} 张；缺失: {len(missing)} 张；本地残留: {len(leftover)} 处")
        for s in missing:
            print(f"  ✗ 缺图: {s}")
        for s in leftover:
            print(f"  ✗ 本地路径: {s}")
        for s, err in failed_remote:
            print(f"  ⚠️ 远程抓取失败（保留 URL）: {s} — {err.splitlines()[0]}")
        sys.exit(1 if (missing or leftover) else 0)

    if leftover and not args.allow_local:
        sys.exit(
            f"✗ 复制版仍残留 {len(leftover)} 处本地图片路径——粘到公众号必定破图。\n"
            + "".join(f"  · {s}\n" for s in leftover)
            + "  处理：找到原图放进目录后重跑，或先把这些图上传素材库改成 https URL。\n"
            + "  确认要带着本地路径导出，再加 --allow-local。"
        )

    for s, err in failed_remote:
        print(f"⚠️  远程抓取失败，保留 URL（微信侧可能能加载）: {s} — {err.splitlines()[0]}")

    mb = len(out.encode("utf-8")) / 1024 / 1024
    print(f"内嵌 {count} 张，base64 体积 {total[0] / 1024 / 1024:.2f}MB，输出 {mb:.2f}MB")
    for s in missing:
        print(f"  ✗ 缺图（保持原 src）: {s}")
    if mb > args.max_mb:
        sys.exit(
            f"✗ 超过 {args.max_mb}MB 上限：单文件过大会让剪贴板与编辑器卡顿。\n"
            "  压缩图片、减少张数，或用 --max-mb 放宽后重试。"
        )
    if count == 0 and not leftover:
        sys.exit("✗ 没有可内嵌的图片（本地不存在、远程也未开启 --inline-remote）")

    out_path = args.out or (os.path.splitext(src_path)[0] + "_内嵌.html")
    open(out_path, "w", encoding="utf-8").write(out)
    print(f"✓ 已写出: {out_path}")


if __name__ == "__main__":
    main()
