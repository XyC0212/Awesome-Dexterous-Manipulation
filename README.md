# Awesome-Dexterous-Manipulation

A curated collection of the latest papers and resources on dexterous robotic manipulation, driven by a passion for research and the ambition to push the boundaries of robotics toward more capable, adaptive, and intelligent manipulation systems.

> 🔎 **[Interactive filterable version »](https://xyc0212.github.io/Awesome-Dexterous-Manipulation/)** — live search and tag filters (RL / IL / WM / Tac / HW / Tele). Requires GitHub Pages to be enabled (Settings → Pages → deploy from branch → `/docs`).

## Categories

Each paper is tagged across the following themes:

- **RL** — Reinforcement Learning
- **IL** — Imitation Learning / Learning from Demonstration
- **WM** — World Model / model-based learning
- **HV** — Learning from Human Video
- **Tac** — Tactile / visuotactile sensing
- **HW** — Hardware (dexterous hands, sensors, data-collection devices)
- **Tele** — Teleoperation & data collection

## Papers

<!-- markdownlint-disable MD060 -->

| # | Title | Venue | Year | Affiliation | RL | IL | WM | HV | Tac | HW | Tele | Links |
|---|-------|-------|------|-------------|:--:|:--:|:--:|:--:|:--:|:--:|:----:|-------|
| 1 | DexJoCo: A Benchmark and Toolkit for Task-Oriented Dexterous Manipulation on MuJoCo | arXiv | 2026 | CASIA | | ✅ | | | | ✅ | ✅ | [Paper](https://arxiv.org/abs/2605.16257) · [Project](https://dexjoco.github.io) |
| 2 | CHORD: Learning Dexterous Manipulation Using Contact Wrench Guidance from Human Demonstration | arXiv | 2026 | NVIDIA | ✅ | ✅ | | ✅ | | | | [Paper](https://arxiv.org/abs/2607.00033) · [Project](https://nvidia-isaac.github.io/video_to_data/chord/) |
| 3 | HumanEgo: Zero-Shot Robot Learning from Minutes of Human Egocentric Videos | arXiv | 2026 | University of Maryland | | ✅ | | ✅ | | | | [Paper](https://arxiv.org/abs/2605.24934) · [Project](https://humanego-ai.github.io) · [Code](https://github.com/TX-Leo/HumanEgo) |
| 4 | Do as I Do: Dexterous Manipulation Data from Everyday Human Videos | arXiv | 2026 | UC Berkeley | | ✅ | | ✅ | | ✅ | | [Paper](https://arxiv.org/abs/2606.19333) · [Project](https://do-as-i-do.com/) |
| 5 | T-Rex: Tactile-Reactive Dexterous Manipulation | arXiv | 2026 | UC Berkeley, NVIDIA | | ✅ | | ✅ | ✅ | ✅ | | [Paper](https://arxiv.org/abs/2606.17055) |
| 6 | EgoEngine: From Egocentric Human Videos to High-Fidelity Dexterous Robot Demonstrations | arXiv | 2026 | Georgia Tech | | ✅ | | ✅ | | | | [Paper](https://arxiv.org/abs/2606.12604) · [Project](https://egoengine.github.io/) |
| 7 | Video2Sim2Real: Full-Stack Autonomous Dexterous Skill Acquisition from a Single Human Video | arXiv | 2026 | Georgia Tech | ✅ | ✅ | | ✅ | | ✅ | | [Paper](https://arxiv.org/abs/2606.08828) · [Project](https://video2sim2real.github.io/) |
| 8 | SimToolReal: An Object-Centric Policy for Zero-Shot Dexterous Tool Manipulation | arXiv | 2026 | Cornell University | ✅ | | | ✅ | | ✅ | | [Paper](https://arxiv.org/abs/2602.16863) · [Project](https://simtoolreal.github.io/) |

<!-- markdownlint-enable MD060 -->

## Contributing

Contributions are welcome! To add a paper, append a new row to the table above with:

- The **title** in the Title column, with all links in the **Links** column.
- The **venue** (e.g. CoRL, ICRA, RSS, NeurIPS, arXiv) and **year**.
- A `✅` in each theme column that genuinely applies (`RL`, `IL`, `WM`, `HV`, `Tac`, `HW`, `Tele`).
- Links in the format `[Paper](url) · [Project](url) · [Code](url)` (include only the ones that exist).

Please keep the table sorted with the newest papers first.

The README table is the single source of truth. After editing it, regenerate the interactive page with:

```bash
python3 scripts/gen_site.py
```

and commit the updated `docs/index.html`.
