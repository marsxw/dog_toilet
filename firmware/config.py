import json

CONFIG_PATH = "config.json"

DEFAULTS = {
    "leave_delay_s": 15,
    "trigger_mode": "hold",
    "trigger_hold_s": 1,
    "flush_count": 1,
    "flush_interval_s": 30,
    "wifi_timeout_s": 1800,
    "sample_ms": 50,
    "lang": "zh",
    "bench_mode": False,
}


def load_config(path=CONFIG_PATH):
    cfg = dict(DEFAULTS)
    try:
        with open(path, "r") as f:
            saved = json.loads(f.read())
        if isinstance(saved, dict):
            cfg.update(saved)
    except OSError:
        pass
    except ValueError:
        pass
    return sanitize(cfg)


def save_config(cfg, path=CONFIG_PATH):
    cfg = sanitize(cfg)
    with open(path, "w") as f:
        f.write(json.dumps(cfg))
    return cfg


def sanitize(cfg):
    out = dict(DEFAULTS)
    out.update(cfg or {})
    out["leave_delay_s"] = _clamp_num(out["leave_delay_s"], 0.1, 300, 15)
    mode = str(out.get("trigger_mode") or "hold").lower()
    out["trigger_mode"] = "instant" if mode == "instant" else "hold"
    out["trigger_hold_s"] = _clamp_num(out.get("trigger_hold_s", 1), 0.1, 30, 1)
    out["flush_count"] = int(_clamp_num(out["flush_count"], 1, 10, 1))
    out["flush_interval_s"] = _clamp_num(out["flush_interval_s"], 0.1, 300, 30)
    out.pop("wifi_password", None)
    out["wifi_timeout_s"] = int(_clamp_num(out["wifi_timeout_s"], 60, 86400, 1800))
    out["sample_ms"] = int(_clamp_num(out.get("sample_ms", 50), 20, 500, 50))
    lang = str(out.get("lang") or "zh").lower()
    out["lang"] = "en" if lang.startswith("en") else "zh"
    out["bench_mode"] = bool(out.get("bench_mode"))
    for key in (
        "threshold_cm",
        "confirm_window_s",
        "confirm_count",
        "cooldown_s",
        "servo_pin",
        "press_deg",
        "release_deg",
        "press_hold_s",
        "invalid_mm",
        "motor_run_s",
    ):
        out.pop(key, None)
    return out


def detector_cfg(cfg):
    return {
        "leave_delay_s": cfg["leave_delay_s"],
        "trigger_mode": cfg["trigger_mode"],
        "trigger_hold_s": cfg["trigger_hold_s"],
    }


def _clamp_num(value, lo, hi, default):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    if n < lo:
        return lo
    if n > hi:
        return hi
    return n
