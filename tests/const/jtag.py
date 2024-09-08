from enum import Enum
from cocotb.triggers import ClockCycles, Timer

# Instruction Register Encoding
class InstJTAG(Enum):
    EXTEST         = "0b0000"
    SAMPLE_PRELOAD = "0b1010"
    IC_RESET       = "0b1100"
    IDCODE         = "0b1110"
    BYPASS         = "0b1111"
    ADDR_AXI_REG   = "0b0001"
    DATA_W_AXI_REG = "0b0010"
    DATA_R_AXI_REG = "0b0011"
    CTRL_AXI_REG   = "0b0100"
    STATUS_AXI_REG = "0b0101"

# JTAG TAP Controller States
class JTAGState(Enum):
    TEST_LOGIC_RESET = 0
    RUN_TEST_IDLE = 1
    SELECT_DR_SCAN = 2
    CAPTURE_DR = 3
    SHIFT_DR = 4
    EXIT1_DR = 5
    PAUSE_DR = 6
    EXIT2_DR = 7
    UPDATE_DR = 8
    SELECT_IR_SCAN = 9
    CAPTURE_IR = 10
    SHIFT_IR = 11
    EXIT1_IR = 12
    PAUSE_IR = 13
    EXIT2_IR = 14
    UPDATE_IR = 15


# JTAG FSM Model
class JTAGFSM:
    def __init__(self):
        self.state = JTAGState.TEST_LOGIC_RESET

    @property
    def fsm(self):
        return self.state

    def reset(self):
        self.state = JTAGState.TEST_LOGIC_RESET

    def transition(self, tms):
        if self.state == JTAGState.TEST_LOGIC_RESET:
            if tms == 0:
                self.state = JTAGState.RUN_TEST_IDLE
        elif self.state == JTAGState.RUN_TEST_IDLE:
            if tms == 1:
                self.state = JTAGState.SELECT_DR_SCAN
        elif self.state == JTAGState.SELECT_DR_SCAN:
            if tms == 0:
                self.state = JTAGState.CAPTURE_DR
            else:
                self.state = JTAGState.SELECT_IR_SCAN
        elif self.state == JTAGState.CAPTURE_DR:
            if tms == 0:
                self.state = JTAGState.SHIFT_DR
            else:
                self.state = JTAGState.EXIT1_DR
        elif self.state == JTAGState.SHIFT_DR:
            if tms == 1:
                self.state = JTAGState.EXIT1_DR
        elif self.state == JTAGState.EXIT1_DR:
            if tms == 0:
                self.state = JTAGState.PAUSE_DR
            else:
                self.state = JTAGState.UPDATE_DR
        elif self.state == JTAGState.PAUSE_DR:
            if tms == 1:
                self.state = JTAGState.EXIT2_DR
        elif self.state == JTAGState.EXIT2_DR:
            if tms == 0:
                self.state = JTAGState.SHIFT_DR
            else:
                self.state = JTAGState.UPDATE_DR
        elif self.state == JTAGState.UPDATE_DR:
            if tms == 0:
                self.state = JTAGState.RUN_TEST_IDLE
            else:
                self.state = JTAGState.SELECT_DR_SCAN
        elif self.state == JTAGState.SELECT_IR_SCAN:
            if tms == 0:
                self.state = JTAGState.CAPTURE_IR
            else:
                self.state = JTAGState.TEST_LOGIC_RESET
        elif self.state == JTAGState.CAPTURE_IR:
            if tms == 0:
                self.state = JTAGState.SHIFT_IR
            else:
                self.state = JTAGState.EXIT1_IR
        elif self.state == JTAGState.SHIFT_IR:
            if tms == 1:
                self.state = JTAGState.EXIT1_IR
        elif self.state == JTAGState.EXIT1_IR:
            if tms == 0:
                self.state = JTAGState.PAUSE_IR
            else:
                self.state = JTAGState.UPDATE_IR
        elif self.state == JTAGState.PAUSE_IR:
            if tms == 1:
                self.state = JTAGState.EXIT2_IR
        elif self.state == JTAGState.EXIT2_IR:
            if tms == 0:
                self.state = JTAGState.SHIFT_IR
            else:
                self.state = JTAGState.UPDATE_IR
        elif self.state == JTAGState.UPDATE_IR:
            if tms == 0:
                self.state = JTAGState.RUN_TEST_IDLE
            else:
                self.state = JTAGState.SELECT_DR_SCAN
        else:
            self.state = JTAGState.TEST_LOGIC_RESET


