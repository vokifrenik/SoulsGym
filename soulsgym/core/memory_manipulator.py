"""Low level memory manipulation interface."""
from __future__ import annotations
import ctypes
from typing import List

import psutil
import win32process
import win32api
import win32con
import pymem as pym
from pymem import Pymem

from soulsgym.core.utils import Singleton

BASES = {
    "A": 0x4740178,
    "B": 0x4768E78,
    "C": 0x4743AB0,
    "D": 0x4743A80,
    "GameFlagData": 0x473BE28,
    "GlobalSpeed": 0x999C28,
    "LockOn": 0x0474C2F8,
    "Cam": 0x47809C8,
    "LockOnParam": 0x4766CA0,
    "IudexA": 0x04743668,
    "IudexC": 0x04739958,
    "PlayerDisabled": 0x7FF48EECCA79,
    "DebugFlags": 0x4768F68,
}

VALUE_ADDRESS_OFFSETS = {
    "PlayerHP": [0x80, 0x1F90, 0x18, 0xD8],
    "PlayerMaxHP": [0x80, 0x1F90, 0x18, 0xDC],
    "PlayerSP": [0x80, 0x1F90, 0x18, 0xF0],
    "PlayerMaxSP": [0x80, 0x1F90, 0x18, 0xF4],
    "SoulLevel": [0x10, 0x70],
    "Vigor": [0x10, 0x44],
    "Attunement": [0x10, 0x48],
    "Endurance": [0x10, 0x4C],
    "Vitality": [0x10, 0x6C],
    "Strength": [0x10, 0x50],
    "Dexterity": [0x10, 0x54],
    "Intelligence": [0x10, 0x58],
    "Faith": [0x10, 0x5C],
    "Luck": [0x10, 0x60],
    "TargetAttack": [0x1EE8],
    "TargetFreeze": [0x18, 0x20],
    "IudexDefeated": [0x0, 0x5A67],  # Bit 7 saves the defeat flag!
    "TargetedHP": [0x1F90, 0x18, 0xD8],
    "TargetedMaxHP": [0x1F90, 0x18, 0xE0],
    "PlayerX": [0x40, 0x28, 0x80],
    "PlayerY": [0x40, 0x28, 0x88],
    "PlayerZ": [0x40, 0x28, 0x84],
    "PlayerA": [0x40, 0x28, 0x74],
    "PlayerAnimation": [0x80, 0x1F90, 0x28, 0x898],
    "TargetX": [0x1F90, 0x68, 0xa8, 0x40, 0x70],
    "TargetY": [0x1F90, 0x68, 0xa8, 0x40, 0x78],
    "TargetZ": [0x1F90, 0x68, 0xa8, 0x40, 0x74],
    "TargetA": [0x1F90, 0x68, 0xa8, 0x40, 0x7C],
    "TargetXUpdate": [0x1F90, 0x68, 0x80],
    "TargetYUpdate": [0x1F90, 0x68, 0x88],
    "TargetZUpdate": [0x1F90, 0x68, 0x84],
    "TargetAUpdate": [0x1F90, 0x68, 0x8C],
    "TargetedAnimation": [0x1F90, 0x28, 0x898],
    "PlayerSpeedMod": [0x80, 0x1F90, 0x28, 0xA58],
    "LockedOnFlag": [0x70],
    "CamQ1": [0x10, 0x568, 0x108],
    "CamQ2": [0x10, 0x568, 0x110],
    "CamQ3": [0x10, 0x568, 0x114],
    "CamQ4": [0x10, 0x568, 0x118],
    "CameraX": [0x18, 0x0568, 0x120],
    "CameraY": [0x18, 0x0568, 0x128],
    "CameraZ": [0x18, 0x0568, 0x124],
    "LoSLockOnTime": [0x2910],
    "LockOnBonusRange": [0x2914],
    "noGravity": [0x80, 0x1a08],  # Bit 6 saves the gravity flag!
    "IudexHP": [0x0, 0x320, 0x0, 0x1F90, 0x18, 0xD8],
    "IudexAnimation": [0x0, 0x320, 0x0, 0x1B00, 0x38, 0x898],
    "IudexPoseX": [0x0, 0x320, 0x0, 0x1F90, 0x68, 0x80],
    "IudexPoseY": [0x0, 0x320, 0x0, 0x1F90, 0x68, 0x88],
    "IudexPoseZ": [0x0, 0x320, 0x0, 0x1F90, 0x68, 0x84],
    "IudexPoseA": [0x0, 0x320, 0x0, 0x1F90, 0x68, 0x74],
    "IudexAttacks": [0x0, 0x320, 0x0, 0x1EE8],
    "LockOn": [0x24B0],
    "LastBonfire": [0xACC],
    "PlayerNoDeath": [0x0],
    "PlayerDeathCount": [0x98],
}

# Iudex HP: 1F90 18 D8

TARGETED_ENTITY_CODE_POS = 0x85a74a
TARGETED_ENTITY_OLD_CODE = b"\x48\x8b\x80\x90\x1f\x00\x00"

# Docs: https://docs.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-VIRTUAL_ALLOC
VIRTUAL_ALLOC = ctypes.windll.kernel32.VirtualAlloc
VIRTUAL_ALLOC.argtypes = [
    ctypes.wintypes.LPVOID, ctypes.c_ulonglong, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD
]
VIRTUAL_ALLOC.restype = ctypes.c_ulonglong

# currently not needed
# VirtualFree = ctypes.windll.kernel32.VirtualFree
# VirtualFree.restype = ctypes.wintypes.BOOL
# VirtualFree.argtypes = [ ctypes.wintypes.LPVOID, ctypes.c_ulonglong, ctypes.wintypes.DWORD ]


