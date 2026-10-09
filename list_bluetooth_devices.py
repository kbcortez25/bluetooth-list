#!/usr/bin/env python3
"""List nearby Bluetooth Low Energy devices.

Requires:
    pip install bleak
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceResult:
    name: str
    address: str
    rssi: Optional[int]


async def scan_devices(timeout: float) -> list[DeviceResult]:
    try:
        from bleak import BleakScanner
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: bleak\n"
            "Install it with: python3 -m pip install bleak"
        ) from exc

    devices = await BleakScanner.discover(timeout=timeout)
    results: list[DeviceResult] = []
    for device in devices:
        results.append(
            DeviceResult(
                name=device.name or "(unknown)",
                address=device.address,
                rssi=getattr(device, "rssi", None),
            )
        )
    return results


async def pair_device(address: str) -> None:
    try:
        from bleak import BleakClient
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: bleak\n"
            "Install it with: python3 -m pip install bleak"
        ) from exc

    client = BleakClient(address)
    try:
        paired = await client.pair()
        if not paired:
            raise RuntimeError("The Bluetooth adapter did not confirm pairing.")
    finally:
        if client.is_connected:
            await client.disconnect()


def format_rssi(rssi: Optional[int]) -> str:
    return f"{rssi:>4}" if rssi is not None else "   ?"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan for nearby Bluetooth Low Energy devices."
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=5.0,
        help="Scan duration in seconds (default: 5.0).",
    )
    parser.add_argument(
        "--pair",
        metavar="ADDRESS",
        help="Pair with a device after scanning (use its Bluetooth address).",
    )
    args = parser.parse_args()

    try:
        devices = asyncio.run(scan_devices(args.timeout))
    except KeyboardInterrupt:
        return 130

    if not devices and not args.pair:
        print("No nearby Bluetooth Low Energy devices found.")
        return 0

    if devices:
        print(f"{'RSSI':>5}  {'Address':<20}  Name")
        print(f"{'-' * 5}  {'-' * 20}  {'-' * 32}")
        for device in devices:
            print(f"{format_rssi(device.rssi)}  {device.address:<20}  {device.name}")

    if args.pair:
        try:
            asyncio.run(pair_device(args.pair))
        except (Exception, KeyboardInterrupt) as exc:
            print(f"Could not pair with {args.pair}: {exc}", file=sys.stderr)
            return 1
        print(f"Paired with {args.pair}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
