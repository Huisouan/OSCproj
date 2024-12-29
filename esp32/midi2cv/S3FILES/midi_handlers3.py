import machine
import mcp4728
# midi_handler.py
from machine import Pin
GATE1 = Pin(48, Pin.OUT, Pin.PULL_DOWN)
GATE2 = Pin(47, Pin.OUT, Pin.PULL_DOWN)
GATE3 = Pin(21, Pin.OUT, Pin.PULL_DOWN)
GATE4 = Pin(20, Pin.OUT, Pin.PULL_DOWN)
GATE5 = Pin(19, Pin.OUT, Pin.PULL_DOWN)
GATE6 = Pin(7, Pin.OUT, Pin.PULL_DOWN)

# 定义TRIGGER引脚为推挽输出模式并初始化为下拉状态
TRIGGER = Pin(8, Pin.OUT, Pin.PULL_DOWN)

NOTE_ON = 0x90
NOTE_OFF = 0x80
CONTROL_CHANGE = 0xB0
PITCH_BEND = 0xE0


class MidiMessage:
    def __init__(self, status, data1=0, data2=0):
        # 确保所有参数都是整数
        self.status = int(status)
        self.data1 = int(data1)
        self.data2 = int(data2)

        # 验证 MIDI 状态字节是否有效
        if not (0x80 <= self.status <= 0xEF):
            raise ValueError("Invalid MIDI status byte")

        # 验证 data1 和 data2 是否在 0-127 的范围内
        if not (0 <= self.data1 <= 127) or not (0 <= self.data2 <= 127):
            raise ValueError("Data values must be in the range 0-127")

    @property
    def command(self):
        return self.status & 0xF0

    @property
    def channel(self):
        return self.status & 0x0F

    @property
    def type(self):
        # 返回MIDI消息的类型
        if self.command == NOTE_ON:
            return 'note_on'
        elif self.command == NOTE_OFF:
            return 'note_off'
        elif self.command == CONTROL_CHANGE:
            return 'control_change'
        elif self.command == PITCH_BEND:
            return 'pitchwheel'
        else:
            return 'unknown'

    def __repr__(self):
        return f"MidiMessage(status={self.status:02X}, data1={self.data1:02X}, data2={self.data2:02X})"

