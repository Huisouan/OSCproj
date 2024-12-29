# The MIT License (MIT)
#
# Copyright (c) 2019 Bryan Siepert for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
`MCP4728`
================================================================================
Helper library for the Microchip MCP4728 I2C 12-bit Quad DAC

Author of original Adafruit_CircuitPython_MCP4728 library: Bryan Siepert
Ported to microPython by Alexander Olikevich (openfablab) with some changes:

* Channel properties read from device not only at init but at every call
* Added power down control function
* Added config() function for laconic channel initial setup
* Changed "raw_value" to "value" and channel names from "channel_a" to "a", etc.
* Removed confusing emulation of 16 bit interface
* Fixed incorrect register values types on initialisation 
* Gains values read and write as 1 or 2
* Rewrited Vref control for simplicity

"""

from struct import pack_into
from time import sleep
_MCP4728_DEFAULT_ADDRESS = 0x60 #0x60
_MCP4728_CH_A_MULTI_EEPROM = 0x50



class MCP4728:
    """Helper library for the Microchip MCP4728 I2C 12-bit Quad DAC.
        :param i2c_bus: The I2C bus the MCP4728 is connected to.
        :param address: The I2C slave address of the sensor
    """

    def __init__(self, i2c_bus, address=_MCP4728_DEFAULT_ADDRESS):
        """
        初始化函数。
        
        :param i2c_bus: I2C总线对象，用于与MCP4728进行通信。
        :param address: MCP4728的I2C地址，默认为_MCP4728_DEFAULT_ADDRESS。
        """
        # 将I2C总线对象和地址保存为实例变量
        self.i2c_device = i2c_bus
        self.address = address
        
        # 读取所有通道的寄存器原始值
        raw_registers = self._read_registers()

        # 根据读取的寄存器值和通道编号初始化四个通道对象
        self.a = Channel(self, self._cache_page(*raw_registers[0]), 0)
        self.b = Channel(self, self._cache_page(*raw_registers[1]), 1)
        self.c = Channel(self, self._cache_page(*raw_registers[2]), 2)
        self.d = Channel(self, self._cache_page(*raw_registers[3]), 3)
        
        
        
    @staticmethod
    def _get_flags(high_byte):
        vref = (high_byte & 1 << 7) > 0
        gain = (high_byte & 1 << 4) > 0
        pdm = (high_byte & 0b011 << 5) >> 5
        return (vref, gain, pdm)

    @staticmethod
    def _cache_page(value, vref, gain, pdm):
        return {"value": value, "vref": vref, "gain": gain, "pdm": pdm}

    def _read_registers(self):
        """
        从I2C设备读取寄存器数据。
        
        此函数首先从I2C设备读取24字节数据，然后解析这些数据以获取当前的输出寄存器值。
        数据被组织为每6字节一个通道，其中前3字节为输出寄存器数据，后3字节为EEPROM数据。
        本函数只关注输出寄存器数据，因此EEPROM数据被忽略。
        
        Returns:
            list: 包含每个通道的元组列表，每个元组包含(value, vref, gain, power_state)。
        """
        # 初始化一个24字节的缓冲区，用于存储从I2C设备读取的数据。
        buf = bytearray(24)
        
        # 从I2C设备读取数据到缓冲区。
        self.i2c_device.readfrom_into(self.address,buf)
        # 解析缓冲区中的数据，获取每个通道的当前值。
        # 初始化一个列表，用于存储解析后的每个通道的当前值。
        current_values = []
        
        # 按每6字节为一组，解析每个通道的数据。
        # pylint:disable=unused-variable
        for header, high_byte, low_byte, na_1, na_2, na_3 in self._chunk(buf, 6):
            # pylint:enable=unused-variable
            # 解析当前通道的值，忽略EEPROM数据。
            value = (high_byte & 0b00001111) << 8 | low_byte
            # 获取并解析高位字节中的标志位。
            vref, gain, power_state = self._get_flags(high_byte)
            # 将解析后的值添加到列表中。
            current_values.append((int(value), int(vref), int(gain)+1, int(power_state)))
        # 返回解析后的数据列表。
        return current_values
    

    def save_settings(self):
        """Saves the currently selected values, Vref, and gain selections for each channel
           to the EEPROM, setting them as defaults on power up"""
        byte_list = []
        byte_list += self._generate_bytes_with_flags(self.a)
        byte_list += self._generate_bytes_with_flags(self.b)
        byte_list += self._generate_bytes_with_flags(self.c)
        byte_list += self._generate_bytes_with_flags(self.d)
        self._write_multi_eeprom(byte_list)

    # TODO: 添加设置偏移量的能力
    def _write_multi_eeprom(self, byte_list):
        """
        向多路 EEPROM 写入字节列表。

        参数:
        byte_list: 要写入多路 EEPROM 的字节列表。

        返回值:
        无
        """
        # 初始化缓冲列表，并加入多路 EEPROM 通道地址
        buffer_list = [_MCP4728_CH_A_MULTI_EEPROM]
        # 将要写入的字节添加到缓冲列表中
        buffer_list += byte_list
        # 将缓冲列表转换为字节序列以供 I2C 传输
        buf = bytearray(buffer_list)
        # 向指定的 I2C 地址写入字节序列
        self.i2c_device.writeto(self.address, buf)
        # 延时以确保数据正确写入
        sleep(0.015)  # 更好的保证数据写入

    def sync_vrefs(self):
        """同步驱动器的vref状态与DAC"""
        # 构建vref设置命令字节，最高位为1表示设置vref
        vref_setter_command = 0b10000000
        # 将通道a、b、c、d的_vref值分别左移3、2、1、0位后，合并到命令字节中
        vref_setter_command |= self.a._vref << 3
        vref_setter_command |= self.b._vref << 2
        vref_setter_command |= self.c._vref << 1
        vref_setter_command |= self.d._vref
        # 创建一个字节数组，用于存储打包后的命令
        buf = bytearray(1)
        # 将vref设置命令打包到字节数组buf中
        pack_into(">B", buf, 0, vref_setter_command)
        # 通过I2C通信，将设置命令发送给指定地址的设备
        self.i2c_device.writeto(self.address,buf)

    def sync_gains(self):
        """Syncs the driver's gain state with the DAC"""
        gain_setter_command = 0b11000000
        gain_setter_command |= (self.a._gain-1) << 3
        gain_setter_command |= (self.b._gain-1) << 2
        gain_setter_command |= (self.c._gain-1) << 1
        gain_setter_command |= (self.d._gain-1)
        buf = bytearray(1)
        pack_into(">B", buf, 0, gain_setter_command)
        self.i2c_device.writeto(self.address,buf)

    def sync_pdms(self):
        """
        同步驱动器的增益状态与DAC（数字模拟转换器）。
        
        通过向I2C设备发送一系列命令，这些命令代表了四个通道(a, b, c, d)的PDM（ Pulse Density Modulation）设置状态。
        每个PDM状态被编码进两个不同的命令字中，根据其所属的通道不同，进行不同的位移操作。
        """
        # 构建第一个PDM设置命令字，包括通道a和b的PDM状态
        pdm_setter_command_1 = 0b10100000
        pdm_setter_command_1 |= (self.a._pdm) << 2
        pdm_setter_command_1 |= (self.b._pdm) 
        # 构建第二个PDM设置命令字，包括通道c和d的PDM状态
        pdm_setter_command_2 = 0b00000000
        pdm_setter_command_2 |= (self.c._pdm) << 6
        pdm_setter_command_2 |= (self.d._pdm) << 4
        # 将两个命令字放入输出缓冲区，准备通过I2C发送
        output_buffer = bytearray([pdm_setter_command_1,pdm_setter_command_2])
        # 向I2C设备发送数据，同步PDM状态
        self.i2c_device.writeto(self.address,output_buffer)

    def _set_value(self, channel):
        """
        设置DAC通道的输出值。

        此方法首先生成包含通道值和标志的字节序列，然后根据这些字节和通道索引
        构建一个写命令字节。最后，将写命令字节和通道值字节序列组合成输出缓冲区，
        并通过I2C通信将该缓冲区发送到DAC设备。

        参数:
        - channel: DACChannel对象，包含要设置的DAC通道索引和值。

        返回值:
        无返回值。
        """
        # 生成包含通道值和标志的字节序列
        channel_bytes = self._generate_bytes_with_flags(channel)
        # 构建写命令字节，设置DAC1、DAC0和UDAC位
        # 0b01000000 表示 B7位为0，B6位为1，其余位在后续操作中设置
        write_command_byte = 0b01000000  # 0 1 0 0 0 DAC1 DAC0 UDAC
        # 根据通道索引设置DAC1和DAC0位
        write_command_byte |= channel.channel_index << 1
        # 初始化输出缓冲区，将写命令字节作为第一个元素
        output_buffer = bytearray([write_command_byte])
        # 将通道值字节序列添加到输出缓冲区
        output_buffer.extend(channel_bytes)
        # 通过I2C通信将输出缓冲区发送到DAC设备
        self.i2c_device.writeto(self.address, output_buffer)

    @staticmethod
    def _generate_bytes_with_flags(channel):
        buf = bytearray(2)
        pack_into(">H", buf, 0, channel._value)
        buf[0] |= channel._vref << 7
        buf[0] |= (channel._gain-1) << 4
        return buf

    @staticmethod
    def _chunk(big_list, chunk_size):
        """Divides a given list into `chunk_size` sized chunks"""
        for i in range(0, len(big_list), chunk_size):
            yield big_list[i : i + chunk_size]


