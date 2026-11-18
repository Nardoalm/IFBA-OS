# Next implementation prompt

Continue IFBA OS on the `development` branch. Keep all commit subjects and commit bodies in English, following the existing Conventional Commits style, and write detailed bodies that list the changes and their purpose. Review `AGENTS.md` before editing.

## Prompt

> Continue the IFBA OS prototype from its current repository state. Inspect the source, current branch, working tree, and project instructions first. Improve the welcome experience that is included in the live image: verify that the desktop launcher opens the local welcome page, the wallpaper appears in XFCE, and SUAP/AVA shortcuts are clearly presented as ordinary browser links. Keep the AI assistant optional, do not ask for or store credentials in this mockup, and do not implement automated login, scraping, undocumented endpoints, or silent privileged package installation. Make only changes you can validate in a disposable virtual machine. Record remaining gaps and recovery steps in the VM guide. Use the official IFBA artwork only if supplied and authorized; keep the current generated mark clearly labeled as a placeholder. Create a focused, detailed English Conventional Commit and push it to `origin/development` only after reviewing the staged diff.

## Execute now

The current task executes the portion of this prompt that can be prepared without a VM: include the existing welcome prototype, its visual assets, a desktop shortcut, and the generated wallpaper in the live-image filesystem. Build and inspect the ISO structure. Actual desktop appearance and launcher behavior still require booting it in a VM.

## Deferred work

- Boot the ISO in a disposable VM and confirm the desktop, wallpaper, network, launcher, and shutdown/reboot behavior.
- Replace the placeholder mark with institution-supplied artwork only after authorization is confirmed.
- Implement a real, permission-aware package selection flow with explicit user confirmation and rollback guidance.
- Decide on a supported first-run identity model and approved SUAP/AVA integration interfaces with IFBA/DGTI.
- Design an optional AI integration with per-user secret storage, visible screen sharing, scoped actions, and explicit confirmation for consequential operations.
- Evaluate hardware support, accessibility, package licenses, update policy, and a real installer before any wider release.
