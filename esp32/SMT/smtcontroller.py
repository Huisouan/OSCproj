from machine import Pin, I2C, UART
import time
import math

# 定义 UART 引脚

AIR_PUMP = 4
UP_LIGHT = 5
DOWN_LIGHT = 6

A_EN = 1
A_STEP = 2
A_DIR = 42

B_EN = 41
B_STEP = 40
B_DIR = 39

C_EN = 38
C_STEP = 37
C_DIR = 36

D_EN = 35
D_STEP = 0
D_DIR = 45

class Motar:
    def __init__(self, en, step, dir):
        self.en = Pin(en, Pin.OUT)
        self.step = Pin(step, Pin.OUT)
        self.dir = Pin(dir, Pin.OUT)
        self.position = 0
        self.target_position = 0

        self.direction = 0  # 0: 正向, 1: 反向

    def on(self):
        self.en.value(1)

    def off(self):
        self.en.value(0)

    def set_direction(self, direction):
        self.direction = direction
        self.dir.value(direction)
    
    def get_position(self):
        return self.position
    
    def set_position(self, position):
        self.position = position

class CoreXY:
    def __init__(self, a_en, a_step, a_dir, b_en, b_step, b_dir):
        self.motar_a = Motar(a_en, a_step, a_dir)
        self.motar_b = Motar(b_en, b_step, b_dir)
        self.steps_per_second = 1000  # max_speed 
        self.acceleration = 1 # 设置加速度

    def set_steps_per_second(self, steps_per_second):
        self.steps_per_second = steps_per_second
    
    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

    def move_motors(self, delta_a, delta_b):
        # 初始化方向
        self.motar_a.set_direction(1 if delta_a > 0 else 0)
        self.motar_b.set_direction(1 if delta_b > 0 else 0)

        # 计算总步数
        total_steps_a = abs(delta_a)
        total_steps_b = abs(delta_b)

        # 计算最大速度
        max_speed_a = self.steps_per_second
        max_speed_b = self.steps_per_second

        # 计算加速度阶段的步数
        accel_steps_a = int(0.5 * max_speed_a / self.acceleration)
        accel_steps_b = int(0.5 * max_speed_b / self.acceleration)

        # 初始化时间戳
        start_time = time.ticks_ms()

        # 运动循环
        for i in range(max(total_steps_a, total_steps_b)):
            current_time = time.ticks_diff(time.ticks_ms(), start_time) / 1000  # 转换为秒

            # 计算当前速度
            if i < accel_steps_a:
                speed_a = self.acceleration * (3 * (i / accel_steps_a) ** 2 - 2 * (i / accel_steps_a) ** 3)
            elif i > total_steps_a - accel_steps_a:
                speed_a = max_speed_a - self.acceleration * (3 * ((total_steps_a - i) / accel_steps_a) ** 2 - 2 * ((total_steps_a - i) / accel_steps_a) ** 3)
            else:
                speed_a = max_speed_a

            if i < accel_steps_b:
                speed_b = self.acceleration * (3 * (i / accel_steps_b) ** 2 - 2 * (i / accel_steps_b) ** 3)
            elif i > total_steps_b - accel_steps_b:
                speed_b = max_speed_b - self.acceleration * (3 * ((total_steps_b - i) / accel_steps_b) ** 2 - 2 * ((total_steps_b - i) / accel_steps_b) ** 3)
            else:
                speed_b = max_speed_b

            # 计算步进间隔
            step_interval_a = 1 / speed_a if speed_a > 0 else 0
            step_interval_b = 1 / speed_b if speed_b > 0 else 0

            # 计算下一个步进的时间戳
            next_step_time_a = start_time + i * step_interval_a * 1000
            next_step_time_b = start_time + i * step_interval_b * 1000

            # 步进电机A
            if i < total_steps_a and current_time >= next_step_time_a:
                self.motar_a.step.on()
                time.sleep_us(1)
                self.motar_a.step.off()

            # 步进电机B
            if i < total_steps_b and current_time >= next_step_time_b:
                self.motar_b.step.on()
                time.sleep_us(1)
                self.motar_b.step.off()

        self.motar_b.step.off()
        self.motar_a.step.off()

