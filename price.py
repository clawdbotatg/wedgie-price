# ETH Price: the price from wedgie.dev, checked on the wedgie, so the computer can't fake it.
# A: the wedgie makes a random nonce and asks the computer ({"type": "price_ask", "nonce"}). The computer
# (relay.py, or any page) gets https://wedgie.dev/api/price?nonce=... and sends the answer back as one
# line ({"type": "price", ...}). The wedgie checks wedgie.dev's signature (KEY) and its own nonce: a
# computer can block the answer, but a changed or old one says so in red.
import sys, os, select, json, time, gc, binascii, hashlib
import lcd as L
import wedgie as W
import ui
from ui import INK, MUTED, GREEN_D, RED

# The public half of wedgie.dev's PRICE_KEY (api/price.ts).
KEY = (0xd7909a464f1dd7cce5a5309780bc15a6ba9c6da66d439ecd0bc1179d7ae81af2,
       0x21943b1c7a934405adf8f053144258a00e28b08a7b499c9a15aa8ac3152daeda)
WAIT_MS = 15000

d = keys = _poll = None
nonce = None            # the question out, while waiting
asked = 0
head, lines = "ETH price", [("Press A to ask", INK), ("wedgie.dev, through", MUTED), ("this computer.", MUTED)]


def money(p):
    """"2422.7" -> "$2,422.70"."""
    a, _, b = p.partition(".")
    s = ""
    while len(a) > 3:
        s, a = "," + a[-3:] + s, a[:-3]
    return "$" + a + s + "." + (b + "00")[:2]


def ok(m):
    """True if wedgie.dev signed this answer to our question."""
    if m.get("nonce") != nonce:
        return False
    try:
        import p256
        text = "wedgie.dev price\n%s\n%s\n%s\n%d" % (nonce, m["pair"], m["price"], int(m["t"]))
        return p256.verify(KEY[0], KEY[1], hashlib.sha256(text.encode()).digest(), int(m["r"], 16), int(m["s"], 16))
    except Exception as e:
        sys.print_exception(e)
        return False
    finally:
        sys.modules.pop("p256", None)
        gc.collect()


def on_price(m):
    global nonce, head, lines
    ui.progress("ETH price", "checking the signature", bar=False)
    good = ok(m)
    nonce = None
    W.send({"type": "price_checked", "ok": good})    # for the computer to say so; the screen is what counts
    if good:
        head = money(m["price"])
        lines = [("ETH in USD", INK), ("signed by wedgie.dev", GREEN_D)]
    else:
        head = "Not trusted"
        lines = [("The answer wasn't signed", RED), ("by wedgie.dev, or it", RED), ("was old. Ignored.", RED)]


def ask():
    global nonce, asked, head, lines
    nonce = binascii.hexlify(os.urandom(16)).decode()
    asked = time.ticks_ms()
    W.send({"type": "price_ask", "nonce": nonce, "url": "https://wedgie.dev/api/price?nonce=" + nonce})
    head, lines = "Asking...", [("waiting for the", MUTED), ("computer to pass it on", MUTED)]


def pump():
    """One line from USB per call, through the one line reader (wedgie.lines)."""
    R = W.lines()
    line = R.pump(_poll)
    if R.intr:                          # a Ctrl-C while sealed: the red question (hatch.py)
        R.intr = False
        if W.SEALED and not W.is_open():
            import hatch
            if hatch.ctrl_c():
                raise KeyboardInterrupt
            return True
    if not line or not line.strip():
        return False
    try:
        m = json.loads(line)
    except Exception:
        return False
    if not isinstance(m, dict):
        return False
    try:
        if m.get("type") == "price":
            if nonce:
                on_price(m)
        elif m.get("type") == "hello":
            W.send(W.hello(m.get("id"), running="price"))
        else:                           # shots, jobs, open: the slot's
            import slot
            slot.handle(m)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        W.failed(m.get("id"), e)
    return True


def run():
    global d, keys, _poll, nonce, head, lines
    d = L.LCD()
    keys = L.Keys(physical=True)
    _poll = select.poll()
    _poll.register(sys.stdin, select.POLLIN)
    W.send(W.hello(None, type="ready", running="price"))
    dirty = True
    while True:
        for k in keys.pressed():
            if k == "A" and not nonce:
                ask()
                dirty = True
        if pump():
            dirty = True
        if nonce and time.ticks_diff(time.ticks_ms(), asked) > WAIT_MS:
            nonce = None
            head, lines = "No answer", [("The computer didn't", RED), ("pass it on.", RED), ("A: try again", MUTED)]
            dirty = True
        if dirty:
            ui.page(d, head, lines, "A: get the price")
            dirty = False
        time.sleep_ms(20)
