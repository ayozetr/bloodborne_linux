"""MkDocs hook: links in docs/ to files elsewhere in the repository (../BBPORT.md, ../bbsc/) point
to them on GitHub, since the guide is built from docs/ alone. The documents stay as they are, so
the same links keep working when they are read on GitHub."""
import posixpath
import re

REPOSITORY = "https://github.com/ayozetr/bloodborne_linux"
LINK = re.compile(r"(\]\()([^)\s]+)(\))")


def on_page_markdown(markdown, page, **kwargs):
    folder = posixpath.dirname(page.file.src_uri)

    def outside(match):
        target = match.group(2)
        if "://" in target or target.startswith(("#", "mailto:")):
            return match.group(0)
        path, _, anchor = target.partition("#")
        resolved = posixpath.normpath(posixpath.join("docs", folder, path))
        if resolved == "docs" or resolved.startswith("docs/"):
            return match.group(0)
        kind = "tree" if path.endswith("/") or "." not in posixpath.basename(path) else "blob"
        url = f"{REPOSITORY}/{kind}/main/{resolved.rstrip('/')}" + (f"#{anchor}" if anchor else "")
        return match.group(1) + url + match.group(3)

    return LINK.sub(outside, markdown)
