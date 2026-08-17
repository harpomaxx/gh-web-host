# Opinion

A minimal black-and-white site for notes and opinion pieces. Posts are
written in markdown and compiled to static HTML by `build.py`.

## Layout

```
opinion/
  build.py            generator (Python 3, no dependencies)
  style.css           the theme
  templates/
    index.html        index template
    post.html         post template
  posts/
    post001.md        sources — this is what you edit
    post002.md
  index.html          generated — do not edit by hand
  post001.html        generated
  post002.html        generated
```

## Writing a post

Create `posts/postNNN.md` with front matter at the top:

```markdown
---
title: The title of the post
date: 2026-08-17
subtitle: Optional standfirst, shown under the title.
---

Body text in markdown...
```

Front-matter fields:

| Field      | Purpose                                                      |
|------------|--------------------------------------------------------------|
| `title`    | Post title. The only one that really matters.                |
| `date`     | `YYYY-MM-DD`. Drives the index order and the displayed date. |
| `subtitle` | Optional standfirst under the title.                         |
| `summary`  | Index blurb. Falls back to `subtitle`, then the first paragraph. |
| `draft`    | `true` keeps the post out of the build.                      |
| `author`   | Optional author metadata; defaults in `build.py`.            |
| `image`    | Optional sharing image URL/path for Open Graph/Twitter cards.|

The output filename comes from the source filename: `posts/post003.md`
becomes `post003.html`.

## Building

```sh
python3 build.py
```

This rewrites every `postNNN.html` and regenerates `index.html`. Run it
after each edit — the generated HTML is committed to the repo, since the
site is served as static files.

## Supported markdown

Headings (`#`–`######`), paragraphs, **bold**, *italics*, `inline code`,
fenced code blocks, links, images, blockquotes, bulleted and numbered
lists, horizontal rules, and raw HTML passed through as-is.

Tables are not parsed by the generator, but the theme styles `<table>`,
so you can drop raw HTML tables into a post and they will look right.
