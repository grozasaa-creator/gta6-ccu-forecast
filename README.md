# gta6-ccu-forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/grozasaa-creator/gta6-ccu-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/grozasaa-creator/gta6-ccu-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Hour-by-hour quantile forecast (hours 2-24) of GTA VI's launch-day Twitch viewers. Past big launches are pooled as
log-ratio curves against their own hour 1, weighted by how closely their hour 1 resembles the case's (position against
the crest of the 14 hours before it, and size); the five quantiles come from a weighted mixture of normals whose
spread widens with the horizon. Python standard library only, offline, deterministic.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`tools/eval_loo.py` is a leave-one-out check over the comparables in a case file.

---

<sub>Entered on [make.fun](https://make.fun/?ref=tjxw76gf&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
