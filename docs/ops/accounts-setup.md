# Accounts and secrets: checklist for the lead

Agents never create accounts, handle credentials or create cloud resources (AGENTS.md rules 9 and 10). These steps are yours. Do them when a task needs them, not all at once.

## Now (to put the repository on GitHub)

- [ ] Create a GitHub account or organisation for the project, and an empty repository (suggested name `srilankafacts`, private until launch).
- [ ] Tell the agent the repository URL. The agent adds it as the remote; you approve the first push.
- [ ] In the repository settings, enable branch protection on `main`: require the CI checks to pass and require a pull request.

## Before real data is stored in the cloud (Stage 0, after G01 works locally)

- [ ] Create a Cloudflare account and enable R2.
- [ ] Create two buckets: `slf-raw` (snapshots, never public) and `slf-releases` (published releases, public read later).
- [ ] Create an R2 API token limited to those two buckets, with read and write but **not** delete if the console allows it.
- [ ] Add these as GitHub Actions secrets (Settings → Secrets and variables → Actions): `SLF_S3_ENDPOINT`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`. Never paste them into chat, files or issues.
- [ ] Turn on R2 bucket versioning or object lock if available, as a second guard against deletion.

## Before the first public preview (Stage 1)

- [ ] Hosting project (Vercel Pro, per D-007) linked to the repository; production deploys only from `main`.
- [ ] Domain purchased and pointed at hosting (see the name and domain item in the legal checklist). **Interim (lead, 2026-11-12):** `kuruppu.xyz`, for now; not yet pointed at hosting. R2 and Vercel are deferred by the lead.
- [ ] Privacy-respecting analytics account (Cloudflare Web Analytics or Umami).

## Ongoing

- [ ] Monthly: check costs (R2, hosting) and review Dependabot pull requests.
- [ ] Rotate R2 tokens yearly or when anyone with access leaves.
