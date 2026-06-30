---
name: add-paper
description: Catalogue a dexterous-manipulation paper into this repo. Use this WHENEVER the user provides a paper to add — an arXiv link, any URL, a title, or a PDF/file. It reads the paper, assigns theme labels (RL/IL/WM/Tac/HW/Tele), appends a row to the README table, writes a one-sentence summary to summaries/ for later retrieval, regenerates the GitHub Pages site, and commits.
---

# Add a paper to Awesome-Dexterous-Manipulation

When the user gives you a paper, run this end-to-end. The README table is the single
source of truth; everything else is derived from it.

## Labels

Assign **every** label that genuinely applies (a paper often has several). Do not add a
label that doesn't truly apply.

- **RL** — Reinforcement Learning
- **IL** — Imitation Learning / Learning from Demonstration
- **WM** — World Model / model-based learning
- **HV** — Learning from Human Video
- **Tac** — Tactile / visuotactile sensing
- **HW** — Hardware (dexterous hands, sensors, data-collection devices)
- **Tele** — Teleoperation & data collection

## Steps

1. **Read the paper.** Fetch the source (WebFetch for a URL; for arXiv use the
   `/abs/<id>` page for metadata and `/html/<id>` or the PDF for content; Read for a local
   file). Extract:
   - exact **title**
   - **venue** (publication venue, or `arXiv` if unpublished) and **year**
   - **primary (first) affiliation** only — unless the user asks to list more
   - **links**: a `Paper` link (prefer `https://arxiv.org/abs/...`), plus `Project` and
     `Code` links **only if they genuinely exist** (verify; never invent a URL)
   Read enough of the abstract/method to assign labels and write the summary.

2. **Determine the labels** from the six above.

3. **Update the README table** ([README.md](../../../README.md)). Insert a new row in the
   correct sorted position (**newest year first**; new same-year papers go at the top of
   that year). Row format (12 columns):

   ```
   | <#> | <Title> | <Venue> | <Year> | <Primary Affiliation> | <RL> | <IL> | <WM> | <Tac> | <HW> | <Tele> | <Links> |
   ```

   Put `✅` in each applicable label column, leave the others blank. Links column:
   `[Paper](url) · [Project](url) · [Code](url)` (only the ones that exist). The `#` value
   doesn't matter at insert time — step 5 renumbers.

4. **Write the summary** by prepending one bullet to the top of the list in
   [SUMMARIES.md](../../../SUMMARIES.md) (newest first, matching the table). Format:

   ```text
   - **<Title>** ([paper](<url>)) — <one specific sentence: method + key result>.
   ```

   Keep it to a single sentence. This file is the retrieval index; do not duplicate
   labels/venue/year/affiliation here — those live in the README table.

   Then create an empty **notes stub** at `notes/<slug>.md` for the user to fill in their
   own opinion, following the template of the existing files in
   [notes/](../../../notes/) (title heading, a `> ` link line, a `## My take` section with
   a placeholder, and a `## Notes` section). Never overwrite a notes file that already
   exists.

5. **Renumber and regenerate**, from the repo root:

   ```bash
   python3 scripts/renumber.py && python3 scripts/gen_site.py
   ```

6. **Commit.** Stage and commit all changes with a message like
   `Add <short title> to the table`. Then push (`git push`) — the user keeps this repo
   public on GitHub Pages and wants new papers to go live. If you are unsure whether to
   push, ask.

7. **Report** to the user: the new table row, the chosen labels, the one-sentence summary,
   and the summary file path.

## Retrieval

When the user later asks you to find / recall a paper ("which paper used a tactile glove?",
"the world-model one from 2025", "the paper I liked for its dataset"), read
[SUMMARIES.md](../../../SUMMARIES.md) for the summaries, the
[README table](../../../README.md) for labels/year/affiliation, and the
[notes/](../../../notes/) files for the user's own opinions (`## My take`). Answer from the
matching entry, citing the paper link.