# JTAG State Transitions - From TEST_LOGIC_RESET
JtagTrans = {
    JTAGState.TEST_LOGIC_RESET: [1, 1, 1, 1, 1],  # From any state
    JTAGState.RUN_TEST_IDLE: [0],  # From TEST_LOGIC_RESET  or other states
    JTAGState.SELECT_DR_SCAN: [0, 1],  # From RUN_TEST_IDLE
    JTAGState.CAPTURE_DR: [0, 1, 0],  # From SELECT_DR_SCAN
    JTAGState.SHIFT_DR: [0, 1, 0, 0],  # From CAPTURE_DR
    JTAGState.EXIT1_DR: [0, 1, 0, 1],  # From SHIFT_DR
    JTAGState.PAUSE_DR: [0, 1, 0, 1, 0],  # From EXIT1_DR
    JTAGState.EXIT2_DR: [0, 1, 0, 1, 0, 1],  # From PAUSE_DR
    JTAGState.UPDATE_DR: [0, 1, 0, 0, 1, 0, 1, 1],  # From EXIT2_DR or SHIFT_DR
    JTAGState.SELECT_IR_SCAN: [0, 1, 1, 0],  # From SELECT_DR_SCAN
    JTAGState.CAPTURE_IR: [0, 1, 1, 0],  # From SELECT_IR_SCAN
    JTAGState.SHIFT_IR: [0, 1, 1, 0, 0],  # From CAPTURE_IR
    JTAGState.EXIT1_IR: [0, 1, 1, 0, 1],  # From SHIFT_IR
    JTAGState.PAUSE_IR: [0, 1, 1, 0, 1, 0],  # From EXIT1_IR
    JTAGState.EXIT2_IR: [0, 1, 1, 0, 1, 0, 1],  # From PAUSE_IR
    JTAGState.UPDATE_IR: [0, 1, 1, 0, 1, 1],  # From EXIT2_IR or SHIFT_IR
}

async def reset_fsm(dut):
    dut._log.info(f"Reset JTAG FSM")
    dut.trstn.value = 0
    dut.tms.value = 0
    dut.tdi.value = 0
    dut.tck.value = 0
    await Timer(10, units="ns")
    dut.trstn.value = 1
    await Timer(2, units="ns")


async def update_tck(dut):
    dut.tck.value = 0
    await Timer(1, units="ns")
    dut.tck.value = 1
    await Timer(1, units="ns")


async def move_to_jtag_state(dut, state):
    tms = dut.tms

    transitions = JtagTrans[state]

    await reset_fsm(dut)

    for tms_value in transitions:
        dut.tms.value = tms_value
        await update_tck(dut)


async def select_instruction(dut, instr):
    dut._log.info(f"Setting up instr: {instr}")
    await move_to_jtag_state(dut, JTAGState.SHIFT_IR)

    for idx, tdi_val in enumerate(instr.value[2:][::-1]):
        dut.tdi.value = int(tdi_val)
        if idx == len(instr.value[2:]) - 1:
            break
        await update_tck(dut)

    dut.tms.value = 1
    await update_tck(dut)
    await update_tck(dut)
    dut.tms.value = 0
    await update_tck(dut)


async def move_to_shift_dr(dut, value):
    dut._log.info(f"Moving to shift DR")

    # Assuming we're on RUN_TEST_IDLE
    dut.tdi.value = 0
    dut.tms.value = 1
    await update_tck(dut)
    dut.tms.value = 0
    await update_tck(dut)
    dut.tms.value = 0
    await update_tck(dut)

    tdo = []
    for idx, tdi_val in enumerate(value[::-1]):
        dut.tdi.value = tdi_val

        if idx == len(value) - 1:
            break

        dut.tck.value = 0
        await Timer(1, units="ns")
        tdo.append(dut.tdo.value)
        dut.tck.value = 1
        await Timer(1, units="ns")

    dut.tms.value = 1

    dut.tck.value = 0
    await Timer(1, units="ns")
    tdo.append(dut.tdo.value)
    dut.tck.value = 1
    await Timer(1, units="ns")
    await update_tck(dut)
    dut.tms.value = 0
    await update_tck(dut)

    return tdo[::-1]
