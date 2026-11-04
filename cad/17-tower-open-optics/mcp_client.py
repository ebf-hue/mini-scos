import json
import os
import selectors
import shutil
import subprocess
import time
from contextlib import ExitStack
from pathlib import Path


class SolidCraft:
    def __init__(self):
        self._resources = ExitStack()
        self.err = self._resources.enter_context(
            open("/tmp/scos-solidcraft-server.log", "w")  # noqa: SIM115 - owned by ExitStack until close()
        )
        self.p = subprocess.Popen(
            [
                os.environ.get(
                    "SOLIDCRAFT_CLI",
                    shutil.which("solidcraft-cli")
                    or "/Applications/SolidCraft.app/Contents/MacOS/solidcraft-cli",
                ),
                "mcp",
                "--headless",
                "--allow-path",
                str(Path(__file__).resolve().parents[2]),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.err,
            text=True,
            bufsize=1,
        )
        self.id = 0
        self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mini-scos CAD", "version": "1"},
            },
        )
        self.p.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
        )
        self.p.stdin.flush()

    def request(self, method, params):
        self.id += 1
        i = self.id
        self.p.stdin.write(
            json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params})
            + "\n"
        )
        self.p.stdin.flush()
        sel = selectors.DefaultSelector()
        sel.register(self.p.stdout, selectors.EVENT_READ)
        end = time.monotonic() + 180
        while time.monotonic() < end:
            if not sel.select(end - time.monotonic()):
                break
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("SolidCraft server closed")
            out = json.loads(line)
            if out.get("id") == i:
                if "error" in out:
                    raise RuntimeError(out["error"])
                return out.get("result")
        raise TimeoutError(method)

    def call(self, tool_name, **args):
        return self.request("tools/call", {"name": tool_name, "arguments": args})

    def close(self):
        self.p.terminate()
        try:
            self.p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.p.kill()
        self._resources.close()
