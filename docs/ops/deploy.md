# Deploying Sri Lanka Facts for free

The site and its data go on Cloudflare's free plan as two static sites. The three files that are too
large for it go on a GitHub release of this repository (decision D-053). Nothing here needs a
payment method, and nothing runs a server.

Verification tags: ✅ checked by an agent on 2026-11-19 · 🟡 from the vendor's pages, not tested ·
❓ not checked.

## What goes where

| Part | Where | Free-plan limit | Our size (from `v2026.11.17-preview.3`) |
|---|---|---|---|
| Website (`web/`, static export) | Cloudflare Worker `srilankafacts-site`, static assets only | 20,000 files, 25 MiB per file 🟡 | 6,840 files, 962 MB, largest 16.1 MB ✅ |
| Data site (release API and downloads) | Cloudflare Worker `srilankafacts-data`, static assets only | the same 🟡 | 16,156 files, 1.03 GB, largest under 25 MiB ✅ |
| Three large downloads | GitHub release of this public repository | 2 GiB per file 🟡 | 1.03 GB, 126 MB, 103 MB ✅ |
| SQL engine for `/query` | jsDelivr's copy of `@duckdb/duckdb-wasm@1.32.0` | free public CDN 🟡 | 33 MB, loaded only on `/query` |

Requests for static files are "free and unlimited" on Cloudflare's free plan (Workers static-assets
billing page 🟡). Neither Worker has a script, so the 100,000 requests a day limit for scripts
should not apply. Cloudflare's limits page does not say this outright 🟡. There is no bandwidth
charge on either service 🟡.

**Why not Vercel or R2?** Vercel's free (Hobby) plan accepts uploads up to 100 MB and 15,000 files
🟡. The site alone is about 1 GB. R2's free tier needs an R2 subscription checkout 🟡. Both remain
options if the project ever pays for hosting.

## Before you start (once)

1. **Free disk space: at least 6 GB.** A public release is 2.2 GB, and the website build needs
   about 2 GB while it runs. On 2026-11-19 the Mac had 2.7 GB free, so the agent did not build
   the release. The old private previews `pipeline/data/build/releases-preview/v2026.11.17-preview.1`
   and `-preview.2` (2.1 GB each) are superseded by `-preview.3` and can be deleted to make room.
2. **Create a free Cloudflare account** at dash.cloudflare.com. Choose the Free plan. Do not add
   R2 or a paid Workers plan. ❓ The agent has not confirmed that sign-up asks for no card.
3. **Log Wrangler in** (it opens your browser):

   ```bash
   npx -y wrangler@4.156.0 login
   ```

4. **GitHub CLI** is already used for pull requests; `gh auth status` should show you logged in.

## Deploy, step by step

Run each block from the repository root unless it says otherwise. Replace `v2026.11.19` with the
version you are publishing.

### 1. Build the public release (decision D-054 item 4)

```bash
cd pipeline
uv run slf release --version v2026.11.19 \
  --dataset census-2024-gnd-tables --dataset census-2024-topic-tables --dataset election-results \
  --profile-dir data/build/profile-v03 \
  --notes "First public release: Census 2024 (non-commercial, D-030/D-032) and the 2024 presidential election (D-039)."
```

It must print `public release: data/build/releases/v2026.11.19`. A dry run of the rights gate on
2026-11-19 refused nothing for these three datasets ✅. If you leave out `--dataset`, the code's
`example` dataset is refused. Then run the Q01 audit on the new release (AGENTS.md command table)
before publishing.

### 2. Build the public atlas bundle

```bash
uv run slf atlas export --public --release-dir data/build/releases/v2026.11.19 \
  --profile-dir data/build/profile-v03 --spaces-dir data/build/spaces --grid-dir data/build/grid \
  --landscape-dir data/build/landscape --subnational-dir data/build/subnational \
  --events-dir data/build/events --out-dir data/build/atlas-public
cd ..
```

`--public` refuses a release that is not publishable. It leaves out the 2012 comparison
(`change.json`, the trajectory space: D-038) and named features (D-049). Its manifest says
`"public": true`.

### 3. Stage and deploy the data site

```bash
node deploy/stage-data-site.mjs pipeline/data/build/releases/v2026.11.19
```

```bash
npx -y wrangler@4.156.0 deploy --config deploy/cloudflare/data/wrangler.jsonc
```

