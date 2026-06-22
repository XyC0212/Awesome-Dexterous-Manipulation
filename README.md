# Awesome-Dexterous-Manipulation

A curated collection of the latest papers and resources on dexterous robotic manipulation, driven by a passion for research and the ambition to push the boundaries of robotics toward more capable, adaptive, and intelligent manipulation systems.

> 🔎 **[Interactive filterable version »](https://xyc0212.github.io/Awesome-Dexterous-Manipulation/)** — live search and tag filters (RL / IL / WM / Tac / HW / Tele). Requires GitHub Pages to be enabled (Settings → Pages → deploy from branch → `/docs`).

## Categories

Each paper is tagged across the following themes:

- **RL** — Reinforcement Learning
- **IL** — Imitation Learning / Learning from Demonstration
- **WM** — World Model / model-based learning
- **Tac** — Tactile / visuotactile sensing
- **HW** — Hardware (dexterous hands, sensors, data-collection devices)
- **Tele** — Teleoperation & data collection

## Papers

<!-- markdownlint-disable MD060 -->

| # | Title | Venue | Year | Affiliation | RL | IL | WM | Tac | HW | Tele | Links |
|---|-------|-------|------|-------------|:--:|:--:|:--:|:--:|:--:|:----:|-------|
| 1 | T-Rex: Tactile-Reactive Dexterous Manipulation | arXiv | 2026 | UC Berkeley | | ✅ | | ✅ | ✅ | | [Paper](https://arxiv.org/abs/2606.17055) |

<!-- markdownlint-enable MD060 -->

## Contributing

Contributions are welcome! To add a paper, append a new row to the table above with:

- The **title** in the Title column, with all links in the **Links** column.
- The **venue** (e.g. CoRL, ICRA, RSS, NeurIPS, arXiv) and **year**.
- A `✅` in each theme column that genuinely applies (`RL`, `IL`, `WM`, `Tac`, `HW`, `Tele`).
- Links in the format `[Paper](url) · [Project](url) · [Code](url)` (include only the ones that exist).

Please keep the table sorted with the newest papers first.

The README table is the single source of truth. After editing it, regenerate the interactive page with:

```bash
python3 scripts/gen_site.py
```

and commit the updated `docs/index.html`.
