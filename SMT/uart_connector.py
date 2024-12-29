#file:c:\Codes\OSCproj\SMT\uart_connector.py
import serial
import time

class UARTConnector:
    def __init__(self, port, baudrate=115200, timeout=1):
        """
        初始化UART连接器

        :param port: 串口号，例如 'COM3' 或 '/dev/ttyUSB0'
        :param baudrate: 波特率，默认为 115200
        :param timeout: 读取超时时间，默认为 1 秒
        :param parity: 校验位，默认为无校验 (serial.PARITY_NONE)
        :param stopbits: 停止位，默认为 1 (serial.STOPBITS_ONE)
        :param bytesize: 数据位，默认为 8 (serial.EIGHTBITS)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None

    def connect(self):
        """
        打开串口连接
        """
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            print(f"成功连接到 {self.port}")
        except serial.SerialException as e:
            print(f"连接失败: {e}")

    def disconnect(self):
        """
        关闭串口连接
        """
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print(f"已断开 {self.port} 连接")

    def send_data(self, data):
        """
        发送数据到串口

        :param data: 要发送的数据，可以是字符串或字节
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write(data)
            print(f"发送数据: {data}")

    def read_data(self, size=1):
        """
        从串口读取数据

        :param size: 要读取的字节数，默认为 1
        :return: 读取到的数据（字符串）
        """
        if self.serial_connection and self.serial_connection.is_open:
            data = self.serial_connection.read(size)
            decoded_data = data.decode('utf-8')
            print(f"接收数据: {decoded_data}")
            return decoded_data
        return None

    def read_until(self, terminator=b'\n'):
        """
        从串口读取数据直到遇到指定的终止符

        :param terminator: 终止符，默认为换行符 b'\n'
        :return: 读取到的数据（字符串）
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            return None

        data = bytearray()
        while True:
            byte = self.serial_connection.read(1)
            if byte:
                data += byte
                if data.endswith(terminator):
                    break
            else:
                break

        decoded_data = bytes(data).decode('utf-8')
        print(f"接收数据: {decoded_data}")
        return decoded_data

    def flush_buffers(self):
        """
        清空串口的输入和输出缓冲区
        """
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            print("已清空缓冲区")

# 示例用法
if __name__ == "__main__":
    uart = UARTConnector(
        port='COM10',  # 根据实际情况修改串口号
        baudrate=115200,
        timeout=1,
    )
    uart.connect()

    while True:
        received_data = uart.read_until()
        time.sleep(1)
    uart.disconnect()