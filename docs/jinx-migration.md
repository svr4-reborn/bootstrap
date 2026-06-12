# Jinx to xbstrap migration

The old tree under `uts/` contains Jinx source recipes, host recipes, target recipes, extra package sources, and patch directories. The new bootstrap tree uses xbstrap recipes in `bootstrap.d/*.y4.yml` and patches in `patches/<source>/`.

Use the audit helper to generate a current checklist:

```sh
python3 scripts/audit-jinx-migration.py --output docs/jinx-migration-audit.md
```

The generated report compares:

- `uts/source-recipes/*` against xbstrap `sources:`
- `uts/host-recipes/*` against xbstrap `tools:`, usually as `host-<name>`
- `uts/recipes/*` against xbstrap `packages:`
- `uts/patches/<name>` against `patches/<name>`

## Migration checklist

For each package:

- [ ] Create or update the xbstrap source entry.
- [ ] Copy old patches from `uts/patches/<name>` to `patches/<source-name>` and keep the original patch order.
- [ ] Translate Jinx `prepare()` into xbstrap `regenerate:` when it modifies the source tree before configure.
- [ ] Translate Jinx `configure()`, `build()`, and `package()` into xbstrap `configure:` and `build:` commands.
- [ ] Map Jinx `hostdeps` to `tools_required`.
- [ ] Map Jinx `deps` and runtime library needs to `pkgs_required`.
- [ ] Preserve package `revision` when the package was already shipped from the old tree.
- [ ] Add metadata and subpackages where the new tree expects them.
- [ ] Run `xbstrap -n install <package>` to verify the dependency plan.
- [ ] Run `xbstrap install <package> --reconfigure` for the first real build.

## Notes

Jinx recipes often hide important behavior inside shell functions. The audit report lists those functions as "Custom steps"; entries with custom `package()` bodies generally need manual translation because they may create symlinks, install config files, or strip/debug-split binaries.

Patch directories marked `old+new` should be diffed before deleting either side. Patch directories marked `old` are the highest-risk migration leftovers, especially for packages that already have an xbstrap recipe.
