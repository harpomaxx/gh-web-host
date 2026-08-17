#!/usr/bin/env python3
"""Build the Opinion site from the markdown files in posts/.

Usage:
    python3 build.py

Reads posts/*.md, writes one .html per post into the opinion/ root and
regenerates index.html with the list sorted by date (newest first).

No external dependencies: markdown is converted by the parser below,
which covers the usual subset (headings, paragraphs, lists, blockquotes,
code, links, images, emphasis).
"""

import html
import os
import re
import sys
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(BASE, "posts")
TEMPLATES_DIR = os.path.join(BASE, "templates")

SITE_NAME = "Opinion"
SITE_URL = "https://harpomaxx.github.io/gh-web-host/opinion"
SITE_DESCRIPTION = "Notes and opinion pieces."
DEFAULT_AUTHOR = "Harpo MAxx"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# --------------------------------------------------------------------------
# Front matter
# --------------------------------------------------------------------------

def split_front_matter(text):
    """Split the leading `---` block from the body. Returns (dict, body)."""
    meta = {}
    if not text.startswith("---"):
        return meta, text

    end = text.find("\n---", 3)
    if end == -1:
        return meta, text

    block = text[3:end]
    body = text[end + 4:].lstrip("\n")

    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[key.strip().lower()] = value

    return meta, body


def human_date(iso):
    """'2026-08-17' -> 'August 17, 2026'. Returned unchanged if unparseable."""
    try:
        parsed = date.fromisoformat(iso.strip())
    except ValueError:
        return iso
    return "%s %d, %d" % (MONTHS[parsed.month - 1], parsed.day, parsed.year)


def absolute_url(path_or_url):
    """Return an absolute URL for a root-relative/site-relative path or URL."""
    if not path_or_url:
        return ""
    if re.match(r"^[a-z][a-z0-9+.-]*://", path_or_url, flags=re.I):
        return path_or_url
    return "%s/%s" % (SITE_URL.rstrip("/"), path_or_url.lstrip("/"))


# --------------------------------------------------------------------------
# Markdown -> HTML
# --------------------------------------------------------------------------

def inline(text):
    """Convert inline markdown (emphasis, links, code, images)."""
    # Literal code is set aside before escaping so it stays untouched.
    codes = []

    def stash_code(m):
        codes.append(m.group(1))
        return "\x00CODE%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", stash_code, text)
    text = html.escape(text, quote=False)

    # Images before links: same syntax apart from the leading '!'.
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;([^&]*)&quot;)?\)",
        lambda m: '<img src="%s" alt="%s"%s>' % (
            html.escape(m.group(2), quote=True),
            html.escape(m.group(1), quote=True),
            ' title="%s"' % html.escape(m.group(3), quote=True) if m.group(3) else "",
        ),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: '<a href="%s">%s</a>' % (
            html.escape(m.group(2), quote=True), m.group(1)
        ),
        text,
    )

    # DOTALL so emphasis spanning a soft line break inside a paragraph works.
    text = re.sub(
        r"\*\*\*(\S(?:.*?\S)?)\*\*\*", r"<strong><em>\1</em></strong>", text, flags=re.DOTALL
    )
    text = re.sub(r"\*\*(\S(?:.*?\S)?)\*\*", r"<strong>\1</strong>", text, flags=re.DOTALL)
    text = re.sub(r"(?<!\*)\*(\S(?:.*?\S)?)\*(?!\*)", r"<em>\1</em>", text, flags=re.DOTALL)
    text = re.sub(
        r"(?<![\w\\])_(\S(?:.*?\S)?)_(?![\w])", r"<em>\1</em>", text, flags=re.DOTALL
    )

    # Two trailing spaces mean an explicit line break.
    text = re.sub(r"  \n", "<br>\n", text)

    for i, code in enumerate(codes):
        text = text.replace(
            "\x00CODE%d\x00" % i,
            "<code>%s</code>" % html.escape(code, quote=False),
        )
    return text


