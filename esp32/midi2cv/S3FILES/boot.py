from machine import Pin, I2C, UART
import time
from midi_handlers3 import MidiToVoltageConverter

# 定义 UART 引脚
TX_PIN = 17  # TX (通常用于发送)
RX_PIN = 18  # RX (通常用于接收)

# 配置SCL为推挽输出模式
SCL = Pin(2, Pin.OUT, Pin.PULL_UP)

# 配置SDA为开漏输出模式
SDA = Pin(1, Pin.OPEN_DRAIN)

# 构建1个I2C对象
i2c = I2C(0, scl=SCL, sda=SDA, freq=400000)

DAC_ADDRESSES = [0x60, 0x61]

midi2cv = MidiToVoltageConverter(i2c, DAC_ADDRESSES)

# 初始化 UART
uart = UART(2, baudrate=31250, tx=TX_PIN, rx=RX_PIN)

# 主循环


def main():
    buffer = bytearray()  # 用于保存不完整的 MIDI 消息
    while True:
        if uart.any():
            # 读取完整的 MIDI 消息
            data = uart.read(3)  # 假设 MIDI 消息最大长度为 3 字节
            if data:
                buffer.extend(data)
                while len(buffer) >= 3:  # 确保有足够的数据构成一个完整的 MIDI 消息
                    midi_message = buffer[:3]
                    try:
                        parsed_midi_message = midi2cv.parse_midi_message(list(midi_message))
                        if parsed_midi_message: 
                            midi2cv.handle_midi_message(parsed_midi_message)
                    except Exception as e:
                        print(f"Error parsing MIDI message: {e}")
                        uart.read() # 直接赋值为空的 bytearray 来清空 buffer
                        
                    buffer = buffer[3:]  # 移除已处理的消息
        # 可以尝试减少或移除延时
        # time.sleep_ms(5)

# 运行主循环
main()