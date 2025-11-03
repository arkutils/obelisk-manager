# Obelisk Data Manager

A small utility to import/manage Obelisk data files and maintain its `_manifest.json`.

- Can import files into a manifest-manager folder.
- Updates `_manifest.json` to catalogue files and their metadata within the folder.
- Can also work with a live Git repository; handles pulling, committing and pushing.
- Generates compact and deterministic manifests for clean repository commits.
- Understands JSON and common image extensions; skips hidden/underscored names and directories.

Requirements:
- uv (recommended to run or develop) — https://docs.astral.sh/uv/
- Git CLI on PATH (only required for the live-import command)

## Run as a tool

One-off execution - no need to download or install:

```bash
uvx @arkutils/obelisk-manager --help
```

If you have downloaded/clone this repo:

```bash
uv run obelisk --help
```


## Quick start

We offer multiple commands that perform different levels of functionality.

Simply update or create a folder's manifest (non-recursive):

```bash
uvx @arkutils/obelisk-manager update-manifest path/to/folder
# or give the manifest file directly
uvx @arkutils/obelisk-manager update-manifest path/to/folder/_manifest.json
```

Copy files into a destination folder then update the manifest:

```bash
uvx @arkutils/obelisk-manager add-files inputs/*.json path/to/folder
# allow filtered files (hidden/underscored or unrecognised types)
uvx @arkutils/obelisk-manager add-files --all inputs/ path/to/folder
```

Import files into a live Git repository, updating its manifest:

```bash
uvx @arkutils/obelisk-manager live-import -r /path/to/repo inputs/*.json data/asb/
# customise the commit message
uvx @arkutils/obelisk-manager live-import -r /path/to/repo \
    -t "Imported $total changes to $path" \
    -b "Automated import via CI" \
    inputs/ data/
```



## Command Details

All commands support common flags: `-v/--verbose` (repeatable), `-q/--quiet` (repeatable), `--dry-run`, and `--version`. See `--help` for more information about them.

### update-manifest
Create, update or delete `_manifest.json` for an existing directory based on files present there.

```bash
uvx @arkutils/obelisk-manager update-manifest <FOLDER|_manifest.json> [--dry-run] [-v|-q]
```

Behavior:
- Scans the folder (non-recursive) and creates a manifest for allowed file types.
- If there are no valid entries, the existing manifest is deleted; otherwise it is updated.
- A new manifest will be created from scratch if there was none before.
- With `--dry-run`, no files are modified; exit code 2 indicates changes would be made.

### add-files
Copy files into a destination folder and update its manifest.

```bash
uvx @arkutils/obelisk-manager add-files <INPUTS...> <DEST_PATH> [--allow-all|-a] [--dry-run] [-v|-q]
```

Behavior:
- Expands directory inputs one level deep to their immediate files.
- Filters files using the rules above unless `--allow-all` is passed.
- Copies files, then updates `<DEST_PATH>/_manifest.json`.

### live-import
Import into a live Git repository, updating manifest and performing Git actions.

```bash
uvx @arkutils/obelisk-manager live-import -r <REPO> <INPUTS...> <DEST_PATH> \
    [--git-reset] [--skip-pull] [--skip-push] \
    [--allow-all|-a] [--title <T>] [--body <B>] [--exclude-file-list] \
    [--dry-run] [-v|-q]
```

Workflow:
1. Validate the repo and Git availability.
2. Ensure the repo is clean; fetch and fast-forward (or `--git-reset` for a hard reset) unless `--skip-pull`.
3. Copy supplied inputs into `<REPO>/<DEST_PATH>` and update its manifest.
4. If the manifest changed, commit and push (skip with `--skip-push` or implied by `--skip-pull`).

Commit messages:
- Use `--title/-t` and `--body/-b` to customise. `$added`, `$updated`, `$removed`, `$total` are available.
- Additionally, `$path` is provided as the destination path value.
- Include a formatted file change list by default; suppress with `--exclude-file-list`.


## Troubleshooting

- "git CLI not found": ensure Git is installed and available on PATH.
- "Repository has uncommitted changes": commit/stash, pass `--skip-pull` to proceed without syncing, or pass `--git-reset` to perform a hard reset to origin/main before processing.
- "Destination path must be an existing directory" (live-import): create the folder in the repo (e.g. `data/asb/`).
- "Some unhandled files are excluded": pass `--allow-all` if you intend to include them.


## Development

Run checks and tests with uv:

```bash
uv run ruff check --fix
uv run pyright
uv run pytest tests/unit
uv run pytest tests/integration
```

Run locally:

```bash
uv run obelisk --help
```

## License

This software is offered under the MIT license. All contributions will be placed under this license.
