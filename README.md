# SNOO

This is an API client to the [SNOO Smart Bassinet](https://www.happiestbaby.com/products/snoo-smart-bassinet). The SNOO is a bassinet that will rock your baby to sleep, and responds to the baby by trying to sooth it with different rocking motions and sounds when it detects crying.

Currently, it supports getting the current session data from SNOO, and historic data.

# Usage

## Installation

```sh
pip install snoo
```

## Command line usage

To get the status of your snoo, simply run

```
$ snoo
```

The first time you run it, it will prompt for your username and password. These will be stored in either `~/.snoo_config` or `~/.config/snoo/snoo.config`, depending on your system. The output of the `snoo` command is the status (`Awake`, `Asleep`, or `Soothing`), and the duration of the current session.

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