class MidiToVoltageConverter:
    def __init__(self, i2c, dac_addresses):
        self.dacs = []
        for address in dac_addresses:
            try:
                dac = mcp4728.MCP4728(i2c, address)
                dac.a.vref = 1
                dac.b.vref = 1
                dac.c.vref = 1
                dac.d.vref = 1
                dac.a.gain = 2
                dac.b.gain = 2
                dac.c.gain = 2 
                dac.d.gain = 2
                self.dacs.append(dac)
                print(f"Initialized DAC at address 0x{address:X}")
            except OSError as e:
                print(f"Failed to initialize MCP4728 at address 0x{address:X}: {e}")

        self.gates = [GATE1, GATE2, GATE3, GATE4, GATE5, GATE6]
        self.notes = [self.dacs[0].b, self.dacs[0].c,
                      self.dacs[1].a, self.dacs[1].c,
                      self.dacs[2].a, self.dacs[2].c,                     
                      ]
        self.vel = self.dacs[0].a
        self.pitchbend = self.dacs[1].d
        self.cc = self.dacs[1].b
        self.notestatus = [None, None, None, None, None, None]
        self.midilatch = []
        self.channel = 0
        
        
        
    def midi_to_voltage(self, data):
        """
        将0-127之间的数值转换为适合12位DAC使用的值。

        :param data: 一个0-127之间的数值
        :return: 一个0-4095之间的12位数值，用于驱动DAC
        """
        dac_value = (data << 4) | (data >> 4)
        
        return dac_value

    
    def parse_midi_message(self,data):
        """
            解析MIDI消息。data是一个包含MIDI消息字节的列表或字节串。
        """
        if len(data) < 2:
            return None
        status = data[0]
        if len(data) > 1:
            data1 = data[1]
            if len(data) > 2:
                data2 = data[2]
            else:
                data2 = 0
            self.midimessage = MidiMessage(status, data1, data2)
            return self.midimessage
        return None


    def update_noteon(self, note, velocity):
        """
        处理MIDI音符触键事件，将MIDI信号转换为控制电压，并更新内部状态。

        参数:
        note -- 被触键的音符，表示为MIDI音符编号。
        velocity -- 触键的力度，表示为MIDI力度值。

        返回值:
        无
        """
        full = False
        # 遍历6个音符通道，寻找空闲通道
        for i in range(6):
            if self.notestatus[i] == None:
                # 触发信号，准备发送MIDI信息
                TRIGGER.value(1)
                # 将MIDI音符转换为控制电压并发送
                self.notes[i].value = self.midi_to_voltage(note)
                # 将MIDI力度转换为控制电压并发送
                self.vel.value = self.midi_to_voltage(velocity)
                # 更新通道状态为当前音符
                self.notestatus[i] = note
                # 打开通道的门控
                self.gates[i].value(1)
                # 记录触发的通道编号
                self.midilatch.append(i)
                # 打印触发信息
                #print(f"note: {self.notes[i]}")
                # 结束触发信号
                TRIGGER.value(0)
                full = False
                break
        else:
            full = True
        
        if full:
            # 从等待队列中移除并返回最早触发的通道编号
            latch = self.midilatch.pop(0)
            print("Latch = {latch}")
            # 触发信号，准备发送MIDI信息
            TRIGGER.value(1)
            # 将MIDI音符转换为控制电压并发送
            self.notes[latch].value = self.midi_to_voltage(note)
            # 将MIDI力度转换为控制电压并发送
            self.vel.value = self.midi_to_voltage(velocity)
            # 更新通道状态为当前音符
            self.notestatus[latch] = note
            # 打开通道的门控
            self.gates[latch].value(1)
            # 更新等待队列，记录当前触发的通道编号
            self.midilatch.append(latch)
            # 打印更新信息
            #print(f"note: {self.notes[latch]}") 
            # 结束触发信号
            TRIGGER.value(0)
        
        
        
    def update_noteoff(self, note):
        """
        处理midi音符释放事件。

        当检测到特定音符的状态为释放时，更新内部状态，并将相关音符从中间件中移除。
        这个方法负责在音符状态数组中找到指定音符，然后将对应的门控信号设为关闭，
        清零速度值，并从音符状态和中间件中移除该音符。

        参数:
        note -- 待处理的midi音符编号。
        """
        # 遍历音符状态数组，寻找与传入音符匹配的项
        for i in range(6):
            if self.notestatus[i] == note:
                # 找到匹配的音符时，关闭对应的门控信号
                self.gates[i].value(0)
                # 将速度值设为0，表示没有音符演奏
                self.vel.value = 0
                # 将当前音符状态设为None，表示该位置空闲
                self.notestatus[i] = None
                # 从中间件中移除已释放的音符，并打印信息
                # 使用remove而不是pop，因为pop需要正确的索引
                try:
                    self.midilatch.remove(i)
                except ValueError:
                    pass  # 如果i不在midilatch中，忽略这个错误
                #print(f"noteoff: {self.midilatch}")
                #print(f"noteoff: {self.notestatus}")

            
    def update_cc(self,cc):
        #cc = vel5
        self.cc.value = cc
        print(f"cc: {self.cc}")
        
    def update_pitchbend(self,pb):
        #pb = vel7
        pb_12bit = (pb >> 2) & 0xFFF  # 右移4位以匹配12位DAC的范围
        
        # 将转换后的值写入DAC
        self.pitchbend.value = pb_12bit
        print(f"pitchbend: {pb_12bit}")
     
    def handle_midi_message(self, message):
        """
        处理MIDI消息。
        """
        if message.type == 'note_on' and message.data2 > 0:
            print(f"Note On: Channel {message.channel}, Note {message.data1}, Velocity {message.data2}")  
            self.update_noteon(message.data1, message.data2)
        elif message.type == 'note_off':
            print(f"Note Off: Channel {message.channel}, Note {message.data1}, Velocity {message.data2}")
            self.update_noteoff(message.data1)
        elif message.type == 'control_change':
            print(f"Control Change: Channel {message.channel}, Controller {message.data1}, Value {message.data2}")
            cc = self.midi_to_voltage(message.data2)
            self.update_cc(cc)
        elif message.type == 'pitchwheel':
            pitch_bend = message.data2 + (message.data1 << 7)
            print(f"Pitch Bend: Channel {message.channel}, Value {pitch_bend}")
            print(f"MidiMessage(data1={message.data1}, data2={message.data2})")
            self.update_pitchbend(pitch_bend)