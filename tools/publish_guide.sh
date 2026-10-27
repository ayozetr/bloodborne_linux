#!/usr/bin/env bash
# tools/publish_guide.sh: builds the players' guide (mkdocs.yml, from docs/) and publishes it to
# the gh-pages branch, which GitHub Pages serves (https://ayozetr.github.io/bloodborne_linux/).
# Run it after changing docs/, mkdocs.yml or site/ on main (and with each release).
# Needs mkdocs and mkdocs-material (site/requirements.txt), e.g. in a venv: MKDOCS=/path/to/mkdocs.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
mkdocs=${MKDOCS:-mkdocs}
rev=$(git rev-parse --short HEAD)
rm -rf _site
"$mkdocs" build --strict
touch _site/.nojekyll
work=$(mktemp -d)
trap 'git worktree remove --force "$work" 2>/dev/null || true; rm -rf "$work"' EXIT
git fetch -q origin gh-pages 2>/dev/null || true
if git rev-parse -q --verify origin/gh-pages >/dev/null; then
    git worktree add -q -B gh-pages "$work" origin/gh-pages
else
    git worktree add -q --detach "$work"
    git -C "$work" checkout -q --orphan gh-pages
fi
git -C "$work" rm -rq --cached . 2>/dev/null || true
git -C "$work" clean -fdxq
cp -a _site/. "$work"/
git -C "$work" add -A
if git -C "$work" diff --cached --quiet; then
    echo "The guide is already up to date"
    exit 0
fi
git -C "$work" commit -q -m "Players' guide, built from $rev"
git -C "$work" push -q origin gh-pages
echo "Published the guide built from $rev"
