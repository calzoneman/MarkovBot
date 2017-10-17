import irc.bot
import irc.connection
import irc.strings
import random
import re
import ssl
import sys
import time

import config
from db import MarkovDB
from markov import Markov

ACCOUNT_LOOKUP = re.compile(r"Information on ([-\w\[\]\{\}\^\|`]+)\s*"
                            r"\(account ([-\w\[\]\{\}\^`]+)\)")
NOT_REGISTERED = re.compile(r"([-\w\[\]\{\}\^`]+)")

irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer

def cooldown_for(chan):
    if chan in config.cooldown_override:
        return config.cooldown_override[chan]
    else:
        return config.cooldown

class MarkovBot(irc.bot.SingleServerIRCBot):
    def __init__(self, markov, channels, nickname, server_list, nspass=None,
            use_ssl=False):
        if use_ssl:
            kwargs = {
                'connect_factory': irc.connection.Factory(
                    wrapper=ssl.wrap_socket)
            }
        else:
            kwargs = {}

        irc.bot.SingleServerIRCBot.__init__(self, server_list, nickname,
                nickname, **kwargs)
        self.markov = markov
        self.chanlist = channels
        self.nspass = nspass
        self._acclookup_queue = []
        self.timers = {}
        self.init_time = time.time()

    def should_cooldown(self, chan):
        if chan not in self.timers:
            return False

        return self.timers[chan] + cooldown_for(chan) >= time.time()

    def lookup_account(self, name, cb):
        self.connection.privmsg("NickServ", "INFO " + name)
        self._acclookup_queue.append((name, cb))

    def _handle_nickserv(self, c, e):
        msg = e.arguments[0].replace("\x02", "")
        if msg.startswith("Information on"):
            m = ACCOUNT_LOOKUP.search(msg)
            name = m.group(1)
            acct = m.group(2)
            if acct == "*":
                acct = None
            remove = set()
            for pending in self._acclookup_queue:
                if pending[0].lower() == name.lower():
                    pending[1](acct.lower())
                    remove.add(pending)
            for old in remove:
                self._acclookup_queue.remove(old)
        elif msg.endswith("is not registered."):
            m = NOT_REGISTERED.search(msg)
            name = m.group(1)
            remove = set()
            for pending in self._acclookup_queue:
                if pending[0].lower() == name.lower():
                    pending[1](None)
                    remove.add(pending)
            for old in remove:
                self._acclookup_queue.remove(old)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "`")

    def on_welcome(self, c, e):
        if self.nspass:
            c.privmsg("NickServ", "IDENTIFY " + self.nspass)
        for channel in self.chanlist:
            c.join(channel)

    def on_privnotice(self, c, e):
        n = e.source.nick
        if n == "NickServ":
            self._handle_nickserv(c, e)
            return

    def on_privmsg(self, c, e):
        n = e.source.nick

        args = e.arguments[0].split()
        if args[0] == "join" and len(args) == 2:
            def after_admin(acc):
                if acc not in config.admins:
                    return
                c.join(args[1])
            self.lookup_account(n, after_admin)
        elif args[0] == "part" and len(args) == 2:
            def after_admin(acc):
                if acc not in config.admins:
                    return
                c.part(args[1])
            self.lookup_account(n, after_admin)
        else:
            c.privmsg(n, "I don't recognize that command.")

    def on_pubmsg(self, c, e):
        msg = e.arguments[0]

        # Require a cooldown period after bot startup (prevents channels with
        # +H from triggering the bot with scrollback)
        if time.time() < self.init_time + cooldown_for(e.target):
            return

        if c.get_nickname().lower() not in msg.lower():
            # Unless the bot is specifically addressed, only reply
            # with certain probability
            if random.random() > config.random_chance:
                return

        # Require a cooldown period between successive messages
        if self.should_cooldown(e.target):
            return

        try:
            # only consider seeds that do not include the bot's name
            words = []
            for w in msg.split():
                if c.get_nickname().lower() not in w.lower():
                    words.append(w)

            seed = self.markov.random_head(words) if len(words) > 0 else None

            print("Seed is", seed)

            size = random.randint(4, 14)
            text = self.markov.chain(length=size, head=seed)

            if text[-1] not in "?!,.;:'\"":
                text += random.choice("?!.")

            # Add underscores to usernames to prevent highlighting people
            names = list(self.channels[e.target].users())
            names += config.extra_nohighlight
            for name in names:
                filtered = (name[0:int(len(name)/2)] +
                            "_" +
                            name[int(len(name)/2):])
                # Escape any regex special chars that may appear in the name
                name = re.sub(r"([\\\.\?\+\*\$\^\|\(\)\[\]\{\}])", r"\\\1",
                        name)
                name = r"\b" + name + r"\b" # Only match on word boundaries
                text = re.sub(name, filtered, text, flags=re.I)

            # Tag links just in case
            text = text.replace("http://", "[might be nsfw] http://").replace(
                    "https://", "[might be nsfw] https://")

            # Avoid triggering bots or GameServ commands
            if text.startswith("!") or text.startswith("."):
                text = text[1:]

            # IRC messages are at most 512 characters (incl. \r\n)
            if len(text) > 510:
                text = text.substring(0, 510)
            c.privmsg(e.target, text)
            self.timers[e.target] = time.time()
        except Exception as err:
            c.privmsg(e.target, "[Uncaught Exception] " + str(err))
            print(err, file=sys.stderr)

    def on_kick(self, c, e):
        # Auto rejoin on kick
        if e.arguments[0] == c.get_nickname():
            time.sleep(1)
            c.join(e.target)

def main():
    db = MarkovDB(config.database, k=config.k)
    markov = Markov(db)
    server = irc.bot.ServerSpec(config.server, config.port,
            config.server_password)
    bot = MarkovBot(markov, config.channels, config.nick, [server],
            nspass=config.password, use_ssl=config.ssl)

    import signal
    def sigint(signal, frame):
        print("Caught SIGINT, terminating")
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint)

    bot.start()

if __name__ == "__main__":
    main()
