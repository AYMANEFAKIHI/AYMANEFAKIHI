# Setup checklist — the parts only you can do

Everything Claude generated lives in this folder. These are the by-hand steps
(account actions Claude cannot and must not do for you).

---

## 0. Fill in your details
Open `config.py`, replace every `[...]` with your real info, and set the palette
(or keep the defaults). Then regenerate:

```bash
python make_demo_assets.py   # ONLY for the demo — skip once you have a real photo
python generate_banner.py    # -> output/dark.svg, output/light.svg
```

Put your real photo at `assets/photo.jpg` (flat background, head-and-shoulders,
1000px+ short edge) and your three logo references as PNGs in `assets/logos/`.

---

## 1. Banner (Phase 1)
- [ ] Upload `output/dark.svg` and `output/light.svg` to the **root** of your
      `USERNAME/USERNAME` repo on branch `main` (the README points at
      `raw.githubusercontent.com/.../main/dark.svg`).
- [ ] If it "doesn't update", it's almost always CDN cache — hard-refresh with
      `?v=999` on the raw URL, and confirm you're viewing the right OS theme
      (dark assets only render in dark mode).

> File size: the banner lands ~900KB–1MB per SVG. That's expected for ~17k dots.

---

## 2. Stats cards (Phase 2) — self-host, don't use the public instance
The public github-readme-stats instance is shared by thousands and constantly
returns "API rate limit exceeded". Host your own — 10 minutes:

1. [ ] **Create a classic token:** GitHub → Settings → Developer settings →
       Personal access tokens → **Tokens (classic)** → Generate new (classic) →
       scope **`repo`** → **No expiration**. **Copy it immediately** and never
       paste it anywhere public.
2. [ ] **Fork** `anuraghazra/github-readme-stats`.
3. [ ] **Vercel** → sign up with GitHub → **Hobby (free)** → Add New Project →
       import your fork.
4. [ ] Add environment variable **`PAT_1`** = your token → **Deploy**.
5. [ ] Copy your instance URL (e.g. `github-readme-stats-you.vercel.app`) and
       replace **`STATS_INSTANCE`** in `README.md`.

**Why `hide_rank=true`:** the letter rank is stars-weighted, so a newer account
scores harshly regardless of real activity. Hiding it is more honest, not less —
the streak and language cards already show your actual work.

---

## 3. Contribution snake (Phase 3)
- [ ] Commit `.github/workflows/snake.yml` to `main`.
- [ ] **Repo → Settings → Actions → General → Workflow permissions →
      Read and write permissions.** This is the *repo's* settings, not your
      account settings.
- [ ] Run the workflow once (Actions tab → Generate Contribution Snake → Run
      workflow) and wait for **green**.
- [ ] Only *then* add the snake `<picture>` block — the `output` branch does not
      exist until the first successful run.

> The dark snake's empty cell is `#2d3343` (a visible slate) on purpose: a
> near-black empty cell disappears against GitHub's `#0d1117` and the grid looks
> broken.

---

## 4. Social badges (Phase 4)
Already in `README.md`. Replace `MAIL_ADDR`, `PORTFOLIO_URL`, `LINKEDIN_URL`,
`INSTAGRAM_URL`, `FACEBOOK_URL`.

> **LinkedIn badge:** its logo only renders on brand blue `#0A66C2`. On any
> custom colour the glyph silently vanishes, leaving just text — so that one
> badge stays brand blue by design. The others recolour fine.
> No GitHub badge — it's circular on your own profile.

---

## 5. Final find-&-replace
In `README.md`, replace **`USERNAME`** (all occurrences) with your handle, then
commit `README.md` to `USERNAME/USERNAME` on `main`.

---

## Known: 1080p moiré
At GitHub's ~900px width the dot lattice can show faint vertical banding; it
vanishes on zoom. Already tried & rejected: removing crispEdges (softens the
face), capping run lengths (no effect), per-dot jitter (file balloons to 2.8MB).
The only real fix is a coarser portrait (fewer, larger dots) — most visitors
never notice. Don't burn hours here.

## Source of truth
Keep `config.py`, the generator scripts, and `build/*.npy` — they regenerate the
SVGs. The SVGs themselves are outputs, not the source.
