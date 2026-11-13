#!/usr/bin/env python3
"""TCP↔serial bridge helpers for Dev-Host → cede-gateway instrument ports.

SDL owns the bridge; spectrometer-lab / CEDE stay untouched. The remote side
opens the by-id node only while a client is connected.
"""

from __future__ import annotations

import argparse
import os
import select
import socket
import sys
import threading
import time
from typing import Optional


def _serve_serial(*, listen_host: str, listen_port: int, serial_port: str, baud: int) -> int:
    import serial

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((listen_host, listen_port))
    srv.listen(1)
    print(f"listening {listen_host}:{listen_port} → {serial_port}@{baud}", flush=True)
    while True:
        conn, addr = srv.accept()
        print(f"client {addr}", flush=True)
        ser = serial.Serial(
            port=serial_port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.05,
            write_timeout=2.0,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
            exclusive=True,
        )
        try:
            ser.reset_input_buffer()
            conn.setblocking(False)
            while True:
                r, _, _ = select.select([conn, ser], [], [], 1.0)
                if conn in r:
                    data = conn.recv(4096)
                    if not data:
                        break
                    ser.write(data)
                    ser.flush()
                if ser in r:
                    data = ser.read(ser.in_waiting or 1)
                    if data:
                        conn.sendall(data)
        finally:
            try:
                ser.close()
            except Exception:  # noqa: BLE001
                pass
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
            print("client closed; serial released", flush=True)


def _pty_client(*, host: str, port: int, link_path: str) -> int:
    import pty

    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)
    try:
        if os.path.islink(link_path) or os.path.exists(link_path):
            os.unlink(link_path)
    except FileNotFoundError:
        pass
    os.symlink(slave_name, link_path)
    print(f"pty={slave_name} link={link_path} → {host}:{port}", flush=True)

    sock = socket.create_connection((host, port), timeout=10.0)
    sock.setblocking(False)
    os.set_blocking(master, False)
    try:
        while True:
            r, _, _ = select.select([master, sock], [], [], 1.0)
            if master in r:
                data = os.read(master, 4096)
                if not data:
                    break
                sock.sendall(data)
            if sock in r:
                data = sock.recv(4096)
                if not data:
                    break
                os.write(master, data)
    finally:
        try:
            sock.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            os.close(master)
        except Exception:  # noqa: BLE001
            pass
        try:
            os.close(slave)
        except Exception:  # noqa: BLE001
            pass
        try:
            if os.path.islink(link_path):
                os.unlink(link_path)
        except FileNotFoundError:
            pass
    return 0


def _probe_es(*, port: str, baud: int, timeout_s: float) -> int:
    """Minimal $ES query using pyserial only (no spectrometer-lab import)."""
    import serial

    ser = serial.Serial(
        port=port,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.05,
        write_timeout=2.0,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
        exclusive=True,
    )
    try:
        ser.reset_input_buffer()
        ser.write(b"$ES\r")
        ser.flush()
        deadline = time.monotonic() + timeout_s
        buf = b""
        while time.monotonic() < deadline:
            chunk = ser.read(256)
            if chunk:
                buf += chunk
                # Prompted mode: status, DEL payload, status.
                if buf.count(b"\r\n") >= 3 or (b"\x7f" in buf and buf.count(b"\r\n") >= 2):
                    break
            else:
                time.sleep(0.02)
    finally:
        ser.close()

    text = buf.decode("latin1", errors="replace")
    print(f"raw={buf!r}", flush=True)
    # Look for DEL-prefixed '0' or '1'
    es: Optional[str] = None
    for line in text.splitlines():
        if "\x7f" in line:
            payload = line.split("\x7f", 1)[-1].strip()
            if payload in {"0", "1"}:
                es = payload
    if es is None:
        print("FAIL: no $ES readback", flush=True)
        return 1
    print(f"ES={es}", flush=True)
    if es != "1":
        print("FAIL: Xe not OFF", flush=True)
        return 1
    print("PASS: Xe OFF", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="Run on gateway: TCP → serial")
    serve.add_argument("--listen", default="127.0.0.1")
    serve.add_argument("--tcp-port", type=int, default=29700)
    serve.add_argument("--serial-port", required=True)
    serve.add_argument("--baud", type=int, default=9600)

    client = sub.add_parser("pty", help="Run on Dev-Host: local PTY → remote TCP")
    client.add_argument("--host", default="127.0.0.1")
    client.add_argument("--tcp-port", type=int, default=29700)
    client.add_argument(
        "--link",
        default="/tmp/ls55-bridge",
        help="Symlink path for acquisition scripts (--port)",
    )

    probe = sub.add_parser("probe-es", help="Query $ES; require readback 1 (OFF)")
    probe.add_argument("--port", required=True)
    probe.add_argument("--baud", type=int, default=9600)
    probe.add_argument("--timeout", type=float, default=5.0)

    args = parser.parse_args(argv)
    if args.cmd == "serve":
        return _serve_serial(
            listen_host=args.listen,
            listen_port=args.tcp_port,
            serial_port=args.serial_port,
            baud=args.baud,
        )
    if args.cmd == "pty":
        return _pty_client(host=args.host, port=args.tcp_port, link_path=args.link)
    if args.cmd == "probe-es":
        return _probe_es(port=args.port, baud=args.baud, timeout_s=args.timeout)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
