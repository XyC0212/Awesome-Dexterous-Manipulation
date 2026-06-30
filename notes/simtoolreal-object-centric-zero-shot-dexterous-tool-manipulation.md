# SimToolReal: An Object-Centric Policy for Zero-Shot Dexterous Tool Manipulation

> [Paper](https://arxiv.org/abs/2602.16863) · [Project](https://simtoolreal.github.io/) · metadata in [README](../README.md) · summary in [SUMMARIES.md](../SUMMARIES.md)

## My take

My opinion is one strong infrastructure and suitable representation to elimate the sim-to-real gap.

They also propose one benchmarks for the dexterous manipulation.

The human video processing adopt the SAM3D + FoundationPose conditioned on the extracted mesh to obtain the 6D pose.

The RL training is used the SAPG, a variant of PPO.

PPO faces the exploration bottlenecks.

One interesting thing is use the Asymmetric Critic

The critic use more information than actor.

## Notes

-
