from machine import Pin, I2C,UART

# 定义 UART 引脚
TX_PIN = 17  # TX (通常用于发送)
RX_PIN = 18  # RX (通常用于接收)


GATE = Pin(48, Pin.OUT, Pin.PULL_DOWN)


# 定义TRIGGER引脚为推挽输出模式并初始化为下拉状态
TRIGGER = Pin(8, Pin.OUT, Pin.PULL_DOWN)
