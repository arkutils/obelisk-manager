# Obelisk Importer

A small utility to import new data into arkutils/Obelisk while updating manifests.

Requires Git CLI to be installed.

## Plans

Planned CLI:
```
uv tool run @arkutils/obelisk-manager
    live-import -- reset repo, add, update manifest, push
    add-files -- add files and update manifest, no repo stuff
    update-manifest -- just update a manifest file
```

Steps:
1. Check there are no local changes in the repo
2. Hard reset the repo to match origin
3. Import all source files to the given destination folder within the repo (e.g. data/asb/)
4. Update the manifest for that folder to include the source files
5. Use the supplied Git identity if present
6. Create a commit with either the given commit message or a simple list of imported files and versions
7. Push the changes, if not skipped

