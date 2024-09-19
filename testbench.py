# testbench.py

from amaranth import *
from amaranth.sim import Simulator, Settle, Tick

from pci_target import PCITarget
from pci_signals import PCISignals

def testbench():
    pci_target = PCITarget()

    sim = Simulator(pci_target)
    sim.add_clock(3e-7)  # 30 MHz 时钟

    # 定义测试程序的 AD_o 和 AD_oe 信号
    testbench_ad_o = Signal(32, reset=0)
    testbench_ad_oe = Signal(reset=0)

    # 定义共享的 AD 总线信号
    ad_bus = Signal(32, reset=0)

    def process():
        # 初始化信号
        yield pci_target.pci.RST_n.eq(1)
        yield pci_target.pci.CLK.eq(0)
        # 系统复位
        yield pci_target.pci.RST_n.eq(0)
        for _ in range(10):
            yield Tick()
        yield pci_target.pci.RST_n.eq(1)
        yield Settle()

        # 模拟一个IO Write事务
        yield pci_target.pci.FRAME_n.eq(0)
        yield pci_target.pci.IRDY_n.eq(1)  # 初始 IRDY_n 高

        # 地址阶段
        yield pci_target.pci.CBE.eq(0b0011)  # IO Write 命令
        yield testbench_ad_o.eq(0x00000000)  # 地址
        yield testbench_ad_oe.eq(1)          # 使能 AD 输出
        yield pci_target.pci.IRDY_n.eq(0)    # IRDY_n 置低，表示主设备准备好
        yield Tick()
        yield Settle()

        # 等待目标设备响应 DEVSEL_n
        while (yield pci_target.pci.DEVSEL_n):
            yield Tick()
            yield Settle()

        # 数据阶段 - 写数据
        yield testbench_ad_o.eq(0xDEADBEEF)
        yield Tick()
        yield Settle()

        # 完成事务
        yield pci_target.pci.FRAME_n.eq(1)
        yield pci_target.pci.IRDY_n.eq(1)
        yield testbench_ad_oe.eq(0)          # 释放 AD 总线
        yield Tick()
        yield Settle()

        # 模拟一个IO Read事务
        yield pci_target.pci.FRAME_n.eq(0)
        yield pci_target.pci.IRDY_n.eq(1)  # 初始 IRDY_n 高

        # 地址阶段
        yield pci_target.pci.CBE.eq(0b0010)  # IO Read 命令
        yield testbench_ad_o.eq(0x00000000)  # 地址
        yield testbench_ad_oe.eq(1)          # 使能 AD 输出
        yield pci_target.pci.IRDY_n.eq(0)    # IRDY_n 置低，表示主设备准备好
        yield Tick()
        yield Settle()

        # 地址阶段结束，释放 AD 总线
        yield testbench_ad_oe.eq(0)          # 禁止 AD 输出
        yield Tick()
        yield Settle()

        # 等待目标设备响应 DEVSEL_n 和 TRDY_n
        while (yield pci_target.pci.DEVSEL_n) or (yield pci_target.pci.TRDY_n):
            yield Tick()
            yield Settle()

        # 数据阶段 - 读取数据
        data = yield ad_bus
        print(f"Read Data: 0x{data:08X}")

        # 完成事务
        yield pci_target.pci.FRAME_n.eq(1)
        yield pci_target.pci.IRDY_n.eq(1)
        yield Tick()
        yield Settle()

    def ad_bus_logic():
        while True:
            # 默认情况下，无人驱动时，ad_value 为全 1
            ad_value = 0xFFFFFFFF

            if (yield pci_target.pci.AD_oe):
                ad_value = (yield pci_target.pci.AD_o)
            elif (yield testbench_ad_oe):
                ad_value = (yield testbench_ad_o)
            else:
                ad_value = 0xFFFFFFFF  # 无人驱动时，假设为全 1

            # 更新共享总线和 PCI 目标设备的 AD_i
            yield ad_bus.eq(ad_value)
            yield pci_target.pci.AD_i.eq(ad_value)
            yield

    sim.add_sync_process(process)
    sim.add_sync_process(ad_bus_logic)

    with sim.write_vcd("pci_target.vcd"):
        sim.run()

if __name__ == "__main__":
    testbench()