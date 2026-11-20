# IFBA OS Project Instructions

## Project context

IFBA OS is a proposed Linux distribution for the IFBA academic community. The current direction is to evaluate a supported Ubuntu LTS base, take usability inspiration from Linux Mint, and curate educational applications inspired by Linux Educacional. Do not assume institutional endorsement or authorization to use IFBA trademarks, logos, or private systems.

## Branch and repository workflow

- The canonical remote is `https://github.com/Nardoalm/IFBA-OS.git` and its Git remote name must be `origin`.
- Do all project work on the `development` branch. Never commit project changes directly to `main` or another branch.
- Before editing, inspect `git status`, the current branch, and the repository instructions. Preserve unrelated changes and do not switch branches if doing so would overwrite or hide uncommitted work.
- If `development` does not exist locally, create it from the appropriate project base without discarding work. If the remote branch is missing, initialize it only when the remote repository is empty or its history has been inspected and the update is safe.
- Commit each coherent, meaningful change requested by the user. Keep commits focused, use clear imperative commit messages, and exclude unrelated files, generated artifacts, secrets, and machine-specific data.
- Push completed project commits to `origin/development` when the user has authorized the repository workflow. Never force-push, rewrite shared history, or push to `main`.
- If the working tree contains user changes, or the remote state makes a safe commit/push uncertain, preserve the work and explain the blocker rather than overwriting it.

## Safety and privacy

- Never commit API keys, access tokens, passwords, private student data, cookies, or credentials. Keep user-provided AI API keys in the operating system's secure credential store; never bake them into an ISO, package, repository, or shared configuration.
- Treat SUAP and AVA data as private academic information. Do not scrape pages, automate credential entry, read session cookies, or call undocumented/private endpoints. Use only integrations documented and authorized by IFBA/DGTI.
- Keep AI assistance optional. Screen sharing must be user-initiated and visible. Require explicit confirmation before installing software, running commands, changing system settings, or modifying/deleting user files. Do not give a model silent unrestricted administrator access.
- Do not execute untrusted scripts, install packages, build/install an ISO on real hardware, format disks, or perform privileged system changes unless the user explicitly requests that operation.
- Verify software sources and licenses before including applications in a distribution. Prefer maintained packages from trusted repositories.

## Implementation guidance

- Prefer small, reviewable changes and document architectural decisions, supported hardware, package sources, licensing, and recovery steps.
- Keep the user interface, branding assets, package selection, system configuration, and any future AI assistant isolated into clear components.
- Install shared system applications once for all local users where the package format supports it; keep each user's documents, settings, and credentials isolated.
- Use official IFBA artwork only when supplied and authorized. Do not approximate or regenerate official institutional logos as production assets.
- Do not claim the project is official, endorsed, or supported by IFBA unless the user provides confirmation of authorization.
- Respect repository-specific instructions and existing project conventions when they are added.

## Validation and reporting

- Run only checks that are relevant to the requested change and allowed by the user's instructions. Do not add or run tests unless requested.
- Before committing, review the staged diff and confirm it contains only the intended change.
- In the completion summary, state what changed, what validation was performed, the commit identifier, and whether the push succeeded. If a push fails, do not claim it succeeded.

## ISO versioning and release history

- Treat every successfully generated ISO as a distinct build and give it a new semantic product version (`MAJOR.MINOR.PATCH`) in `tools/build_metadata.py` before starting the build. Increment the patch for routine prototype changes; use a minor increment for a new feature set and a major increment only for an incompatible release milestone.
- Every ISO must have a unique timestamped build ID, source commit, UTC build time, clean/dirty source state, and an external SHA-256/size manifest. Never reuse or overwrite a version entry in `docs/ISO-RELEASES.md`.
- Update `docs/ISO-RELEASES.md` with each artifact's version, build ID, source commit, date, SHA-256, size, build/cache method, checks, UTM result, and unresolved issues. Include failed boot/runtime checks; do not label a build validated based only on source or mocked tests.
- When a live VM check changes the understanding of a blocker, add a dated evidence addendum to `docs/VM-TESTING.md`, update the relevant rows in `docs/FINAL-AUDIT.md` and `docs/PROJECT-ROADMAP.md`, and link the finding from `docs/DEVELOPMENT-LOOP.md`. Keep prior release outcomes immutable; add new runtime evidence to the relevant ISO entry without inventing a new artifact.
- Commit the product version and build inputs before generating the ISO so its embedded commit identifies the exact source. After the build, add the final hash and VM evidence to the release history in a separate documentation-only commit; do not rebuild solely because that log commit changed.
- Keep older release entries immutable. Historical artifacts created before this policy may be listed as `unversioned legacy` with their known hashes and contemporaneous evidence. Do not invent missing build IDs, commits, or validation results.
