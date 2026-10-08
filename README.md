# 狗厕所图纸 & 代码

模组：**ESP32-S3-WROOM-1-N16R8**（16MB Flash + 8MB Octal PSRAM；有时写作 N16S8，指同一类 8MB 外扩 RAM）。

## PC 虚拟环境

完整依赖与复现步骤见 **`environment.txt`**；一键安装：

```powershell
cd c:\Users\Siven\Desktop\dog_toilet
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 刷 MicroPython（COM3 示例）

须用 **SPIRAM_OCT** 固件，不要用不带 Octal PSRAM 的 `ESP32_GENERIC_S3-*.bin`（否则会报 `PSRAM chip is not connected`）。

```powershell
cd c:\Users\Siven\Desktop\dog_toilet
.\venv\Scripts\Activate.ps1
pip install esptool mpremote

python -m esptool --chip esp32s3 --port COM3 erase_flash
python -m esptool --chip esp32s3 --port COM3 --baud 460800 write_flash -z 0x0 `
  firmware\ESP32_GENERIC_S3-SPIRAM_OCT-20260824-v1.29.0.bin
```

## 上传 Python 到板子（COM3 示例）

先关掉 **bench_gui / Thonny** 等占用串口的程序。端口 `COM3` 按设备管理器修改。

```powershell
cd c:\Users\Siven\Desktop\dog_toilet\firmware
..\venv\Scripts\mpremote.exe connect COM3 soft-reset

..\venv\Scripts\mpremote.exe connect COM3 cp main.py :main.py
..\venv\Scripts\mpremote.exe connect COM3 cp bench.py :bench.py
..\venv\Scripts\mpremote.exe connect COM3 cp pins.py :pins.py
..\venv\Scripts\mpremote.exe connect COM3 cp motor.py :motor.py
..\venv\Scripts\mpremote.exe connect COM3 cp servo_ctrl.py :servo_ctrl.py
..\venv\Scripts\mpremote.exe connect COM3 cp config.py :config.py
..\venv\Scripts\mpremote.exe connect COM3 cp detector.py :detector.py
..\venv\Scripts\mpremote.exe connect COM3 cp web.py :web.py
..\venv\Scripts\mpremote.exe connect COM3 cp ir_input.py :ir_input.py

# 电机调试：用 bench 配置（含 "bench_mode": true）
..\venv\Scripts\mpremote.exe connect COM3 cp config.bench.json :config.json

# 正式自动冲水：去掉上一行，改传自己的 config.json，或删板子 config.json 用默认参数

..\venv\Scripts\mpremote.exe connect COM3 reset
```

若提示 `could not enter raw repl`，先 `soft-reset` 再 `cp`；若仍失败，按一下板子复位后重试。

## 电机调试界面

```powershell
.\venv\Scripts\Activate.ps1
python bench_gui\app.py
```

板子 `config.json` 中 `"bench_mode": true` 时为串口调试；测完改回 `false` 恢复自动冲水。
