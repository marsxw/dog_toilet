# ESP32-S3-WROOM-1（新 PCB IO）

# 红外：固定 GPIO1 数字输入。触发=低、未触发=高
PIN_IR = 1

# 电机电流：采样电阻 0.1Ω，放大 10.5 倍后进 ADC
PIN_IADC = 3

# 粉碎电机驱动芯片 IN1 / IN2（禁止两脚同时为高）
PIN_CRUSH_IN1 = 11
PIN_CRUSH_IN2 = 12

# 冲水舵机 PWM
PIN_SERVO = 13
