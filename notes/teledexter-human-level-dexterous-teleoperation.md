# TeleDexter: Towards Human-level Dexterous Teleoperation

> [Paper](https://arxiv.org/abs/2607.11481) · [Project](https://bigai-dex.github.io/blog/teledexter/) · metadata in [README](../README.md) · summary in [SUMMARIES.md](../SUMMARIES.md)

## My take

The TeleDexter is one hand-object co-tracking for human-level dexterous teleoperation. 

One weakness is the requirement of the Motion Capturing System.

This paper seems to be one upgrade of simtoolreal. Use the human hand pose from glove and the object pose as the input.

## Notes

- **System**: two phases — kinematic retargeting for pre-grasp, then an RL **co-tracking controller** takes over after grasp. Inputs: NOKOV optical mocap of wrist + fingertips + object 6D pose at 30 Hz; policy sees hand joint positions, object pose, gravity direction, previous action, and a co-tracking goal (target fingertip positions + object pose). It only specifies *what* to match, never *how* contacts should transition.
- **Reward**: hybrid of sparse subgoal-reaching (fires when per-finger / object pose tolerances hold for N_stay frames, exponential kernels on errors) + a small dense tracking term for exploration + time penalty. Ablation: sparse subgoals dramatically beat dense frame-wise tracking (378.6 vs 115.8 episode length on cuboid).
- **Training**: single-stage RL with SAPG, ~62k parallel Isaac Gym envs, ~10^10 steps. Curriculum: start with reduced gravity, then tighten tolerances and widen inter-subgoal jumps.
- **Sim-to-real trick — random action masking**: randomly freeze a sampled subset of action dimensions at the previous command for random durations, preventing overfitting to sim dynamics; removing it costs 30–73 success-rate points.
- **Hardware**: LeapHand (4 fingers, 16 DoF) and SharpaWave (5 fingers, 22 DoF) on a Franka FR3. Offline capture uses dense markers; real-time teleop only needs lightweight wrist + fingertip markers.
- **Results**: 75.2% average success over 7 tasks (3 reorientation: cylinder/cuboid/bunny; 4 tool-use: hammer, brush, screwdriver, light-bulb replacement) while DexRT, GeoRT, DexGen, and SimToolReal baselines essentially all fail (best baseline: DexRT ~6.7% on cylinder reorientation).
- **Demos → autonomy**: 50 teleop demos per task train Diffusion Policy (RGB, third-person + wrist cams): BulbInstall 46.7%, HammerDriver 73.3%, BrushForward 40.0% — tasks no baseline teleop system can even demonstrate.
- **Limitations**: per-object policy training (no unified object-conditioned controller); depends on mocap (authors themselves call out markerless vision tracking as the fix); failure modes: tool-impact perturbations, contact-transition jams, and tracking stalls from missing tactile feedback (can't adapt regrasps).
