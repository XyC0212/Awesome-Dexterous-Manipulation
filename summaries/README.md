# Summaries

One file per paper, used as a lightweight **retrieval index**. Each file is named
after the paper's slug and carries machine-readable frontmatter plus a one-sentence
summary. To find a paper, search this folder (e.g. `grep -ri "tactile" summaries/`).

Format:

```markdown
---
title: <exact paper title>
slug: <kebab-case-slug>
venue: <CoRL | ICRA | RSS | NeurIPS | arXiv | ...>
year: <YYYY>
affiliation: <primary affiliation>
labels: [RL, IL, WM, Tac, HW, Tele]   # only those that apply
paper: <url>
project: <url or empty>
code: <url or empty>
added: <YYYY-MM-DD>
---

<one sentence summarizing the paper>
```

Labels: **RL** (Reinforcement Learning) · **IL** (Imitation Learning) ·
**WM** (World Model) · **Tac** (Tactile) · **HW** (Hardware) · **Tele** (Teleoperation).
