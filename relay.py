#!/usr/bin/env python3
# The computer's side of ETH Price: pass the wedgie's question to wedgie.dev and the answer back.
# The wedgie trusts none of this: it checks wedgie.dev's signature itself.
#   python3 relay.py           # leave it running, press A on the wedgie
#   python3 relay.py --evil    # changes the price on the way: the wedgie should say "Not trusted"
# Needs pyserial (pip install pyserial). Close the wedgie's page first: one program per USB port.
import json, sys, time, urllib.request

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("relay.py needs pyserial:  pip install pyserial")

EVIL = "--evil" in sys.argv
SITE = "https://wedgie.dev"


def port():
    while True:
        p = [p.device for p in list_ports.comports() if p.vid == 0x2E8A]
        if p:
            return p[0]
        time.sleep(1)


def main():
    while True:
        dev = port()
        print("wedgie on", dev, "(evil)" if EVIL else "")
        try:
            s = serial.Serial(dev, 115200, timeout=0.1)
            buf = b""
            while True:
                buf += s.read(4096)
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    try:
                        m = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(m, dict) and m.get("type") == "price_checked":
                        print("wedgie:", "signed by wedgie.dev, shown" if m.get("ok") else "NOT trusted, ignored")
                    if not isinstance(m, dict) or m.get("type") != "price_ask":
                        continue
                    nonce = m.get("nonce", "")
                    try:
                        with urllib.request.urlopen(SITE + "/api/price?nonce=" + nonce, timeout=10) as r:
                            a = json.load(r)
                    except Exception as e:
                        print("wedgie.dev didn't answer:", e)
                        continue
                    if EVIL:
                        a["price"] = "99999.99"
                    print("price", a.get("price"), "-> wedgie")
                    s.write((json.dumps(dict(a, type="price")) + "\n").encode())
        except (serial.SerialException, OSError) as e:
            print("lost the wedgie:", e)
            time.sleep(1)


if __name__ == "__main__":
    main()
