# ml

Machine learning for the DDDS: CV model training, RF drone classification (US-15) and anomaly detection (US-14). Owner: Diego.

## ml/rfuav (third-party reference code)

`rfuav/` contains the code from the **RFUAV benchmark** by its original authors, used here as a starting point for RF classification.
It is **not** written by Team 31 and keeps its original Apache 2.0 license (`rfuav/LICENSE`).

- Paper: *RFUAV: A Benchmark Dataset for Unmanned Aerial Vehicle Detection and Identification*, https://arxiv.org/abs/2503.09033
- Original README: `rfuav/README.md`

Team-written ML code should go in its own folder under `ml/`, not inside `rfuav/`.
