import os


def killswitch_on():
    return (
        os.environ.get("KILL", "0") == "1"
        or open("/etc/agi/killswitch", "a+").read().strip() == "ON"
    )


def guard():
    if killswitch_on():
        raise SystemExit("Kill-switch engaged")
