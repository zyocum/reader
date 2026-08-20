# reader — project notes for agents

## Dependency management

- This project is managed by **uv**: `pyproject.toml` + `uv.lock` are the
  source of truth. Never `pip install` into the venv directly.
- `requirements.txt` is **derived** from the lock as a courtesy for pip
  users. It does not update itself. Regenerate it after *any* dependency
  change — including merging a Dependabot PR (Dependabot only updates
  `uv.lock`/`pyproject.toml`):

  ```sh
  uv export --no-dev --no-hashes --no-annotate --no-header --no-emit-project -o requirements.txt
  ```

  Commit the result as `chore(deps): regenerate requirements.txt` (or fold
  it into the same commit as the dependency change).
- Dev-only tools (`lxml-stubs`) live in the dev dependency group and must
  NOT appear in `requirements.txt` (hence `--no-dev` above).

## Release checklist

1. Bump `version` in `pyproject.toml` (semver; the CLI surface and JSON
   output schema are the public API).
2. `uv lock` so the lockfile records the new version.
3. Regenerate `requirements.txt` (command above) if dependencies changed.
4. Commit as `chore(release): bump version to X.Y.Z`.
5. Annotated tag: `git tag -a vX.Y.Z` with release notes in the message.
6. `git push origin master vX.Y.Z`.
7. `gh release create vX.Y.Z --title "reader X.Y.Z" --notes "..."` with
   notes grouped by theme and a `compare` changelog link.

## Linting

Run before every commit (CI enforces these on push/PR):

```sh
uv run ruff check .        # lint (ruff is pinned in the dev group)
uv run basedpyright        # strict type check: zero errors AND warnings
```

- `basedpyright` (not plain pyright) is the checker — it matches the
  editor's language server, including its stricter rules (`reportAny`,
  `reportUnusedCallResult`, ...). Config lives in `[tool.pyright]` in
  `pyproject.toml`.
- `uvx pyflakes reader.py` is a useful independent second opinion, but
  its findings overlap ruff's `F` rules; only report non-duplicates.
- Auto-fix with `ruff check --fix` (safe fixes only; never
  `--unsafe-fixes` without asking).
- lxml typing gaps are handled with targeted `# pyright: ignore[rule]`
  comments, never blanket suppressions, and never `# noqa` to silence
  ruff without cause.

## Conventions

- Conventional Commits (`feat:`, `fix:`, `chore:`, `feat!:` + a
  `BREAKING CHANGE:` footer for breaking changes).
- Test changes against a local HTML fixture (write a temporary
  `.fixture.html`, delete it afterwards) plus live pages:
  https://www.paulgraham.com/greatwork.html (pathological 1990s
  table/br-based layout) and https://www.gnu.org/philosophy/free-sw.en.html
  (modern, metadata-rich). Check all four formats (`json`, `html`, `md`,
  `txt`) and `-w` wrapping.
- Run via `.venv/bin/python reader.py` (the venv is `.venv`).
- `~/Dropbox/Scripts/Shell/newspaper.sh` (outside this repo, not in git)
  consumes the JSON output (`.title`, `.author`, `.content.text`) — keep
  those fields stable or update the script in tandem.