The staging step hard-links files, so it uses no extra disk. It refuses a release that is not
publishable, and it lists the files over 25 MiB in `deploy/build/large-files.tsv`. The deploy
prints the data site's address, for example `https://srilankafacts-data.<your-subdomain>.workers.dev`.
Note it down for step 5.

### 4. Put the large files on a GitHub release

```bash
cd pipeline/data/build/releases/v2026.11.19 && gh release create data-v2026.11.19 --repo asithakuruppu/srilankafacts --title "Data files v2026.11.19" --notes-file NOTICE.md geography_versions.geoparquet observations/census-2024-gnd-tables.csv observations/census-2024-topic-tables.csv && cd -
```

Their sha256 hashes are in `deploy/build/large-files.tsv` and the release's `CHECKSUMS.sha256`.
The download address base is
`https://github.com/asithakuruppu/srilankafacts/releases/download/data-v2026.11.19`.

### 5. Build the website

```bash
cd web
SLF_RELEASE_DIR=../pipeline/data/build/releases/v2026.11.19 \
SLF_ATLAS_DIR=../pipeline/data/build/atlas-public/v2026.11.19 \
NEXT_PUBLIC_SITE_URL=https://srilankafacts-site.<your-subdomain>.workers.dev \
NEXT_PUBLIC_DATA_BASE=https://srilankafacts-data.<your-subdomain>.workers.dev \
NEXT_PUBLIC_LARGE_FILES_BASE=https://github.com/asithakuruppu/srilankafacts/releases/download/data-v2026.11.19 \
NEXT_PUBLIC_DUCKDB_BASE=https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.32.0/dist/ \
npx -y pnpm@12.18.0 build:static
cd ..
```

The build ends with a line such as
`static site: 6840 files, 962.0 MB, largest 16.1 MB; public release v2026.11.19`. It fails if the
site would break the free plan's limits. If that line says `PRIVATE PREVIEW`, stop: the build
read a preview release. Optional: set `NEXT_PUBLIC_REPORT_URL` to show a "report a problem" link.

### 6. Deploy the website

```bash
npx -y wrangler@4.156.0 deploy --config deploy/cloudflare/site/wrangler.jsonc
```

### 7. Check it

Open the site and check:

- [ ] The header says the release is public and non-commercial, not "private preview".
- [ ] `/place/LK11` (a district) loads without JavaScript.
- [ ] `/place/LK1103005` (a GN division) shows its values, breadcrumb and rank.
- [ ] `/data` links files to the data site and the three large files to GitHub.
- [ ] `/query` returns rows.
- [ ] The atlas has no Change history and no named features.
- [ ] `robots.txt` allows indexing.

## Updating and rolling back

- **New release:** repeat steps 1 to 6 with a new version. Releases are immutable; never reuse
  a version.
- **Roll back:** `npx -y wrangler@4.156.0 rollback --config deploy/cloudflare/site/wrangler.jsonc`
  (and the same for the data site) returns to the previous upload 🟡.
- **Take something down** (for example a DCS takedown request under D-030, 7 days): rebuild
  without the dataset and redeploy both sites, then delete the GitHub release assets.

## Custom domain (optional, free)

The `workers.dev` addresses work. To use a domain such as `kuruppu.xyz`, add it to Cloudflare
(free plan), switch its nameservers at the registrar, then add a Custom Domain to each Worker
(for example the domain itself for the site and `data.` for the data site). After that, rebuild
the site with the new `NEXT_PUBLIC_SITE_URL` and `NEXT_PUBLIC_DATA_BASE`.

## What was tested, and what was not

- ✅ The static site was built from `v2026.11.17-preview.3` and served by Wrangler's local
  Cloudflare runtime:
  - district and DS pages are served as files
  - GN addresses render in the browser from the API, both opened directly and from a DS page
  - unknown GN ids show "not found"; unknown paths return 404
  - `/query` returned 25 rows using the jsDelivr engine
- ✅ The data site's headers (CORS, content types, caching) were checked on a 3,003-file subset.
  The local runtime fails to start with all 16,156 files (`spawn EBADF`). This is a limit of the
  local emulator, not of the documented free plan, but **the full data site has not been served
  anywhere yet** ❓.
- ❓ Nothing has been uploaded to Cloudflare or GitHub. The first real deploy is the first check
  of the vendors' limits.
