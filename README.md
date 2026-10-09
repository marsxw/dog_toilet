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
..\venv\Scripts\mpremote.exe connect COM3 cp test_web.py :test_web.py
..\venv\Scripts\mpremote.exe connect COM3 cp ir_input.py :ir_input.py

..\venv\Scripts\mpremote.exe connect COM3 reset
```

若提示 `could not enter raw repl`，先 `soft-reset` 再 `cp`；若仍失败，按一下板子复位后重试。

## 客户模式 / 工程师模式

上电、断电重启后**默认客户模式**（自动感应冲水）。工程师模式只存在内存里，断电即回到客户模式。

1. 手机连接热点 `toilet_` + MAC 后 6 位（开放、无密码）。
2. **客户配置页：** [http://192.168.99.1](http://192.168.99.1)
3. **工程师测试页：** [http://192.168.99.1/test](http://192.168.99.1/test)  
   ESP32 热点只有一个本机 IP（`192.168.99.1`），工程师入口是该地址下的 `/test`。若写成 `192.168.99.99` 默认到不了板子。
4. **电脑 GUI：** 串口连接后会发 `ENG` 进入工程师模式；也可点「返回客户模式」（`CUST`）。断开串口会回到客户模式。

```powershell
.\venv\Scripts\Activate.ps1
python bench_gui\app.py
```

WiFi 默认开启 30 分钟，超时关闭后需重新上电。
