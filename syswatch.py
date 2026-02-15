#!/usr/bin/env python3

import argparse
import psutil
import re
import sys

# ---------------------------
# EXIT CODES
# ---------------------------
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


# ---------------------------
# VALIDATE INCLUDE ARG USING REGEX
# allowed:
# cpu
# mem
# cpu,mem
# mem,cpu
# reject duplicates & spaces
# ---------------------------
def validate_include(value: str):
    pattern = r"^(cpu|mem)(,(cpu|mem))?$"

    if not re.fullmatch(pattern, value):
        raise argparse.ArgumentTypeError(
            "Invalid --include. Use cpu | mem | cpu,mem | mem,cpu (no spaces)"
        )

    parts = value.split(",")

    # Reject duplicates like cpu,cpu
    if len(parts) != len(set(parts)):
        raise argparse.ArgumentTypeError("Duplicate metrics not allowed")

    return parts


# ---------------------------
# CHECK STATUS HELPER
# ---------------------------
def evaluate(value, warn, crit):
    if value >= crit:
        return CRITICAL
    elif value >= warn:
        return WARNING
    return OK


# ---------------------------
# MAIN
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description="Simple system monitoring check")

    parser.add_argument("--cpu-warn", type=float, default=80)
    parser.add_argument("--cpu-crit", type=float, default=90)

    parser.add_argument("--mem-warn", type=float, default=80)
    parser.add_argument("--mem-crit", type=float, default=90)

    parser.add_argument(
        "--include",
        type=validate_include,
        default=["cpu", "mem"],
        help="cpu | mem | cpu,mem | mem,cpu"
    )

    args = parser.parse_args()

    try:
        results = []
        statuses = []

        # ---------------- CPU ----------------
        if "cpu" in args.include:
            cpu = psutil.cpu_percent(interval=1)
            results.append(f"cpu={cpu:.1f}%")
            statuses.append(evaluate(cpu, args.cpu_warn, args.cpu_crit))

        # ---------------- MEMORY ----------------
        if "mem" in args.include:
            mem = psutil.virtual_memory().percent
            results.append(f"mem={mem:.1f}%")
            statuses.append(evaluate(mem, args.mem_warn, args.mem_crit))

        # ---------------- FINAL STATUS ----------------
        if CRITICAL in statuses:
            state = "CRITICAL"
            code = CRITICAL
        elif WARNING in statuses:
            state = "WARNING"
            code = WARNING
        else:
            state = "OK"
            code = OK

        # single line output
        print(f"{state} " + " ".join(results))
        sys.exit(code)

    except Exception as e:
        print(f"UNKNOWN error={e}")
        sys.exit(UNKNOWN)


if __name__ == "__main__":
    main()
