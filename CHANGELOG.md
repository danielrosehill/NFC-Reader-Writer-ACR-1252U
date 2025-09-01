# Changelog

## v1.0.0 (Initial Release)

- Removed lock confirmation prompt in CLI; all variants now lock by default.
- Updated TUI to lock tags by default; removed irreversible lock warnings.
- Ensured GUI mirrors CLI behavior (default lock, no warning).
- Added run scripts for all three variants:
  - TUI: `./scripts/run.sh`
  - CLI: `./scripts/run_cli.sh`
  - GUI: `./scripts/run_gui.sh`
- Documentation updated to reflect variants and default no-lock behavior.