class OneAxis:
    def __init__(self, z_en, z_step, z_dir):
        self.motar = Motar(z_en, z_step, z_dir)
        self.steps_per_second = 1000  # max_speed 
        self.acceleration = 1 # 设置加速度    
    
    def set_steps_per_second(self, steps_per_second):
        self.steps_per_second = steps_per_second
    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

    def move_motors(self, delta):
        # 初始化方向
        self.motar.set_direction(1 if delta > 0 else 0)

        # 计算总步数
        total_steps = abs(delta)

        # 计算最大速度
        max_speed = self.steps_per_second

        # 计算加速度阶段的步数
        accel_steps = int(0.5 * max_speed / self.acceleration)

        # 初始化时间戳
        start_time = time.ticks_ms()

        # 运动循环
        for i in range(total_steps):
            current_time = time.ticks_diff(time.ticks_ms(), start_time) / 1000  # 转换为秒

            # 计算当前速度
            if i < accel_steps:
                speed = self.acceleration * (3 * (i / accel_steps) ** 2 - 2 * (i / accel_steps) ** 3)
            elif i > total_steps - accel_steps:
                speed = max_speed - self.acceleration * (3 * ((total_steps - i) / accel_steps) ** 2 - 2 * ((total_steps - i) / accel_steps) ** 3)
            else:
                speed = max_speed

            # 计算步进间隔
            step_interval = 1 / speed if speed > 0 else 0

            # 计算下一个步进的时间戳
            next_step_time = start_time + i * step_interval * 1000

            # 步进电机Z
            if current_time >= next_step_time:
                self.motar.step = -self.motar.step
        self.motar.step.off()

class SmtController:
    def __init__(self):
        self.busy = False
        self.uart = UART(1, baudrate=115200, tx=Pin(15), rx=Pin(16))
        self.send_data("init smt controller\n")
        
        self.init_rigids()

    def init_rigids(self):
        self.uart.write("init rigids\n")
        self.air_pump = Pin(AIR_PUMP, Pin.OUT)
        self.up_light = Pin(UP_LIGHT, Pin.OUT)
        self.down_light = Pin(DOWN_LIGHT, Pin.OUT)
        self.corexy = CoreXY(A_EN, A_STEP, A_DIR, B_EN, B_STEP, B_DIR)
        self.zaxis = OneAxis(C_EN, C_STEP, C_DIR)
        self.raxis = OneAxis(D_EN, D_STEP, D_DIR)
        self.uart.write("init rigids done\n")

    def send_data(self,data):
        """ 发送数据到UART """
        self.uart.write(data.encode())
        print(f"Sent: {data}\n")

    def receive_data(self):
        """ 从UART接收数据 """
        if self.uart.any():
            data = self.uart.read()
            print(f"Received: {data.decode()}\n")
            return data.decode()
        
        return None
    
    def air_pump_on(self):
        self.air_pump.value(1)
    
    def air_pump_off(self):
        self.air_pump.value(0)
        
    def up_light_on(self):
        self.up_light.value(1)
        
    def up_light_off(self):
        self.up_light.value(0)
        
    def down_light_on(self):
        self.down_light.value(1)
        
    def down_light_off(self):
        self.down_light.value(0)

    def read_command(self):
        data = self.uart.read()
        self.process_command(data)

    def more_corexy(self, *args):
        self.corexy.move_motors(*args)

    def process_command(self):
        data = self.receive_data()
        if data:
            command = data.strip()
            parts = command.split()
            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            if cmd in self.commands:
                print(f"Command {cmd} processed with args: {args}")
                self.commands[cmd](*args) 
            else:
                self.send_data(f"Unknown command: {cmd}\n")
        else:
            self.send_data("wait_for_command\n")
    def handle_cmd1(self, *args):
        print(f"Handling CMD1 with args: {args}")
        # 处理 CMD1 的逻辑，使用 args

    def handle_cmd2(self, *args):
        print(f"Handling CMD2 with args: {args}")
        # 处理 CMD2 的逻辑，使用 args

    @property
    def commands(self):
        return {
            'up_light_on': self.up_light_on,
            'up_light_off': self.up_light_off,
            'down_light_on': self.down_light_on,
            'down_light_off': self.down_light_off,
            'air_pump_on': self.air_pump_on,
            'air_pump_off': self.air_pump_off,
            
            # 添加更多命令
        }