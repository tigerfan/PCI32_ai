# pci_config_space.py

from amaranth import *

class PCIConfigSpace(Elaboratable):
    def __init__(self):
        # 输入信号
        self.addr = Signal(8)  # 配置空间地址，偏移量
        self.data_in = Signal(32)
        self.we = Signal()     # 写使能
        self.re = Signal()     # 读使能

        # 输出信号
        self.data_out = Signal(32)

        # 配置空间寄存器
        self.vendor_id = Signal(16, reset=0x1234)
        self.device_id = Signal(16, reset=0x5678)
        self.command = Signal(16, reset=0x0000)
        self.status = Signal(16, reset=0x0200)  # 副版本号：0x02
        self.revision_id = Signal(8, reset=0x01)
        self.class_code = Signal(24, reset=0x000000)
        self.cache_line_size = Signal(8, reset=0x00)
        self.latency_timer = Signal(8, reset=0x00)
        self.header_type = Signal(8, reset=0x00)
        self.bist = Signal(8, reset=0x00)
        self.base_address_registers = Array(Signal(32) for _ in range(6))
        # 更多的寄存器可以根据需要添加

    def elaborate(self, platform):
        m = Module()

        read_data = Signal(32)

        with m.Switch(self.addr):
            with m.Case(0x00):  # Vendor ID and Device ID
                m.d.comb += read_data.eq(Cat(self.vendor_id, self.device_id))
            with m.Case(0x04):  # Command and Status
                m.d.comb += read_data.eq(Cat(self.command, self.status))
            with m.Case(0x08):  # Revision ID and Class Code
                m.d.comb += read_data.eq(Cat(self.revision_id, self.class_code))
            with m.Case(0x0C):  # Cache Line Size, Latency Timer, Header Type, BIST
                m.d.comb += read_data.eq(Cat(self.cache_line_size, self.latency_timer, self.header_type, self.bist))
            # 可以继续添加其他寄存器的处理
            with m.Default():
                m.d.comb += read_data.eq(0xFFFFFFFF)  # 未实现的寄存器返回全1

        with m.If(self.we):
            # 处理写操作，可以根据需要实现写使能的寄存器
            with m.Switch(self.addr):
                with m.Case(0x04):  # Command 寄存器
                    m.d.sync += self.command.eq(self.data_in[:16])
                # 添加其他可写寄存器的处理
        with m.Elif(self.re):
            m.d.sync += self.data_out.eq(read_data)

        return m