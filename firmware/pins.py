# ESP32-S3-WROOM-1 (新 PCB 原理图 net 名)

# 红外 HR_INPUT（原理图 net IO1 = GPIO1）。分压后数字输入，触发=低、未触发=高
PIN_IR = 1

# 按压电机 A4950：IREF 经 RC 滤波作为电流/等效电压参考，PWM 调占空比
PIN_IREF = 10
PIN_MOTOR_H = 11
PIN_MOTOR_L = 12

# 粉碎电机：经 UCC27517 驱动 MOSFET，高电平导通
PIN_CRUSH = 9