class Channel:
    """An instance of a single channel for a multi-channel DAC.
    **All available channels are created automatically and should not be created by the user**"""

    def __init__(self, dac_instance, cache_page, index):
        self._vref = cache_page["vref"]
        self._gain = cache_page["gain"]
        self._value = cache_page["value"]
        self._pdm = cache_page["pdm"]
        self._dac = dac_instance
        self.channel_index = index

    @property
    def normalized_value(self):
        """The DAC value as a floating point number in the range 0.0 to 1.0."""
        return self.value / (2 ** 12 - 1)

    @normalized_value.setter
    def normalized_value(self, value):
        if value < 0.0 or value > 1.0:
            raise AttributeError("`normalized_value` must be between 0.0 and 1.0")

        self.value = int(value * 4095.0)

    @property
    def value(self):
      """The 12-bit current value for the channel."""
      self._value=self._dac._read_registers()[self.channel_index][0] 
      return self._value

    @value.setter
    def value(self, value):
        if value < 0 or value > (2 ** 12 - 1):
            raise AttributeError(
                "`raw_value` must be a 12-bit integer between 0 and %s" % (2 ** 12 - 1)
            )
        self._value=value
        self._dac._set_value(self)  # pylint:disable=protected-access

    @property
    def gain(self):
        """Sets the gain of the channel if the Vref for the channel is ``Vref.INTERNAL``.
        **The gain setting has no effect if the Vref for the channel is `Vref.VDD`**.

        With gain set to 1, the output voltage goes from 0v to 2.048V. If a channe's gain is set
        to 2, the voltage goes from 0v to 4.096V. `gain` Must be 1 or 2"""
        self._gain=self._dac._read_registers()[self.channel_index][2] 
        return self._gain

    @gain.setter
    def gain(self, value):
        if not value in (1, 2):
            raise AttributeError("Gain must be 1 or 2")
        self._gain = value
        self._dac.sync_gains()

    @property
    def vref(self):
        """Sets the DAC's voltage reference source. Must be 0 (VDD) or 1 (Internal 2.048V)"""
        self._vref=self._dac._read_registers()[self.channel_index][1] 
        return self._vref

    @vref.setter
    def vref(self, value):
        if not value in (0, 1):
            raise AttributeError("Vref must be 0 (VDD) or 1 (Internal 2.048V)")
        self._vref = value
        self._dac.sync_vrefs()

    @property
    def pdm(self):
        """
        设置DAC的电源管理（PDM）模式。有两种模式可供选择：
        - 0：正常操作模式，所有通道电路正常工作。
        - 非0：关闭大多数通道电路，并通过电阻将VOUT连接到GND，电阻值根据模式不同而不同（1：1 kΩ，2：100 kΩ，3：500 kΩ）。
        
        该方法首先从DAC寄存器读取当前的PDM状态，然后将其存储在实例变量`_pdm`中，最后返回这个状态值。
        """
        # 从DAC寄存器中读取当前PDM状态，并将其保存到实例变量`_pdm`中
        self._pdm = self._dac._read_registers()[self.channel_index][3] 
        # 返回PDM状态
        return self._pdm

    @pdm.setter
    def pdm(self, value):
        if not value in (0, 1, 2, 3):
            raise AttributeError("""Power down mode must be 0 for normal operation, or
            other to turn off most of the channel circuits and connect VOUT to GND by 
            resistor (1: 1 kΩ, 2: 100 kΩ, 3: 500 kΩ).""")
        self._pdm = value
        self._dac.sync_pdms()

    def config(self, value=0, vref=1, gain=1, pdm=0):
        self.vref=vref
        self.gain=gain
        self.value=value
        self.pdm=pdm
