#!/usr/bin/env python3
"""End-to-end delay test for every proxy in muse.yaml, run inside GitHub Actions.

Why: the Muse VM's egress is gateway-masked, so delay tests there cannot
distinguish live nodes from dead ones. A GitHub Actions runner has real
internet egress, so mihomo's /delay endpoint gives discriminative results.

Dead controls are always appended; if a control ever reports a delay the
whole run is marked invalid. This script never exits non-zero before writing
results/ -- the workflow publishes results/ even on failure so the failure
is diagnosable from the test-results branch.
"""
import json
import os
import subprocess
import sys
import time
import traceback
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

try:
    import yaml
except ImportError:
    yaml = None

ROOT = os.getcwd()
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)
DEBUG = []


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    DEBUG.append(line)
    print(line, flush=True)


API = "http://127.0.0.1:19090"
SECRET = "nt-secret"
TEST_URL = "http://www.gstatic.com/generate_204"

CONTROLS = [
    {"name": "CTRL-DEAD-UNROUTABLE", "type": "socks5",
     "server": "192.0.2.123", "port": 1080},
    {"name": "CTRL-DEAD-LOCAL", "type": "http",
     "server": "127.0.0.1", "port": 9},
]


def api_get(path, timeout=10):
    req = urllib.request.Request(API + path,
                                 headers={"Authorization": f"Bearer {SECRET}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def delay_once(name, timeout_ms):
    q = urllib.parse.quote(name, safe="")
    qs = urllib.parse.urlencode({"timeout": timeout_ms, "url": TEST_URL})
    try:
        data = api_get(f"/proxies/{q}/delay?{qs}",
                       timeout=timeout_ms / 1000 + 5)
        d = data.get("delay")
        return d if isinstance(d, int) and d > 0 else None
    except Exception:
        return None


def main():
    if yaml is None:
        raise RuntimeError("pyyaml missing")
    with open(os.path.join(ROOT, "muse.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    proxies = cfg.get("proxies") or []
    limit = int(os.environ.get("NODETEST_LIMIT", "0"))
    if limit > 0:
        proxies = proxies[:limit]
    names = [p["name"] for p in proxies]
    log(f"loaded {len(proxies)} proxies from muse.yaml (limit={limit})")

    all_proxies = proxies + CONTROLS
    test_cfg = {
        "mixed-port": 17890,
        "external-controller": "127.0.0.1:19090",
        "secret": SECRET,
        "mode": "rule",
        "log-level": "warning",
        "dns": {"enable": True, "ipv6": False,
                "nameserver": ["8.8.8.8", "1.1.1.1"]},
        "proxies": all_proxies,
        "proxy-groups": [{"name": "TEST", "type": "select",
                          "proxies": [p["name"] for p in all_proxies]}],
        "rules": ["MATCH,TEST"],
    }
    with open(os.path.join(ROOT, "test-config.yaml"), "w",
              encoding="utf-8") as f:
        yaml.safe_dump(test_cfg, f, allow_unicode=True)

    mihomo = os.path.join(ROOT, "mihomo")
    data_dir = os.path.join(ROOT, "mihomo-data")
    os.makedirs(data_dir, exist_ok=True)
    log_file = open(os.path.join(RESULTS, "mihomo.log"), "w")
    proc = subprocess.Popen([mihomo, "-f", "test-config.yaml", "-d", data_dir],
                            stdout=log_file, stderr=subprocess.STDOUT)
    try:
        up = False
        for _ in range(60):
            try:
                v = api_get("/version", timeout=3)
                log(f"mihomo up: {v}")
                up = True
                break
            except Exception:
                time.sleep(1)
        if not up:
            raise RuntimeError("mihomo API never came up")

        targets = names + [c["name"] for c in CONTROLS]
        alive = {}

        def check(name):
            d = delay_once(name, 5000)
            if d is None:
                d = delay_once(name, 6000)
            return name, d

        t0 = time.time()
        with ThreadPoolExecutor(max_workers=40) as ex:
            for name, d in ex.map(check, targets):
                if d is not None:
                    alive[name] = d
        elapsed = round(time.time() - t0, 1)
        log(f"delay sweep done in {elapsed}s: alive {len(alive)}/{len(targets)}")

        # second chance for everything that failed round 1
        failed = [n for n in targets if n not in alive]
        t0 = time.time()

        def retry(name):
            return name, delay_once(name, 7000)

        with ThreadPoolExecutor(max_workers=40) as ex:
            for name, d in ex.map(retry, failed):
                if d is not None:
                    alive[name] = d
        log(f"retry done in {round(time.time()-t0,1)}s: "
            f"failed was {len(failed)}, alive now {len(alive)}")

        controls_alive = {c["name"]: alive.get(c["name"]) for c in CONTROLS}
        valid = all(v is None for v in controls_alive.values())
        log(f"controls: {controls_alive} -> test valid: {valid}")

        alive_list = [{"name": n, "delay": alive[n]}
                      for n in names if n in alive]
        alive_list.sort(key=lambda x: x["delay"])
        summary = {
            "tested_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                           time.gmtime()),
            "total_tested": len(names),
            "alive": len(alive_list),
            "dead": len(names) - len(alive_list),
            "controls": controls_alive,
            "valid": valid,
            "test_url": TEST_URL,
            "note": "Egress: GitHub Actions runner (real internet). "
                    "Alive here means the node completed a real HTTP "
                    "request through the proxy; reachability from China "
                    "networks is not guaranteed by this test alone.",
        }
        with open(os.path.join(RESULTS, "summary.json"), "w",
                  encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=1)
        with open(os.path.join(RESULTS, "alive.json"), "w",
                  encoding="utf-8") as f:
            json.dump(alive_list, f, ensure_ascii=False, indent=1)
        with open(os.path.join(RESULTS, "alive-names.txt"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(x["name"] for x in alive_list) + "\n")
        log(f"summary: {summary}")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        log_file.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("FATAL:\n" + traceback.format_exc())
    finally:
        with open(os.path.join(RESULTS, "debug.log"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(DEBUG) + "\n")
    sys.exit(0)
