# IFBA OS — Project Instructions

## 1. Project identity and scope

IFBA OS is a community-oriented educational Linux distribution for the IFBA academic context. It is not an official or institutionally endorsed distribution unless authorization is explicitly documented. Use institutional logos and assets only if their use has been authorized. Preserve privacy and do not access private SUAP/AVA APIs or credentials.

The current system uses an Ubuntu 26.04-based build pipeline and KDE Plasma, with shared application, branding, and desktop sources targeting ARM64 (`arm64`/`aarch64`) and AMD64 (`amd64`/`x86_64`). Verify the actual state of the local repository before assuming versions, packages, or functionality. The former XFCE4 implementation is preserved on `legacy/xfce4`.

## 2. Canonical repository and Git branches

- Canonical remote: `https://github.com/Nardoalm/IFBA-OS.git`, named `origin`.
- Active development branch: `development`. All project commits and routine pushes target `origin/development`.
- Never commit or push to `main`, force-push, rewrite shared history, delete branches, or change `legacy/xfce4` without an explicit request.
- Before editing, inspect `git status --short --branch`, `git branch -vv`, `git remote -v`, and the relevant project instructions. Preserve unrelated and uncommitted user changes.
- Do not reset, clean, stash, rebase, merge, switch branches, or discard files in a way that risks hiding or losing work. Diagnose conflicts rather than masking them.

## 3. Git identity (mandatory before every commit)

GitHub username and Git commit identity are different:

- GitHub owner: `Nardoalm`.
- Git author and committer name: `Leonardo de Almeida Silva`.
- Git author and committer email: `nardocontapc1234@gmail.com`.

Before **every** commit, inspect `git config --local user.name`, `git config --local user.email`, `git var GIT_AUTHOR_IDENT`, `git var GIT_COMMITTER_IDENT`, and relevant `GIT_AUTHOR_*` / `GIT_COMMITTER_*` environment overrides. Correct identity **locally in this repository** when necessary; do not modify global identity or impersonate another author. Never commit with inherited incorrect identity.

## 4. Mandatory commit-and-push workflow

The project owner authorizes routine, non-destructive pushes of completed, reviewed project commits to `origin/development` as part of requested work. Do **not** wait for a separate confirmation on each routine push.

For each coherent, meaningful set of changes:

1. Make the changes and perform relevant checks, including regression tests when changes affect the build, boot, networking, AI assistant, or release automation.
2. Check `git status`, inspect the diff, scan for credentials and unwanted large/generated files, and stage **only intended paths**. Never blindly use `git add .`.
3. Verify the required author and committer identities before committing.
4. Commit with a clear, focused, imperative message.
5. Fetch/inspect `origin/development` before pushing. If the remote contains new commits, integrate them safely without discarding user work, or report the blocker.
6. Push with `git push origin development` after each completed coherent change or small cohesive batch.
7. Verify the push by comparing local `HEAD` with `origin/development`; report both SHAs and whether they match.

Do not claim a push happened unless it succeeded. Never use `--force` or `--force-with-lease`. Do not push credentials, private files, ISO binaries, VM disks, caches, or secret configuration. If a network/auth/permissions conflict blocks pushing, keep the local commit, show the exact error, and retry only after fixing the cause safely. Stop if a destructive or security-sensitive action would be required.

Do not create trivial commits solely to claim progress. The completion report must state the actual commit and push status. Keep unrelated local `.DS_Store` untouched and excluded.

## 5. Release versioning: one product version, two architectures

- A **release version** (for example, `0.3.2`) identifies one shared product source state and feature set. ARM64 and AMD64 builds of that release must be derived from the **same source commit** and intended package/configuration revision.
- Product version and architecture are independent axes. Never increment the product version just because a second architecture was built.
- Each architecture has its own unique build ID, UTC build time, ISO SHA-256, byte size, boot metadata, and manifest JSON.
- If one architecture is not built or fails, mark it `missing`, `failed`, or `unvalidated`; never invent its artifact or mark the release complete.
- Never rename an old ISO to impersonate a newer version or retroactively rewrite historical source commits.
- Commit the shared release version and all build inputs *before* generating both ISOs. Both must embed that exact immutable source commit. After builds, commit the external manifests and release documentation separately; those documentation-only commits do not change the embedded build source.
- Update `tools/build_metadata.py`, build scripts, documentation, and tests to implement this policy; do not rely on a hardcoded architecture in build metadata.

## 6. ISO artifact layout and preservation

Organize generated local artifacts under `output/` as follows:

```text
output/
├── latest/
│   ├── amd64/
│   │   ├── ifba-os-ubuntu-26.04-amd64-vX.Y.Z.iso
│   │   └── manifest.json
│   └── arm64/
│       ├── ifba-os-ubuntu-26.04-arm64-vX.Y.Z.iso
│       └── manifest.json
└── versions/
    ├── v0.3.0/
    │   └── arm64/
    │       ├── ifba-os-ubuntu-26.04-arm64-v0.3.0.iso
    │       └── manifest.json
    ├── v0.3.1/
    │   └── amd64/
    │       ├── ifba-os-ubuntu-26.04-amd64-v0.3.1.iso
    │       └── manifest.json
    └── vX.Y.Z/
        ├── amd64/...
        └── arm64/...
```

- `versions/` is immutable history organized by actual release version. Only create architecture directories for artifacts that exist.
- `latest/` points to the current release candidate for each architecture using verified symlinks, and includes `release-status.json`. Existing historical latest pointers may differ by version/commit; record both identities and set `complete_pair: false`. For a new product version, do not advance either pointer until both architecture artifacts exist, pass integrity checks, and share the same source commit; then update both pointers and set `complete_pair: true`. In particular, do not label v0.3.2 available until both artifacts have been built and verified.
- Treat boot/build validation and real VM runtime validation as distinct statuses. `latest/` need not be runtime-validated, but every JSON and release document must show actual status. Never label an ISO boot-tested without booting it.
- Do not duplicate gigabytes unnecessarily. Prefer verified symlinks if supported, but ensure the UTM can resolve the final path; use a verified copy when needed.
- Historical ISOs and manifests must be preserved with their original bytes. For old single-file root-level artifacts, compute hashes and sizes before/after safe migration. Where a historical JSON is missing, generate a clearly labeled retrospective manifest using only verifiable metadata, and mark unavailable details as `null`/`unknown`, never guessed.
- Do not remove, overwrite, or relocate any file referenced by a currently attached UTM VM without first checking those references and preserving bootability. If uncertain, leave the original and report it.
- `output/` ISO binaries and local build metadata are generated artifacts, not Git source. Keep them ignored; never commit `.iso`, `.qcow2`, `.raw`, VM images, build caches, or generated secret-bearing files. Track textual release documentation and sanitized JSON manifests if explicitly placed in a tracked manifests directory (not by forcing ignored files into Git).
- Validate each artifact by SHA-256, file size, architecture, embedded metadata, boot files, rootfs, and JSON schema. Perform atomic publication of complete artifacts; partial builds must never appear as successful `latest` files.

## 7. Release documentation and UTM evidence

- Preserve `docs/ISO-RELEASES.md` history without falsifying previous outcomes. It must list version, architecture, build ID, source commit, build time, hash, size, build method, status, UTM results, and unresolved issues.
- Record dated real-VM findings in `docs/VM-TESTING.md` and update `docs/FINAL-AUDIT.md`, `docs/PROJECT-ROADMAP.md`, and `docs/DEVELOPMENT-LOOP.md` when relevant.
- A generated ISO, valid hash, unit tests, or detected bootloader do **not** prove that Linux boots, networking works, KDE renders, or IFBA AI opens. Report each independently.
- The preferred test environment is a native ARM64 UTM VM on Apple Silicon; retain AMD64 build and testing as an independent requirement. Do not delete/reconfigure unrelated VMs.
- If a UTM automation action is blocked by macOS permissions, say exactly where manual intervention is necessary. Do not claim unobserved screenshots or working applications.

## 8. Safety, privacy, licensing, and implementation quality

- Never commit secrets, student records, cookies, access tokens, passwords, private configs, or credentials. Use per-user secure credentials for IFBA AI; do not bake API keys into images.
- Use only documented and authorized IFBA integrations. Do not automate academic login or scrape private APIs.
- IFBA AI must not silently record/share the screen or execute sensitive commands without explicit user consent.
- Do not execute untrusted scripts, format hardware disks, install on physical hardware, or perform destructive privileged operations without explicit authorization. Safe, project-scoped build/test steps requested by the user are allowed.
- Prefer maintained trusted packages. Verify third-party source provenance and licenses; keep architecture-dependent elements separate from common UI and application code.
- Preserve Linux user isolation. Avoid machine-specific configuration and platform-dependent hardcoded paths.

## 9. Execution and reporting standard

- Implement requested changes, test them, review the diff, commit and push. Do not stop at analysis or documentation if implementation is feasible.
- When a task is blocked, complete independent safe portions and state the precise blocker with evidence.
- Before reporting done: provide a concise change summary, tests actually performed, output artifacts and versions, source commits, local commit SHA, remote `origin/development` SHA, and honest push/UTM/runtime statuses.
