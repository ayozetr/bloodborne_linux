# Release notes template

Every release uses this format: same sections, same order. A section with nothing to say keeps
its heading and says "None.". Notes are in English. "New", "Improved" and "Fixed" cover the
changes since the previous release. Third-party work is credited in the line that uses it.

- Tag: `<upstream bbport version>-linux.<n>` (e.g. `0.4-linux.1`).
- Title: `bbport Linux <tag>`.
- Asset: `dist/Bloodborne-bbport-x86_64.AppImage` (`bash build.sh && bash packaging/appimage-sharun.sh`).

```markdown
<One or two sentences: what this release is and which upstream bbport it is based on.>

**Requirements:** your own decrypted dump of Bloodborne 1.09, US (`CUSA03173`) or EU
(`CUSA00900`). No game files are included. Linux x86-64 and a Vulkan 1.3 GPU.

## Download

| File | For |
|---|---|
| `Bloodborne-bbport-x86_64.AppImage` | Any x86-64 distribution and the Steam Deck |

Make it executable, run it, choose your game folder and press **Play**. Saves and settings go
to `~/.local/share/bbport`.

SHA-256: `<sha256sum of the AppImage>`

## New
- **<Feature>**: <what it does>.

## Improved
- <Change to something that existed>.

## Fixed
- <Bug fixed>.

## Upgrading
- <What someone coming from the previous release has to do, or "None.">

## Known issues
- <Limitations and known bugs.>

**Full changes:** https://github.com/ayozetr/bloodborne_linux/compare/<previous tag>...<tag>
**Credits and licenses:** https://github.com/ayozetr/bloodborne_linux#credits
```
