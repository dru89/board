#!/usr/bin/env python3
"""Minimal Home Assistant websocket helper for dev automation.

Usage: HA_TOKEN=... HA_HOST=orinoco:8123 python3 ha_ws.py commands.json
where commands.json is a JSON array of websocket command objects
(without ids — they're assigned sequentially). Results print as JSON lines.
"""
import json
import os
import sys

import websocket

TOKEN = os.environ["HA_TOKEN"]
URL = f"ws://{os.environ.get('HA_HOST', 'orinoco:8123')}/api/websocket"


def main():
    ws = websocket.create_connection(URL, timeout=15)
    assert json.loads(ws.recv())["type"] == "auth_required"
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    assert json.loads(ws.recv())["type"] == "auth_ok"

    cmds = json.load(open(sys.argv[1]))
    mid = 1
    for cmd in cmds:
        cmd["id"] = mid
        ws.send(json.dumps(cmd))
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == mid and resp.get("type") == "result":
                print(json.dumps({"cmd": cmd.get("type"), "success": resp["success"],
                                  "result": resp.get("result"), "error": resp.get("error")}))
                break
        mid += 1
    ws.close()


if __name__ == "__main__":
    main()
