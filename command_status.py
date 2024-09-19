# command_status.py

from amaranth import *

class CommandStatus(Elaboratable):
    def __init__(self):
        # 输入信号
        self.addr = Signal(4)       # 地址偏移
        self.data_in = Signal(32)
        self.we = Signal()          # 写使能
        self.re = Signal()          # 读使能

        # 输出信号
        self.data_out = Signal(32)

        # 命令和状态寄存器
        self.command_reg = Signal(32, reset=0x00000000)
        self.status_reg = Signal(32, reset=0x00000000)

    def elaborate(self, platform):
        m = Module()

        # 数据读取逻辑
        with m.Switch(self.addr):
            with m.Case(0x00):  # 命令寄存器
                m.d.comb += self.data_out.eq(self.command_reg)
            with m.Case(0x04):  # 状态寄存器
                m.d.comb += self.data_out.eq(self.status_reg)
            # 添加其他可读寄存器
            with m.Default():
                m.d.comb += self.data_out.eq(0xFFFFFFFF)

        # 数据写入逻辑
        with m.If(self.we):
            with m.Switch(self.addr):
                with m.Case(0x00):  # 命令寄存器
                    m.d.sync += self.command_reg.eq(self.data_in)
                with m.Case(0x04):  # 状态寄存器
                    m.d.sync += self.status_reg.eq(self.data_in)
                # 添加其他可写寄存器
        # 若未写入，保持寄存器值不变

        return m