import time
import pigpio

FILE = "codes"
GPIO = 18
GLITCH = 100
PRE_US = 200 * 1000
POST_MS = 130
POST_US = POST_MS * 1000
SHORT = 10
TOLERANCE = 15
TOLER_MIN = (100 - TOLERANCE) / 100.0
TOLER_MAX = (100 + TOLERANCE) / 100.0
FREQ = 38.0
GAP_S = 100 / 1000.0


last_tick = 0
fetching_code = False
in_code = False
pi = pigpio.pi()
code = []


def carrier(gpio, frequency, micros):
    """
    Generate carrier square wave.
    """
    wf = []
    cycle = 1000.0 / frequency
    cycles = int(round(micros / cycle))
    on = int(round(cycle / 2.0))
    sofar = 0
    for c in range(cycles):
        target = int(round((c + 1) * cycle))
        sofar += on
        off = target - sofar
        sofar += off
        wf.append(pigpio.pulse(1 << gpio, 0, on))
        wf.append(pigpio.pulse(0, 1 << gpio, off))
    return wf


def reset():
    global last_tick, in_code, code, fetching_code, pi
    last_tick = 0
    fetching_code = False
    in_code = False
    pi = pigpio.pi()
    code = []


def normalise(c):
    entries = len(c)
    p = [0] * entries  # Set all entries not processed.
    for i in range(entries):
        if not p[i]:  # Not processed?
            v = c[i]
            tot = v
            similar = 1.0

            # Find all pulses with similar lengths to the start pulse.
            for j in range(i + 2, entries, 2):
                if not p[j]:  # Unprocessed.
                    if (c[j] * TOLER_MIN) < v < (c[j] * TOLER_MAX):  # Similar.
                        tot = tot + c[j]
                        similar += 1.0

            # Calculate the average pulse length.
            newv = round(tot / similar, 2)
            c[i] = newv

            # Set all similar pulses to the average value.
            for j in range(i + 2, entries, 2):
                if not p[j]:  # Unprocessed.
                    if (c[j] * TOLER_MIN) < v < (c[j] * TOLER_MAX):  # Similar.
                        c[j] = newv
                        p[j] = 1


def end_of_code():
    global code, fetching_code
    if len(code) > SHORT:
        normalise(code)
        fetching_code = False
    else:
        code = []
        print("Short code, probably a repeat, try again")


def cbf(gpio, level, tick):

    global last_tick, in_code, code, fetching_code

    if level != pigpio.TIMEOUT:

        edge = pigpio.tickDiff(last_tick, tick)
        last_tick = tick

        if fetching_code:
            if (edge > PRE_US) and (not in_code):  # Start of a code.
                in_code = True
                pi.set_watchdog(GPIO, POST_MS)  # Start watchdog.

            elif (edge > POST_US) and in_code:  # End of a code.
                in_code = False
                pi.set_watchdog(GPIO, 0)  # Cancel watchdog.
                end_of_code()

            elif in_code:
                code.append(edge)

    else:
        pi.set_watchdog(GPIO, 0)  # Cancel watchdog.
        if in_code:
            in_code = False
            end_of_code()


def tidy_mark_space(records, base):

    ms = {}

    # Find all the unique marks (base=0) or spaces (base=1)
    # and count the number of times they appear,

    for rec in records:
        rl = len(records[rec])
        for i in range(base, rl, 2):
            if records[rec][i] in ms:
                ms[records[rec][i]] += 1
            else:
                ms[records[rec][i]] = 1

    v = None

    for plen in sorted(ms):

        if v is None:
            e = [plen]
            v = plen
            tot = plen * ms[plen]
            similar = ms[plen]

        elif plen < (v * TOLER_MAX):
            e.append(plen)
            tot += plen * ms[plen]
            similar += ms[plen]

        else:
            v = int(round(tot / float(similar)))
            # set all previous to v
            for i in e:
                ms[i] = v
            e = [plen]
            v = plen
            tot = plen * ms[plen]
            similar = ms[plen]

    v = int(round(tot / float(similar)))
    # set all previous to v
    for i in e:
        ms[i] = v

    for rec in records:
        rl = len(records[rec])
        for i in range(base, rl, 2):
            records[rec][i] = ms[records[rec][i]]


def tidy(records):

    tidy_mark_space(records, 0)  # Marks.

    tidy_mark_space(records, 1)  # Spaces.


def record(name):
    global code, fetching_code, GPIO
    GPIO = 18
    reset()
    records = {}

    pi.set_mode(GPIO, pigpio.INPUT)  # IR RX connected to this GPIO.

    pi.set_glitch_filter(GPIO, GLITCH)  # Ignore glitches.

    pi.callback(GPIO, pigpio.EITHER_EDGE, cbf)

    # Process each id

    print("Recording")
    for arg in name:
        print("Press key for '{}'".format(arg))
        code = []
        fetching_code = True
        startTime = time.time()
        while fetching_code:
            elapsed_time = time.time() - startTime
            if elapsed_time > 10:
                pi.set_glitch_filter(GPIO, 0)
                pi.set_watchdog(GPIO, 0)
                pi.stop()
                return False, []
            time.sleep(0.1)
        print("Okay")
        time.sleep(0.5)

        records[arg] = code[:]

    pi.set_glitch_filter(GPIO, 0)  # Cancel glitch filter.
    pi.set_watchdog(GPIO, 0)  # Cancel watchdog.
    pi.stop()
    tidy(records)
    return True, records[arg]


def play(code):
    GPIO = 17
    reset()
    pi.set_mode(GPIO, pigpio.OUTPUT)  # IR TX connected to this GPIO.

    pi.wave_add_new()

    emit_time = time.time()

    # Create wave

    marks_wid = {}
    spaces_wid = {}

    wave = [0] * len(code)

    for i in range(0, len(code)):
        ci = code[i]
        if i & 1:  # Space
            if ci not in spaces_wid:
                pi.wave_add_generic([pigpio.pulse(0, 0, ci)])
                spaces_wid[ci] = pi.wave_create()
            wave[i] = spaces_wid[ci]
        else:  # Mark
            if ci not in marks_wid:
                wf = carrier(GPIO, FREQ, ci)
                pi.wave_add_generic(wf)
                marks_wid[ci] = pi.wave_create()
            wave[i] = marks_wid[ci]

    delay = emit_time - time.time()

    if delay > 0.0:
        time.sleep(delay)

    pi.wave_chain(wave)

    while pi.wave_tx_busy():
        time.sleep(0.002)

    emit_time = time.time() + GAP_S

    for i in marks_wid:
        pi.wave_delete(marks_wid[i])

    marks_wid = {}

    for i in spaces_wid:
        pi.wave_delete(spaces_wid[i])

    spaces_wid = {}
    pi.stop()


if __name__ == "__main__":
    record(["temp"])