def markdown_to_html(text):
    """Convert a whole markdown document to HTML."""
    lines = text.replace("\r\n", "\n").replace("\t", "    ").split("\n")
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Fenced code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip the closing fence
            attr = ' class="language-%s"' % html.escape(lang, quote=True) if lang else ""
            out.append(
                "<pre><code%s>%s</code></pre>"
                % (attr, html.escape("\n".join(buf), quote=False))
            )
            continue

        # Horizontal rule
        if re.match(r"^(\*\s*){3,}$|^(-\s*){3,}$|^(_\s*){3,}$", stripped):
            out.append("<hr>")
            i += 1
            continue

        # ATX heading
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", stripped)
        if m:
            level = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (level, inline(m.group(2)), level))
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>\n%s\n</blockquote>" % markdown_to_html("\n".join(buf)))
            continue

        # Lists
        bullet = re.match(r"^[-*+]\s+(.*)$", stripped)
        number = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if bullet or number:
            tag = "ul" if bullet else "ol"
            pattern = r"^[-*+]\s+(.*)$" if bullet else r"^\d+[.)]\s+(.*)$"
            items = []
            while i < n:
                cur = lines[i].strip()
                m = re.match(pattern, cur)
                if m:
                    items.append([m.group(1)])
                    i += 1
                    # Continuation lines: loose or indented under the item.
                    while i < n:
                        nxt = lines[i]
                        if not nxt.strip():
                            break
                        if re.match(r"^\s*([-*+]|\d+[.)])\s+", nxt):
                            break
                        items[-1].append(nxt.strip())
                        i += 1
                elif not cur:
                    # A blank line ends the list unless another item follows.
                    j = i
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and re.match(pattern, lines[j].strip()):
                        i = j
                    else:
                        break
                else:
                    break
            body = "\n".join(
                "  <li>%s</li>" % inline(" ".join(parts)) for parts in items
            )
            out.append("<%s>\n%s\n</%s>" % (tag, body, tag))
            continue

        # Raw HTML: copied through untouched.
        if stripped.startswith("<"):
            buf = []
            while i < n and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue

        # Paragraph
        buf = []
        while i < n and lines[i].strip():
            cur = lines[i].strip()
            if (
                re.match(r"^#{1,6}\s+", cur)
                or cur.startswith((">", "```"))
                or re.match(r"^([-*+]|\d+[.)])\s+", cur)
                or re.match(r"^(\*\s*){3,}$|^(-\s*){3,}$|^(_\s*){3,}$", cur)
            ):
                break
            buf.append(lines[i])
            i += 1
        if buf:
            out.append("<p>%s</p>" % inline("\n".join(buf).strip()))
        else:
            # Defensive fallback: if a line looks like the start of a block but
            # did not match any supported block parser above, emit it as text
            # instead of looping forever.
            out.append("<p>%s</p>" % inline(stripped))
            i += 1

    return "\n\n".join(out)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def summarize(meta, body, limit=200):
    """Index blurb: 'summary', 'subtitle', or the first paragraph."""
    for key in ("summary", "subtitle"):
        if meta.get(key):
            return meta[key]

    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block or block.startswith(("#", ">", "```", "---", "!", "<")):
            continue
        if re.match(r"^([-*+]|\d+[.)])\s+", block):
            continue
        text = re.sub(r"\s+", " ", block)
        text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"[*_`]", "", text).strip()
        if len(text) > limit:
            cut = text.rfind(" ", 0, limit)
            text = text[: cut if cut > 0 else limit].rstrip(",;:.") + "…"
        return text
    return ""


def read_template(name):
    path = os.path.join(TEMPLATES_DIR, name)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def remove_stale_posts(active_slugs):
    """Remove generated post HTML files that no longer have active sources."""
    for filename in os.listdir(BASE):
        slug, ext = os.path.splitext(filename)
        if ext != ".html" or filename == "index.html" or slug in active_slugs:
            continue

        path = os.path.join(BASE, filename)
        should_remove = bool(re.match(r"^post\d+$", slug))
        if not should_remove:
            try:
                with open(path, encoding="utf-8") as fh:
                    should_remove = "Generated by build.py" in fh.read(512)
            except OSError:
                should_remove = False

        if should_remove:
            os.remove(path)
            print("  removed stale: %s" % filename)


