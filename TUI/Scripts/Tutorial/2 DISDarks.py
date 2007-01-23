def run(sr):
    """Sample script to take a series of DIS darks
    and demonstrate using <inst>Expose to take exposures.
    The exposure times and  # of iterations are short so the demo runs quickly.
    """
    expType = "dark"
    expTime = 1  # in seconds
    numExp = 3

    yield sr.waitCmd(
        actor = "disExpose",
        cmdStr = "%s time=%s n=%d name=dis%s" % \
            (expType, expTime, numExp, expType),
        abortCmdStr = "abort",
    )
