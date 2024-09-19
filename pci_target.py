# pci_target.py

from amaranth import *

from pci_signals import PCISignals
from pci_config_space import PCIConfigSpace
from command_status import CommandStatus

class PCITarget(Elaboratable):
    def __init__(self):
        # PCI总线信号
        self.pci = PCISignals()

        # 内部模块
        self.config_space = PCIConfigSpace()
        self.cmd_status = CommandStatus()

    def elaborate(self, platform):
        m = Module()

        m.submodules.config_space = self.config_space
        m.submodules.cmd_status = self.cmd_status

        # PCI总线信号拉高（默认空闲状态）
        m.d.comb += [
            self.pci.TRDY_n.eq(1),
            self.pci.DEVSEL_n.eq(1),
            self.pci.STOP_n.eq(1),
            self.pci.AD_oe.eq(0),    # 默认不驱动 AD 总线
        ]

        # 状态机状态定义
        IDLE = 0
        DECODE = 1
        IO_READ = 2
        IO_WRITE = 3

        state = Signal(2, reset=IDLE)

        # 地址、命令寄存器
        addr_reg = Signal(32)
        cmd_reg = Signal(4)

        # 设备准备信号（用于延迟 TRDY_n 的断言）
        device_ready = Signal(reset=0)

        with m.FSM(domain="sync"):
            with m.State("IDLE"):
                # 等待 FRAME_n 和 IRDY_n 同时有效，表示事务的开始
                with m.If(~self.pci.FRAME_n & ~self.pci.IRDY_n):
                    m.d.sync += [
                        addr_reg.eq(self.pci.AD_i),
                        cmd_reg.eq(self.pci.CBE),
                    ]
                    # 判断事务类型，进入解码状态
                    with m.If((self.pci.CBE == 0b0010) | (self.pci.CBE == 0b0011)):
                        m.next = "DECODE"
                # 保持在 IDLE 状态

            with m.State("DECODE"):
                # 选中设备，断言 DEVSEL_n
                m.d.comb += [
                    self.pci.DEVSEL_n.eq(0),
                ]
                # 模拟设备准备时间，下一周期准备好
                m.d.sync += device_ready.eq(1)
                # 根据命令进入相应的状态
                with m.If(cmd_reg == 0b0010):
                    m.next = "IO_READ"
                with m.Elif(cmd_reg == 0b0011):
                    m.next = "IO_WRITE"

            with m.State("IO_READ"):
                m.d.comb += [
                    self.pci.DEVSEL_n.eq(0),
                ]
                with m.If(device_ready):
                    m.d.comb += [
                        self.pci.TRDY_n.eq(0),    # 准备好数据
                        self.cmd_status.addr.eq(addr_reg[2:6]),
                        self.cmd_status.re.eq(1),
                        self.pci.AD_o.eq(self.cmd_status.data_out),
                        self.pci.AD_oe.eq(1),
                    ]
                    # 等待主设备准备好接收数据
                    with m.If(~self.pci.IRDY_n):
                        # 等待事务结束
                        with m.If(self.pci.FRAME_n & self.pci.IRDY_n):
                            m.d.sync += device_ready.eq(0)
                            m.next = "IDLE"
                # 否则，等待设备准备好

            with m.State("IO_WRITE"):
                m.d.comb += [
                    self.pci.DEVSEL_n.eq(0),
                ]
                with m.If(device_ready):
                    m.d.comb += [
                        self.pci.TRDY_n.eq(0),    # 准备好接收数据
                        self.cmd_status.addr.eq(addr_reg[2:6]),
                    ]
                    # 等待主设备提供数据
                    with m.If(~self.pci.IRDY_n):
                        m.d.sync += [
                            self.cmd_status.data_in.eq(self.pci.AD_i),
                        ]
                        m.d.comb += [
                            self.cmd_status.we.eq(1),
                        ]
                        # 等待事务结束
                        with m.If(self.pci.FRAME_n & self.pci.IRDY_n):
                            m.d.sync += device_ready.eq(0)
                            m.next = "IDLE"
                # 否则，等待设备准备好

        return m