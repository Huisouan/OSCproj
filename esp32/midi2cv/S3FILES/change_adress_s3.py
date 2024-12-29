from machine import Pin
import time
# 定义引脚
# 配置SCL为推挽输出模式
SCL = Pin(2, Pin.OUT, Pin.PULL_UP)

# 配置SDA为开漏输出模式
SDA = Pin(1, Pin.OPEN_DRAIN)
# 配置LDAC为推挽输出模式
LDAC1 = Pin(42, Pin.OUT, Pin.PULL_UP)
LDAC2 = Pin(40, Pin.OUT, Pin.PULL_UP)
LDAC3 = Pin(38, Pin.OUT, Pin.PULL_UP)
LDAC4 = Pin(36, Pin.OUT, Pin.PULL_UP)
LDAC5 = Pin(0, Pin.OUT, Pin.PULL_UP)

# 配置RDY为输入模式
RDY_1 = Pin(41, Pin.IN)
RDY_2 = Pin(39, Pin.IN)
RDY_3 = Pin(37, Pin.IN)
RDY_4 = Pin(35, Pin.IN)
RDY_5 = Pin(45, Pin.IN)
def IIC_Start_MCP4728():
    SDA.value(1)              # 拉高数据线 SDA_Pin = 1
    SCL.value(1)              # 拉高时钟线 SCL_Pin = 1
    time.sleep_us(4)          # 延时
    SDA.value(0)              # 产生下降沿 SDA_Pin = 0
    time.sleep_us(4)          # 延时
    SCL.value(0)              # 拉低时钟线 SCL_Pin = 0

def IIC_Stop():
    SCL.value(0)              # 拉低时钟线 SCL_Pin = 0
    SDA.value(0)              # 拉低数据线 SDA_Pin = 0
    time.sleep_us(5)          # 延时
    SCL.value(1)              # 拉高时钟线 SCL_Pin = 1
    SDA.value(1)              # 产生上升沿 SDA_Pin = 1
    time.sleep_us(5)          # 延时

def I2C1_Wait_Ack():
    ucErrTime = 0
    SDA.value(1)              # 拉高数据线 SDA_Pin = 1
    time.sleep_us(1)          # 延时
    SCL.value(1)              # 拉高时钟线 SCL_Pin = 1
    time.sleep_us(1)          # 延时
    while SDA.value() == 1:
        ucErrTime += 1
        if ucErrTime > 1000:
            IIC_Stop()        # 调用停止函数
            return 1          # 返回错误
    SCL.value(0)              # 时钟输出0
    return 0                  # 返回成功



def I2C1_Ack():
    SCL.value(0)              # 拉低时钟
    SDA.value(0)              # 拉低数据线
    time.sleep_us(2)
    SCL.value(1)              # 拉高时钟
    time.sleep_us(2)
    SCL.value(0)              # 拉低时钟

def I2C1_NAck():
    SCL.value(0)              # 拉低时钟
    SDA.value(1)              # 拉高数据线
    time.sleep_us(2)
    SCL.value(1)              # 拉高时钟
    time.sleep_us(2)
    SCL.value(0)              # 拉低时钟






def I2C1_Send_One_Byte(txd):
    SCL.value(0)              # 拉低时钟开始数据传输
    for _ in range(8):        # 开始准备信号线
        if txd & 0x80:        # 判断最高位
            SDA.value(1)      # 送数据口 SDA_Pin = 1
        else:
            SDA.value(0)      # 送数据口 SDA_Pin = 0
        txd <<= 1             # 移位
        time.sleep_us(2)      # 这三个延时都是必须的
        SCL.value(1)          # 拉高时钟
        time.sleep_us(2)
        SCL.value(0)          # 拉低时钟
        time.sleep_us(2)
        
def I2C1_Read_One_Byte(ack):
    receive = 0
    for _ in range(8):
        SCL.value(0)          # 拉低时钟
        time.sleep_us(2)
        SCL.value(1)          # 拉高时钟
        receive <<= 1
        if SDA.value() == 1:
            receive |= 1
        time.sleep_us(1)
    
    if not ack:
        I2C1_NAck()           # 发送 nACK
    else:
        I2C1_Ack()            # 发送 ACK
    return receive


def MCP4728_ReadAddr(cs):
    rt = 1
    ADDR_Read = 0
    LDAC1.value(1)
    LDAC2.value(1)
    LDAC3.value(1)
    LDAC4.value(1)  # 初始化 LDAC4
    LDAC5.value(1)  # 初始化 LDAC5
    IIC_Start_MCP4728()
    I2C1_Send_One_Byte(0x00)  # 器件地址
    rt = I2C1_Wait_Ack()
    I2C1_Send_One_Byte(0x0C)
    

    if cs == 0x01:
        LDAC1.value(0)  # 片选为1则第1片设为低电平
    elif cs == 0x02:
        LDAC2.value(0)  # 片选为2则第2片设为低电平
    elif cs == 0x03:
        LDAC3.value(0)  # 片选为3则第3片设为低电平
    elif cs == 0x04:
        LDAC4.value(0)  # 片选为4则第4片设为低电平
    elif cs == 0x05:
        LDAC5.value(0)  # 片选为5则第5片设为低电平
   
    rt = I2C1_Wait_Ack()
    IIC_Start_MCP4728()
    I2C1_Send_One_Byte(0xC1)
    rt = I2C1_Wait_Ack()
    ADDR_Read = I2C1_Read_One_Byte(0)
    IIC_Stop()
    ADDR_Read = ((ADDR_Read >> 4) & 0x0E) | 0xC0  # 得到地址信息
    LDAC1.value(1)
    LDAC2.value(1)
    LDAC3.value(1)
    LDAC4.value(1)  # 初始化 LDAC4
    LDAC5.value(1)  # 初始化 LDAC5    
    
    return ADDR_Read