def main():
    if not os.path.isdir(POSTS_DIR):
        sys.exit("Directory not found: %s" % POSTS_DIR)

    tpl_post = read_template("post.html")
    tpl_index = read_template("index.html")

    sources = sorted(
        f for f in os.listdir(POSTS_DIR)
        if f.endswith(".md") and not f.startswith(".")
    )
    if not sources:
        sys.exit("No .md files in %s" % POSTS_DIR)

    posts = []

    for name in sources:
        with open(os.path.join(POSTS_DIR, name), encoding="utf-8") as fh:
            meta, body = split_front_matter(fh.read())

        slug = os.path.splitext(name)[0]
        title = meta.get("title") or slug
        iso_date = meta.get("date") or ""
        subtitle = meta.get("subtitle") or ""
        blurb = summarize(meta, body)
        author = meta.get("author") or DEFAULT_AUTHOR
        post_url = absolute_url(slug + ".html")
        image_url = absolute_url(meta.get("image") or "")

        if meta.get("draft", "").lower() in ("true", "yes", "1"):
            print("  skipped (draft): %s" % name)
            continue

        subtitle_block = (
            '<p class="subtitle">%s</p>' % inline(subtitle) if subtitle else ""
        )
        image_meta = (
            '<meta property="og:image" content="%s">\n'
            '<meta name="twitter:image" content="%s">'
            % (html.escape(image_url, quote=True), html.escape(image_url, quote=True))
            if image_url else ""
        )

        page = (
            tpl_post
            .replace("{{title}}", html.escape(title, quote=True))
            .replace("{{description}}", html.escape(blurb, quote=True))
            .replace("{{site_name}}", html.escape(SITE_NAME, quote=True))
            .replace("{{url}}", html.escape(post_url, quote=True))
            .replace("{{date_iso}}", html.escape(iso_date, quote=True))
            .replace("{{author}}", html.escape(author, quote=True))
            .replace("{{image_meta}}", image_meta)
            .replace("{{date_human}}", html.escape(human_date(iso_date), quote=False))
            .replace("{{subtitle_block}}", subtitle_block)
            .replace("{{content}}", markdown_to_html(body))
        )

        target = os.path.join(BASE, slug + ".html")
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(page)

        posts.append({
            "slug": slug,
            "title": title,
            "date": iso_date,
            "date_human": human_date(iso_date),
            "summary": blurb,
        })
        print("  %s -> %s.html" % (name, slug))

    remove_stale_posts({p["slug"] for p in posts})

    # Newest first; ties broken by the higher slug.
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)

    items = []
    for p in posts:
        summary_html = (
            '\n      <p class="summary">%s</p>' % inline(p["summary"])
            if p["summary"] else ""
        )
        items.append(
            '    <li>\n'
            '      <span class="meta">%s</span>\n'
            '      <h2><a href="%s.html">%s</a></h2>%s\n'
            '    </li>'
            % (
                html.escape(p["date_human"], quote=False),
                html.escape(p["slug"], quote=True),
                html.escape(p["title"], quote=False),
                summary_html,
            )
        )

    index = (
        tpl_index
        .replace("{{site_name}}", html.escape(SITE_NAME, quote=True))
        .replace("{{description}}", html.escape(SITE_DESCRIPTION, quote=True))
        .replace("{{url}}", html.escape(SITE_URL.rstrip("/") + "/", quote=True))
        .replace("{{items}}", "\n".join(items))
        .replace("{{updated}}", human_date(date.today().isoformat()))
    )
    with open(os.path.join(BASE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(index)

    print("\nDone: %d post(s) and index.html" % len(posts))


if __name__ == "__main__":
    main()
