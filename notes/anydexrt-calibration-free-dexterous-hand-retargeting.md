# AnyDexRT: Calibration-Free Dexterous Hand Retargeting with Few-Shot Human Guidance

> [Paper](https://arxiv.org/abs/2607.08341) · [Project](https://chenxi-wang.github.io/projects/anydexrt) · metadata in [README](../README.md) · summary in [SUMMARIES.md](../SUMMARIES.md)

## My take

This paper focuses on calibration-free hand retargeting for dexterous teleoperation. It combines self-supervised fingertip-correspondence learning with a few paired human–robot anchor poses.

One interesting design is the partial Chamfer loss: it maps the human fingertip space into the robot's feasible space without forcing coverage of redundant robot-only regions. A contact classifier further detects pinch intent and refines pinch poses.

The method assumes that the robot hand is structurally similar to a human hand and that, after a suitable geometric transformation, its fingertip space covers the human fingertip motion space.

## Notes

Three requirements for a good retargeting algorithm:

1. **Intuitiveness:** Preserve motion intent and produce predictable robot motions.

2. **Calibration efficiency:** Minimize precise calibration and manual tuning.

3. **Generality:** Support different human-like robot hands without hand-specific redesign.

The baselines are an offline optimization method and [GeoRT](https://arxiv.org/abs/2503.07541).

The real-world setup uses a Flexiv Rizon 4 arm, Wuji Hand, Manus glove, and HTC Vive Tracker.
