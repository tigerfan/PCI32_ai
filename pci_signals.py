# pci_signals.py

from amaranth import *

class PCISignals(Record):
    def __init__(self):
        super().__init__([
            # 32位地址和数据，拆分为输入和输出以及输出使能
            ("AD_i", 32),   # AD 输入
            ("AD_o", 32),   # AD 输出
            ("AD_oe", 1),   # AD 输出使能
            # 命令/字节使能
            ("CBE", 4),
            # 控制信号
            ("FRAME_n", 1),
            ("IRDY_n", 1),
            ("TRDY_n", 1),
            ("DEVSEL_n", 1),
            ("IDSEL", 1),
            ("PAR", 1),
            # 仲裁信号
            ("REQ_n", 1),
            ("GNT_n", 1),
            ("RST_n", 1),
            ("CLK", 1),
            # 其他信号
            ("STOP_n", 1),
            ("LOCK_n", 1),
            ("PERR_n", 1),
            ("SERR_n", 1),
        ])