# CHORD: Learning Dexterous Manipulation Using Contact Wrench Guidance from Human Demonstration

> [Paper](https://arxiv.org/abs/2607.00033) · [Project](https://nvidia-isaac.github.io/video_to_data/chord/) · metadata in [README](../README.md) · summary in [SUMMARIES.md](../SUMMARIES.md)

## My take

This is impressive work backed by substantial engineering effort.

It inspires me to explore using object-centric information as guidance while penalizing unintended and missed contacts.

## Notes

Like [SimToolReal](simtoolreal-object-centric-zero-shot-dexterous-tool-manipulation.md), this work uses object motion tracking as part of the reinforcement learning reward. Specifically, CHORD's task reward encourages the object's pose trajectory to follow the human demonstration.

The contact-guidance ablation compares three reward formulations: **CHORD**, which uses the contact-wrench support reward; **Position Only**, which replaces it with the contact-position reward used by DexMachina; and **No Contact**, which uses only the shared task- and motion-imitation rewards. Thus, these are three training variants rather than three independent reward terms used together.
