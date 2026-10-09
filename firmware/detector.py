IDLE = "idle"
OCCUPIED = "occupied"
LEAVING = "leaving"
FLUSHING = "flushing"


def remain_s(remain_ms):
    if remain_ms <= 0:
        return 0.0
    return ((remain_ms + 99) // 100) / 10.0


class Detector:
    def __init__(self, cfg):
        self.cfg = cfg
        self.state = IDLE
        self._leave_start_ms = None
        self._occupied_start_ms = None
        self._hold_start_ms = None

    def _hold_ms(self):
        mode = str(self.cfg.get("trigger_mode") or "hold")
        if mode == "instant":
            return 0
        return int(float(self.cfg.get("trigger_hold_s") or 1) * 1000)

    def _occupy_if_ready(self, present, now_ms):
        if not present:
            self._hold_start_ms = None
            return False
        hold_ms = self._hold_ms()
        if hold_ms <= 0:
            self._enter_occupied(now_ms)
            return True
        if self._hold_start_ms is None:
            self._hold_start_ms = now_ms
            return False
        if now_ms - self._hold_start_ms >= hold_ms:
            self._enter_occupied(now_ms)
            return True
        return False

    def _enter_occupied(self, now_ms):
        self.state = OCCUPIED
        self._leave_start_ms = None
        self._hold_start_ms = None
        self._occupied_start_ms = now_ms

    def tick(self, present, now_ms):
        if self.state == FLUSHING:
            return None

        if self.state == IDLE:
            self._occupy_if_ready(present, now_ms)
            return None

        if self.state == OCCUPIED:
            if present:
                return None
            self.state = LEAVING
            self._leave_start_ms = now_ms
            self._hold_start_ms = None
            return None

        if self.state == LEAVING:
            if present:
                self._enter_occupied(now_ms)
                return None
            leave_ms = int(float(self.cfg["leave_delay_s"]) * 1000)
            if now_ms - self._leave_start_ms >= leave_ms:
                self.state = FLUSHING
                self._hold_start_ms = None
                return "start_flush"
            return None

        return None

    def leave_remain_s(self, now_ms):
        if self.state != LEAVING or self._leave_start_ms is None:
            return 0
        leave_ms = int(float(self.cfg["leave_delay_s"]) * 1000)
        remain_ms = leave_ms - (now_ms - self._leave_start_ms)
        return remain_s(remain_ms)

    def hold_remain_s(self, now_ms):
        hold_ms = self._hold_ms()
        if hold_ms <= 0 or self._hold_start_ms is None:
            return 0
        if self.state not in (IDLE,):
            return 0
        remain_ms = hold_ms - (now_ms - self._hold_start_ms)
        return remain_s(remain_ms)

    def occupied_elapsed_s(self, now_ms):
        if self.state != OCCUPIED or self._occupied_start_ms is None:
            return 0
        elapsed = now_ms - self._occupied_start_ms
        if elapsed < 0:
            return 0
        return elapsed // 1000

    def end_flush(self, now_ms=0):
        self.state = IDLE
        self._leave_start_ms = None
        self._occupied_start_ms = None
        self._hold_start_ms = None
