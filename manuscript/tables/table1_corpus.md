# Table 1. Held-out evaluation split, stratified by STEM domain × ETH alt-text category.

Each cell gives the figure count for one stratum of the 30-figure held-out subset.

| Domain                         | Simple | Linked | Decorative | Complex | Total |
|---|---|---|---|---|---|
| Chemistry                      | 2 | 2 | 1 | 3 | 8 |
| Mathematics and computer science | 2 | 2 | 1 | 3 | 8 |
| Biology                        | 1 | 2 | 1 | 3 | 7 |
| Physics                        | 1 | 2 | 1 | 3 | 7 |
| **Total**                      | **6** | **8** | **4** | **12** | **30** |

The full 150-figure corpus partitions into 120 calibration and 30 held-out
figures. The loop and DPO use the calibration figures. Fine-tuning never
touches the held-out figures; they are the surface against which the
pre-registered convergence threshold is evaluated.
