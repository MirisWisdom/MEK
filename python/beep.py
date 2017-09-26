def beep(interval=0, count=1):
    """
    Makes the computer beep by printing the bell character.
    Wont work outside of printing to a system terminal.
    """
    if "sleep" not in globals():
        from time import sleep

    try:
        for i in range(max(1, int(count))):
            print(b"\x07".decode("ascii"))
            if interval <= 0:
                return
            sleep(float(interval))
    except KeyboardInterrupt:
        pass
