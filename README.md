MarkovBot
=========

Markov chain based IRC bot.

# Installation/Usage #


**Requires Python 3**

```sh
$ virtualenv-3.4 .env
$ .env/bin/pip install requirements.txt
$ cp config.py.example config.py
$ $EDITOR config.py
$ .env/bin/python gen_db.py <output db> <k> < source_material.txt # Expects
ZNC-formatted log file
$ .env/bin/python markovbot.py
```

I'm using k=2.
