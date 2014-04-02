import irc.bot
import irc.strings
import re
import random
import time
from markov import Markov

ACCOUNT_LOOKUP = re.compile(r"Information on ([-\w\[\]\{\}\^\|`]+)\s*"
                            r"\(account ([-\w\[\]\{\}\^`]+)\)")
NOT_REGISTERED = re.compile(r"([-\w\[\]\{\}\^`]+)")

admins = ["cyzon"]

class MarkovBot(irc.bot.SingleServerIRCBot):
    def __init__(self, markov, channels, nickname, server, port=6667, nspass=None):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.markov = markov
        self.chanlist = channels
        self.nspass = nspass
        self._acclookup_queue = []
        self.last_time = 0
        self.init_time = time.time()

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
                if acc not in admins:
                    return
                c.join(args[1])
            self.lookup_account(n, after_admin)
        elif args[0] == "part" and n in admins and len(args) == 2:
            def after_admin(acc):
                if acc not in admins:
                    return
                c.part(args[1])
            self.lookup_account(n, after_admin)
        else:
            c.privmsg(n, "I don't recognize that command.")

    def on_pubmsg(self, c, e):
        msg = e.arguments[0]

        if time.time() < self.init_time + 2.0:
            return

        if c.get_nickname().lower() not in msg.lower():
            # Unless the bot is specifically addressed, only reply 1% of the time
            if random.random() > 0.01:
                return

        # Cooldown
        if self.last_time + 2.0 > time.time():
            time.sleep(self.last_time + 2.0 - time.time())

        msg = msg.replace(c.get_nickname(), "")
        seed = None
        tries = 0
        while seed not in self.markov.seeds and tries < 10:
            seed = pick_seed(msg, self.markov.k)
            tries += 1

        if seed not in self.markov.seeds:
            seed = self.markov.find_seed(random.choice(msg.split()))
        print("Seed is", seed)

        size = random.randint(3, 20)
        text = self.markov.chain(length=size, seed=seed)
        if seed in self.markov.seeds:
            text = " ".join(seed) + " " + text

        if text[-1] not in "?!,.;:'\"":
            text += random.choice("?!.")

        # Filter out names in channels
        for name in self.channels[e.target].users():
            filtered = name[0:int(len(name)/2)] + '_' + name[int(len(name)/2):]
            if name in text:
                text = text.replace(name, filtered)

        # Tag links just in case
        text = text.replace("http://", "[might be nsfw] http://").replace("https://", "[might be nsfw] https://")

        if len(text) > 510:
            text = text.substring(0, 510)
        c.privmsg(e.target, text)
        self.last_time = time.time()

def pick_seed(src, length):
    words = src.split()
    if len(words) < length:
        return None
    i = random.randint(0, len(words) - length)
    return tuple(words[i:i+length])

def main():
    import sys
    if len(sys.argv) not in [5, 6]:
        print(sys.argv)
        print("Usage: {} <k> <server[:port]> <channel>[,<channel2>,...] <nickname> [<pass>]"
              .format(sys.argv[0]))
        sys.exit(1)

    k = int(sys.argv[1])
    srv = sys.argv[2].split(":", 1)
    host = srv[0]
    if len(srv) == 2:
        port = int(srv[1])
    else:
        port = 6667

    channels = sys.argv[3].split(",")
    nickname = sys.argv[4]
    password = None
    if len(sys.argv) == 6:
        password = sys.argv[5]

    with open("markovsrc.txt") as f:
        msrc = f.read().replace("\n", " ").split()
    markov = Markov(msrc, k=k)
    bot = MarkovBot(markov, channels, nickname, host, port, password)

    import signal
    def sigint(signal, frame):
        print("Caught SIGINT, terminating")
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint)

    bot.start()

if __name__ == "__main__":
    main()
