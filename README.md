# SNOO

This is an API client to the [SNOO Smart Bassinet](https://www.happiestbaby.com/products/snoo-smart-bassinet). The SNOO is a bassinet that will rock your baby to sleep, and responds to the baby by trying to sooth it with different rocking motions and sounds when it detects crying.

Currently, it supports getting the current session data from SNOO, and historic data. It does not allow you to control the SNOO (the control API is provided by [PubNub](https://www.pubnub.com) and is different from the read-only data API hosted by happiestbaby.com)

# A word of caution

The SNOO API is undocumented. Using it might or might not violate Happiest Baby, Inc [Terms of Service](https://www.happiestbaby.com/pages/terms-of-service). Use at your own risk.

# Usage

## Installation

```sh
pip install snoo
```

## Command line usage

To get the status of your snoo, simply run

```
$ snoo status
Soothing 26m
```

The first time you run it, it will prompt for your username and password. These will be stored in either `~/.snoo_config` or `~/.config/snoo/snoo.config`, depending on your system. The output of the `snoo` command is the status (`Awake`, `Asleep`, or `Soothing`), and the duration of the current session.

## Exporting data

To export data of each individual session, use

```
$ snoo sessions --start DATE --end DATE
```

where `DATE` follows the format `2019-12-03`. By default, `--start` and `--end` correspond to yesterday and today, respectively.

The result is a CSV formatted list of sessions in the snoo, eg.

```csv
start_time,end_time,duration,asleep,soothing
2019-12-03T12:35:11,2019-12-03T13:59:04,5033,4218,815
2019-12-03T15:28:13,2019-12-03T15:28:41,28,17,11
...
```

where `duration`, `asleep`, and `soothing` are durations given in _seconds_.

Alternatively, you can get aggregated information about each day using `snoo days`:

```csv
date,naps,longestSleep,totalSleep,daySleep,nightSleep,nightWakings,timezone
2019-12-03,6,12933,58035,25038,32997,4,None
```

Again, all durations are given in seconds. How `daySleep` and `nightSleep` are defined is set in your Snoo app.

## Programmatic usage

```python
from snoo import Client

client = Client()
# Find out where your config is stored
print(client.config_path)
# Get data from your current session
current_session = client.get_current_session()
# Print the status of the current session.
print(client.status())
```
