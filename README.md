# SCP-079-MANAGE

This bot is used to manage other bots.

## How to use

See [this article](https://scp-079.org/manage/).

## To Do List

- [x] Basic functions
- [x] Support NOPORN、RECHECK
- [x] Leave function
- [x] Add or remove object lists

## Requirements

- Python 3.6 or higher
- pip: `pip install -r requirements.txt` or `pip install -U APScheduler pyAesCrypt pyrogram[fast]`

## Files

- plugins
    - functions
        - `channel.py` : Functions about channel
        - `etc.py` : Miscellaneous
        - `file.py` : Save files
        - `filters.py` : Some filters
        - `group.py` : Functions about group
        - `ids.py` : Modify id lists
        - `manage.py` : MANAGE's core functions
        - `telegram.py` : Some telegram functions
        - `timers.py` : Timer functions
        - `user.py` : Functions about user and channel object
    - handlers
        - `callback.py` : Handle callbacks
        - `command` : Handle commands
        - `message.py`: Handle messages
    - `glovar.py` : Global variables
- `.gitignore` : Ignore
- `config.ini.example` -> `config.ini` : Configuration
- `LICENSE` : GPLv3
- `main.py` : Start here
- `README.md` : This file
- `requirements.txt` : Managed by pip

## Contribute

Welcome to make this project even better. You can submit merge requests, or report issues.

## License

Licensed under the terms of the [GNU General Public License v3](LICENSE).
