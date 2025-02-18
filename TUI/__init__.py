"""Makes TUI into a package, so one can import subpackages"""

import warnings


__all__ = ['get_observatory']


warnings.filterwarnings('ignore', 'PyFITS is deprecated')


def get_observatory():
    """Return the observatory name."""

    # https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    import socket

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        return "unknown"

    if ip.startswith("10.8."):
        return "LCO"

    return "APO"
