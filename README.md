# ETH Price

A [wedgie](https://wedgie.dev) app that shows the ETH price, and doesn't trust the computer it's plugged into.

1. Press **A**. The wedgie makes a random nonce and asks the computer to fetch
   `https://wedgie.dev/api/price?nonce=...`.
2. wedgie.dev signs the price, the time and that nonce with its price key.
3. The computer passes the answer back. The wedgie checks the signature (the key is pinned in `price.py`)
   and the nonce, then shows the price.

A computer can block the answer, but a changed one or an old one says **Not trusted**.

The computer's side: `python3 relay.py` (needs pyserial). `python3 relay.py --evil` changes the price on
the way, to watch the wedgie refuse it. Close the wedgie's page first: one program per USB port.

Install: `python3 wedgie.py install .` (https://wedgie.dev/wedgie.py).

Controls: A asks. No saves. MIT.