class MemoryManipulator(Singleton):
    """Handle the memory manipulation of the game.

    At heart this class wraps pymem functions for memory read and writes. For better useability it
    manages the game memory pointers, address resolving and decoding.
    """

    def __init__(self, process_name: str = "DarkSoulsIII.exe"):
        """Initialize the cache and pointer attributes.

        If the game is not open, the pointer values can't be inferred which causes an exception.

        Args:
            process_name: The target process name. Should always be DarkSoulsIII.exe, unless the app
                name changes.
        """
        if not hasattr(self, "is_init"):
            self.process_name = process_name
            self.pid = self.get_pid(self.process_name)
            # Get the base address
            self.process_handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, self.pid)
            modules = win32process.EnumProcessModules(self.process_handle)
            self.base_address = modules[0]
            # Create Pymem object once, this has a relative long initialziation
            self.pymem = Pymem()
            self.pymem.open_process_from_id(self.pid)
            self.cache = {}

    def clear_cache(self):
        """Clear the reference look-up cache of the memory manipulator."""
        self.cache = {}

    @staticmethod
    def get_pid(process_name: str) -> int:
        """Fetch the process PID of a process identified by a given name.

        Args:
            process_name: The name of the process to get the PID from.

        Returns:
            The process PID.

        Raises:
            RuntimeError: No process with name `process_name` currently open.
        """
        for proc in psutil.process_iter():
            if proc.name() == process_name:
                return proc.pid
        raise RuntimeError(f"Process {process_name} not open")

    def resolve_address(self, addr_offsets: List[int], base: int) -> int:
        """Resolve an address by its offsets and a base.

        Looks up the cache first.

        Warning:
            Can't detect an invalid cache, this is the user's responsibility!

        Args:
            addr_offsets: The offsets which will be resolved iteratively. The first offset is the
            offset to the base itself.
            base: The base offset from the start of the program's memory.

        Returns:
            The resolved address.

        Raises:
            pym.exception.MemoryReadError: An error with the memory read occured.
        """
        u_id = str((addr_offsets, base))
        # Look up the cache
        if u_id in self.cache:
            return self.cache[u_id]
        # When no cache hit: resolve by following the pointer chain until its last link
        helper = self.pymem.read_longlong(base)
        for o in addr_offsets[:-1]:
            helper = self.pymem.read_longlong(helper + o)
        helper += addr_offsets[-1]
        # Add to cache
        self.cache[u_id] = helper
        return helper

    def read_int(self, address: int) -> int:
        """Read an integer from memory.

        Args:
            address: The address to be looked into.

        Returns:
            The integer value.

        Raises:
            pym.exception.MemoryReadError: An error with the memory read occured.
        """
        return self.pymem.read_long(address)

    def read_float(self, address: int) -> float:
        """Read a float from memory.

        Args:
            address: The address to be looked into.

        Returns:
            The float value.

        Raises:
            pym.exception.MemoryReadError: An error with the memory read occured.
        """
        return self.pymem.read_float(address)

    def read_string(self,
                    address: int,
                    length: int,
                    null_term: bool = True,
                    codec: str = "utf-16") -> str:
        """Read a string from memory.

        Args:
            address: The address to be looked into.
            length: The expected (maximum) string length.
            null_term: Whether the string shall be cut after double 0x00.
            codec: The codec used to decode the bytes.

        Returns:
            The string.

        Raises:
            pym.exception.MemoryReadError: An error with the memory read occured.
            UnicodeDecodeError: An error with the decoding of the read bytes occured.
        """
        s = self.pymem.read_bytes(address, length)
        if null_term:
            pos = 0
            for i in range(1, length, 2):
                if s[i - 1] == 0x00 and s[i] == 0x00:
                    pos = i
                    break
            s = s[:pos - 1]
            if not pos:
                s = s + bytes(1)  # Add null termination for strings which exceed 20 chars.
        return s.decode(codec)

    def read_bytes(self, address: int, length: int) -> bytes:
        """Read raw bytes from memory.

        Args:
            address: The address to be looked into.
            length: The amount of bytes that should be read.

        Returns:
            The raw bytes.

        Raises:
            pym.exception.MemoryReadError: An error with the memory read occured.
        """
        return self.pymem.read_bytes(address, length)

    def write_bit(self, address: int, index: int, value: int):
        """Write a single bit.

        Args:
            address: The address to be written into.
            index: The index of the bit (0 ... 7).
            value: The value of the bit (0/1).

        Raises:
            pym.exception.MemoryWriteError: An error with the memory write occured.
        """
        byte = self.read_bytes(address, 1)
        mask = (1 << index).to_bytes(1, "little")
        byte = (byte[0] & ~mask[0]).to_bytes(1, "little")
        if value:
            byte = (byte[0] | mask[0]).to_bytes(1, "little")
        self.write_bytes(address, byte)

    def write_int(self, address: int, value: int):
        """Write an integer to memory.

        Args:
            address: The address to be written into.
            value: The value of the integer.

        Raises:
            pym.exception.MemoryWriteError: An error with the memory write occured.
        """
        pym.memory.write_long(self.pymem.process_handle, address, value)

    def write_float(self, address: int, value: float):
        """Write a float to memory.

        Args:
            address: The address to be written into.
            value: The value of the float.

        Raises:
            pym.exception.MemoryWriteError: An error with the memory write occured.
        """
        pym.memory.write_float(self.pymem.process_handle, address, value)

    def write_bytes(self, address: int, buffer: bytes):
        """Write a series of bytes to memory.

        Args:
            address: The first address to be written into.
            buffer: The bytes to write.

        Raises:
            pym.exception.MemoryWriteError: An error with the memory write occured.
        """
        pym.memory.write_bytes(self.pymem.process_handle, address, buffer, len(buffer))
