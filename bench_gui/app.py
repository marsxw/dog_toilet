"""
舵机冲水 / 粉碎电机 / 电流 调试界面（Windows）。

  cd bench_gui
  python -m venv ..\\venv
  ..\\venv\\Scripts\\activate
  pip install -r requirements.txt
  python app.py

设备端：上传 firmware 后，在板子 config.json 里设 "bench_mode": true 并复位；
或单独运行 firmware/bench.py。串口 115200。
"""

import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import serial
import serial.tools.list_ports


BAUD = 115200


class SerialBench:
    def __init__(self):
        self._ser = None
        self._lock = threading.Lock()

    @property
    def connected(self):
        return self._ser is not None and self._ser.is_open

    def open(self, port):
        self.close()
        self._ser = serial.Serial(port, BAUD, timeout=0.2)
        # 避免 DTR/RTS 拉低 EN/GPIO0 导致反复复位
        self._ser.dtr = False
        self._ser.rts = False
        time.sleep(0.15)
        self._drain(1.5)
        if not self._wait_pong(retries=12):
            self.close()
            raise RuntimeError(
                "设备无响应。请确认：\n"
                "1) 已上传最新 firmware（含 bench.py、main.py）；\n"
                "2) 板子 config.json 含 \"bench_mode\": true 后复位，或运行 bench.py；\n"
                "3) 串口未被 Thonny/串口监视器占用。"
            )

    def close(self):
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except serial.SerialException:
                pass
        self._ser = None

    def _drain(self, seconds):
        if not self.connected:
            return
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            waiting = self._ser.in_waiting
            if waiting:
                self._ser.read(waiting)
            else:
                time.sleep(0.05)

    def _read_line(self, timeout_s=1.0):
        end = time.monotonic() + timeout_s
        buf = b""
        while time.monotonic() < end:
            chunk = self._ser.read(max(1, self._ser.in_waiting))
            if chunk:
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    text = line.decode("utf-8", errors="replace").strip()
                    if text:
                        return text
            else:
                time.sleep(0.02)
        return ""

    def _wait_pong(self, retries=8):
        for _ in range(retries):
            with self._lock:
                self._ser.write(b"PING\n")
                self._ser.flush()
            line = self._read_line(0.8)
            if line == "PONG" or line.endswith("PONG"):
                return True
            time.sleep(0.25)
        return False

    def command(self, cmd):
        with self._lock:
            if not self.connected:
                raise RuntimeError("未连接串口")
            self._ser.write((cmd.strip() + "\n").encode("utf-8"))
            self._ser.flush()
        line = self._read_line(1.2)
        if not line:
            raise RuntimeError("串口超时")
        if line.startswith("ERR "):
            raise RuntimeError(line[4:])
        return line


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("狗厕所 PCB 电机调试")
        self.minsize(440, 520)
        self.bench = SerialBench()
        self._crush_on = False
        self._poll_job = None

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        row0 = ttk.Frame(frm)
        row0.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(row0, text="串口").pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(row0, textvariable=self.port_var, width=18, state="readonly")
        self.port_combo.pack(side=tk.LEFT, padx=6)
        ttk.Button(row0, text="刷新", command=self.refresh_ports).pack(side=tk.LEFT)
        ttk.Button(row0, text="连接", command=self.connect).pack(side=tk.LEFT, padx=4)
        ttk.Button(row0, text="断开", command=self.disconnect).pack(side=tk.LEFT)

        self.conn_label = ttk.Label(frm, text="未连接", foreground="#888")
        self.conn_label.pack(anchor=tk.W)

        ir_fr = ttk.LabelFrame(frm, text="红外输入 (GPIO1 数字)", padding=8)
        ir_fr.pack(fill=tk.X, pady=8)
        self.ir_label = ttk.Label(ir_fr, text="—", wraplength=380)
        self.ir_label.pack(anchor=tk.W)
        ttk.Label(
            ir_fr,
            text="固定读 GPIO1。遮住应为 raw=0、present=1；移开应为 raw=1、present=0。",
            wraplength=380,
            foreground="#555",
        ).pack(anchor=tk.W, pady=(4, 0))

        servo_fr = ttk.LabelFrame(frm, text="冲水舵机 (GPIO13)", padding=8)
        servo_fr.pack(fill=tk.X, pady=8)
        self.servo_var = tk.DoubleVar(value=20.0)
        ttk.Label(servo_fr, text="角度 °").grid(row=0, column=0, sticky=tk.W)
        self.servo_scale = ttk.Scale(
            servo_fr,
            from_=0,
            to=180,
            variable=self.servo_var,
            orient=tk.HORIZONTAL,
            command=self._on_servo_slide,
        )
        self.servo_scale.grid(row=0, column=1, sticky=tk.EW, padx=8)
        servo_fr.columnconfigure(1, weight=1)
        self.servo_entry = ttk.Entry(servo_fr, width=8)
        self.servo_entry.insert(0, "20.0")
        self.servo_entry.grid(row=0, column=2)
        ttk.Button(servo_fr, text="应用", command=self.apply_servo).grid(row=0, column=3, padx=4)
        servo_btns = ttk.Frame(servo_fr)
        servo_btns.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(8, 0))
        ttk.Button(servo_btns, text="冲水 PRESS", command=lambda: self.send_simple("PRESS")).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(servo_btns, text="回位 RELEASE", command=lambda: self.send_simple("RELEASE")).pack(
            side=tk.LEFT, padx=4
        )
        self.servo_reply = ttk.Label(servo_fr, text="默认回位 20°、冲水 90°，可在 firmware/servo_ctrl.py 改。", foreground="#006")
        self.servo_reply.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(6, 0))

        crush_fr = ttk.LabelFrame(frm, text="粉碎电机 (GPIO11 IN1 / GPIO12 IN2)", padding=8)
        crush_fr.pack(fill=tk.X, pady=8)
        bf = ttk.Frame(crush_fr)
        bf.pack(anchor=tk.W)
        self.crush_btn = ttk.Button(bf, text="粉碎：关", command=self.toggle_crush)
        self.crush_btn.pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="正转 FWD", command=lambda: self._crush_dir("FWD")).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="反转 REV", command=lambda: self._crush_dir("REV")).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="停止 STOP", command=lambda: self._crush_dir("STOP")).pack(side=tk.LEFT, padx=4)

        i_fr = ttk.LabelFrame(frm, text="电机电流 (GPIO3 ADC，0.1Ω × 10.5)", padding=8)
        i_fr.pack(fill=tk.X, pady=8)
        self.i_label = ttk.Label(i_fr, text="—", wraplength=400)
        self.i_label.pack(anchor=tk.W)
        ttk.Label(
            i_fr,
            text="I = Vadc / 1.05。超过 4A 会自动停粉碎电机。读数已做均值+滤波。",
            wraplength=400,
            foreground="#555",
        ).pack(anchor=tk.W, pady=(4, 0))

        note = ttk.Label(
            frm,
            text="测好舵机角度后，把 firmware/servo_ctrl.py 里的 RELEASE_DEG / PRESS_DEG 改成你的值。",
            wraplength=420,
        )
        note.pack(anchor=tk.W, pady=(12, 0))

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh_ports()

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])

    def connect(self):
        port = self.port_var.get()
        if not port:
            messagebox.showwarning("串口", "请选择串口")
            return
        try:
            self.bench.open(port)
        except Exception as exc:
            messagebox.showerror("连接失败", str(exc))
            return
        self.conn_label.config(text="已连接 " + port, foreground="#080")
        self._start_poll()

    def disconnect(self):
        self._stop_poll()
        if self._crush_on:
            try:
                self.bench.command("STOP")
            except RuntimeError:
                pass
            self._set_crush_ui(False)
        try:
            if self.bench.connected:
                self.bench.command("RELEASE")
        except RuntimeError:
            pass
        self.bench.close()
        self.conn_label.config(text="未连接", foreground="#888")
        self.ir_label.config(text="—")
        self.i_label.config(text="—")

    def _start_poll(self):
        self._poll_ir()

    def _stop_poll(self):
        if self._poll_job:
            self.after_cancel(self._poll_job)
            self._poll_job = None

    def _poll_ir(self):
        if not self.bench.connected:
            return
        try:
            line = self.bench.command("IR")
            self.ir_label.config(text=line)
        except RuntimeError:
            pass
        try:
            i_line = self.bench.command("I")
            self.i_label.config(text=i_line)
            if "TRIP" in i_line:
                self._set_crush_ui(False)
        except RuntimeError:
            pass
        self._poll_job = self.after(300, self._poll_ir)

    def _on_servo_slide(self, _value):
        deg = float(self.servo_var.get())
        self.servo_entry.delete(0, tk.END)
        self.servo_entry.insert(0, f"{deg:.1f}")

    def apply_servo(self):
        try:
            deg = float(self.servo_entry.get())
        except ValueError:
            messagebox.showwarning("舵机", "请输入数字")
            return
        deg = max(0.0, min(180.0, deg))
        self.servo_var.set(deg)
        if not self.bench.connected:
            messagebox.showinfo("舵机", f"未连接，本地记录角度 {deg:.1f}°")
            return
        try:
            reply = self.bench.command(f"SERVO {deg:.2f}")
            self.servo_reply.config(text=reply)
        except Exception as exc:
            messagebox.showerror("舵机", str(exc))

    def send_simple(self, cmd):
        if not self.bench.connected:
            messagebox.showwarning("电机", "请先连接串口")
            return
        try:
            reply = self.bench.command(cmd)
        except Exception as exc:
            messagebox.showerror(cmd, str(exc))
            return
        if cmd in ("PRESS", "RELEASE"):
            self.servo_reply.config(text=reply)

    def _set_crush_ui(self, on):
        self._crush_on = bool(on)
        self.crush_btn.config(text="粉碎：开" if self._crush_on else "粉碎：关")

    def _crush_dir(self, cmd):
        if not self.bench.connected:
            messagebox.showwarning("粉碎", "请先连接串口")
            return
        try:
            reply = self.bench.command(cmd)
        except Exception as exc:
            messagebox.showerror(cmd, str(exc))
            return
        if cmd == "STOP" or str(reply).startswith("TRIP"):
            self._set_crush_ui(False)
        else:
            self._set_crush_ui(True)

    def toggle_crush(self):
        if not self.bench.connected:
            messagebox.showwarning("粉碎", "请先连接串口")
            return
        want_on = not self._crush_on
        cmd = "CRUSH 1" if want_on else "CRUSH 0"
        try:
            reply = self.bench.command(cmd)
        except Exception as exc:
            messagebox.showerror("粉碎", str(exc))
            return
        if str(reply).startswith("TRIP"):
            self._set_crush_ui(False)
            messagebox.showwarning("过流", reply)
            return
        self._set_crush_ui(want_on)

    def on_close(self):
        self.disconnect()
        self.destroy()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