def change_address(OldAddr, Cmd_NewAdd,cs):
    LDAC1.value(1)
    LDAC2.value(1)
    LDAC3.value(1)
    LDAC4.value(1)  # 初始化 LDAC4
    LDAC5.value(1)  # 初始化 LDAC5
    IIC_Start_MCP4728()
    I2C1_Send_One_Byte(OldAddr)  # 器件地址
    I2C1_Wait_Ack()
    I2C1_Send_One_Byte(((OldAddr & 0x0E) << 1) | 0x61)  # 发送命令+当前地址 0x61
    
    if cs == 0x01:
        LDAC1.value(0)  # 片选为1则第1片设为低电平
    elif cs == 0x02:
        LDAC2.value(0)  # 片选为2则第2片设为低电平
        LDAC5.value(0)  # 片选为5则第5片设为低电平
    elif cs == 0x03:
        LDAC3.value(0)  # 片选为3则第3片设为低电平
    elif cs == 0x04:
        LDAC4.value(0)  # 片选为4则第4片设为低电平
    elif cs == 0x05:
        LDAC2.value(0)  # 片选为2则第2片设为低电平
        LDAC5.value(0)  # 片选为5则第5片设为低电平
    
    I2C1_Wait_Ack()
    I2C1_Send_One_Byte(((Cmd_NewAdd & 0x0E) << 1) | 0x62)  # 发送新地址
    I2C1_Wait_Ack()
    I2C1_Send_One_Byte(((Cmd_NewAdd & 0x0E) << 1) | 0x63)  # 确认发送新地址
    I2C1_Wait_Ack()
    IIC_Stop()  # 产生一个停止条件
    LDAC1.value(1)
    LDAC2.value(1)
    LDAC3.value(1)
    LDAC4.value(1)  # 初始化 LDAC4
    LDAC5.value(1)  # 初始化 LDAC5    
    time.sleep_ms(20)  # 延时

def MCP4728Init():
    
    MCP4728_ADDR1 = 0xC0  # 假设 MCP4728 的第1片期望地址
    MCP4728_ADDR2 = 0xCe  # 假设 MCP4728 的第2片期望地址
    MCP4728_ADDR3 = 0xC2  # 假设 MCP4728 的第3片期望地址
    MCP4728_ADDR4 = 0xC4  # 新增 MCP4728 的第4片期望地址
    MCP4728_ADDR5 = 0xCe  # 新增 MCP4728 的第5片期望地址
    all_adjusted = False
    while not all_adjusted:
        addr1 = MCP4728_ReadAddr(0x01)  # 读取第1片的地址
        addr2 = MCP4728_ReadAddr(0x02)  # 读取第2片的地址
        addr3 = MCP4728_ReadAddr(0x03)  # 读取第3片的地址
        addr4 = MCP4728_ReadAddr(0x04)  # 读取第4片的地址
        addr5 = MCP4728_ReadAddr(0x05)  # 读取第5片的地址
        print(f"addr1: {addr1:x} addr2: {addr2:x} addr3: {addr3:x} addr4: {addr4:x} addr5: {addr5:x}")
        if addr1 != MCP4728_ADDR1:
            change_address(addr1, MCP4728_ADDR1, 0x01)
            print("addr1notadjusted")
        if addr2 != MCP4728_ADDR2:
            change_address(addr2, MCP4728_ADDR2, 0x02)
            print("addr2notadjusted")
        if addr3 != MCP4728_ADDR3:
            change_address(addr3, MCP4728_ADDR3, 0x03)
            print("addr3notadjusted")
        if addr4 != MCP4728_ADDR4:
            change_address(addr4, MCP4728_ADDR4, 0x04)
            print("addr4notadjusted")
        if addr5 != MCP4728_ADDR5:
            change_address(addr5, MCP4728_ADDR5, 0x05)
            print("addr5notadjusted")
        
        LDAC1.value(1)
        LDAC2.value(1)
        LDAC3.value(1)
        LDAC4.value(1)
        LDAC5.value(1)
        
        # 检查所有地址是否都已经调整到位
        all_adjusted = (addr1 == MCP4728_ADDR1 and
                        addr2 == MCP4728_ADDR2 and
                        addr3 == MCP4728_ADDR3 and
                        addr4 == MCP4728_ADDR4 and
                        addr5 == MCP4728_ADDR5)
        
        if not all_adjusted:
            time.sleep_ms(10)  # 如果还有地址未调整到位，则延时后继续尝试
        else :
            print("所有地址都已调整到位")

MCP4728Init()