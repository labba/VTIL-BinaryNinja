from binaryninja.log import log_info, log_error
from binaryninja.architecture import Architecture
from binaryninja.function import RegisterInfo, InstructionInfo, InstructionTextToken
from binaryninja.enums import InstructionTextTokenType, BranchType
from binaryninja.filemetadata import FileMetadata
from .parser import VTILParser
from .utils import to_string, find_instruction, find_block_address

# Still a horrible hack but better than files.
#
active_vtil_file = None

def set_active_vtil_file(vtil_struct):
    global active_vtil_file
    active_vtil_file = vtil_struct

class VTIL(Architecture):
    name = "VTIL"
    max_instr_length = 1
    stack_pointer = "$sp"

    regs = {
        "$sp" : RegisterInfo("$sp", 1)
    }

    instructions = {
        "str": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "str"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "["),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, "+"),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, "]"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
            ],
            "operands": [3, 5, 8]
        },
        "ldd": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "ldd"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ", ["),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, "+"),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, "]"),
            ],
            "operands": [2, 4, 6]
        },
        "te": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "te"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " == "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "tne": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "tne"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " != "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "tg": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "tg"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " > "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "tge": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "tge"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " >= "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "tl": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "tl"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " < "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "tle": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "tle"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " <= "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "tug": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "tug"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " u> "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "tuge": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "tuge"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " u>= "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "tul": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "tul"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " u< "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "tule": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "tule"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " := ("),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " u<= "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, ")")
            ],
            "operands": [2, 4, 6]
        },
        "ifs": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "ifs"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " := "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " ? "),
                InstructionTextToken(InstructionTextTokenType.TextToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " : "),
                InstructionTextToken(InstructionTextTokenType.IntegerToken, "0")
            ],
            "operands": [2, 4, 6]
        },
        "js": {
            "tokens": [
                InstructionTextToken(InstructionTextTokenType.InstructionToken, "js"),
                InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " ? "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN"),
                InstructionTextToken(InstructionTextTokenType.TextToken, " : "),
                InstructionTextToken(InstructionTextTokenType.RegisterToken, "UNKNOWN")
            ],
            "operands": [2, 4, 6]
        }
    }

    def get_instruction_info(self, data, addr):
        global active_vtil_file
        result = InstructionInfo()
        result.length = 1

        next_vip, _, _, _, code = find_instruction(addr, active_vtil_file)

        if code != None and code.startswith("js"):
            try:
                _, _, true, false = code.split(" ")
                true = find_block_address(int(true, 16), active_vtil_file)
                false = find_block_address(int(false, 16), active_vtil_file)
                result.add_branch(BranchType.TrueBranch, true)
                result.add_branch(BranchType.FalseBranch, false)
            except ValueError:
                v1 = find_block_address(next_vip[0], active_vtil_file)
                v2 = find_block_address(next_vip[1], active_vtil_file)
                result.add_branch(BranchType.UnconditionalBranch, v2)
                result.add_branch(BranchType.UnconditionalBranch, v1)
        elif code != None and code.startswith("vxcall"):
            addr = find_block_address(next_vip[0], active_vtil_file)
            result.add_branch(BranchType.UnconditionalBranch, addr)
        elif code != None and code.startswith("jmp"):
            if len(next_vip) == 1:
                addr = find_block_address(next_vip[0], active_vtil_file)
                result.add_branch(BranchType.UnconditionalBranch, addr)
            else:
                result.add_branch(BranchType.IndirectBranch)
                for vip in next_vip:
                    result.add_branch(BranchType.UnconditionalBranch, find_block_address(vip, active_vtil_file))
        elif code != None and code.startswith("vexit"):
            result.add_branch(BranchType.FunctionReturn)

        return result

    def get_instruction_text(self, data, addr):
        global active_vtil_file
        tokens = []

        next_vip, sp_index, sp_reset, sp_offset, code = find_instruction(addr, active_vtil_file)
        if code == None:
            tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, "ERROR"))
            return tokens, 1

        if sp_index > 0:
            tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, "["))
            tokens.append(InstructionTextToken(InstructionTextTokenType.IntegerToken, f"{int(sp_index):>2}", value=sp_index, size=64))
            tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, "] "))
        else:
            tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, "     "))

        prefix = "-"
        if sp_offset >= 0: prefix = "+"
        sp_offset = abs(sp_offset)

        if sp_reset > 0:
            txt = f">{prefix}{hex(sp_offset)}"
            txt = f"{txt:<6}"
            tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, txt))
        else:
            txt = f" {prefix}{hex(sp_offset)}"
            txt = f"{txt:<6}"
            tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, txt))
        tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, " "))

        
        if " " in code:
            instr, operands = code.split(" ", 1)

            if " " in operands:
                operands = operands.split(" ")
            else:
                operands = [operands]

            if instr in self.instructions.keys():
                token_set = self.instructions[instr]["tokens"]

                for index in self.instructions[instr]["operands"]:
                    operand = operands.pop(0)

                    if "0x" in operand:
                        if instr == "js":
                            token_set[index] = InstructionTextToken(InstructionTextTokenType.GotoLabelToken, f"vip_{operand[2:]}")
                        elif instr == "jmp":
                            token_set[index] = InstructionTextToken(InstructionTextTokenType.GotoLabelToken, f"vip_{hex(next_vip[0])[2:]}")
                        else:
                            token_set[index] = InstructionTextToken(InstructionTextTokenType.IntegerToken, operand, value=int(operand, 16), size=64)
                    else:
                        token_set[index] = InstructionTextToken(InstructionTextTokenType.RegisterToken, operand)
                
                tokens.extend(token_set)
            else:
                # fallback
                tokens.append(InstructionTextToken(InstructionTextTokenType.InstructionToken, instr))
                tokens.append(InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, " "))
                
                for operand in operands:
                    if "0x" in operand:
                        if instr == "jmp":
                            tokens.append(InstructionTextToken(InstructionTextTokenType.GotoLabelToken, f"vip_{hex(next_vip[0])[2:]}"))
                        else:
                            tokens.append(InstructionTextToken(InstructionTextTokenType.IntegerToken, operand, value=int(operand, 16), size=64))
                    else:
                        tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, operand))
                    tokens.append(InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "))
                
                tokens.pop()
        else:
            tokens.append(InstructionTextToken(InstructionTextTokenType.InstructionToken, code))
        
        return tokens, 1
        
    
    def get_instruction_low_level_il(self, data, addr, il):
        pass
