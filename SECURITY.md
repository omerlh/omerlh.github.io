# Security

Static site, no server-side code, no dependencies, no secrets. What protects it:

- **Secret scanning:** gitleaks in CI (full history, on every push and PR) and as a local pre-commit hook.
- **Snyk:** connected through the Snyk GitHub integration (not in CI), plus the Snyk MCP locally.
- **Pinned actions:** every GitHub Action is pinned to a commit SHA; Dependabot proposes updates.
- **Least privilege:** workflows default to no permissions and get read-only access per job.
- **Pull requests only:** `main` is protected; every change, including mine, goes through a PR with passing checks.
- **No write-back from CI:** the site is built locally and CI only verifies that the committed output is current.

Found a problem? Open an issue or email omerlh@gmail.com.
