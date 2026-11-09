"""Preflight the workbook without attaching to or closing a user's Excel session."""
import os
from pathlib import Path

EXCEL_IN_USE='Excel está abierto o se está abriendo. Guarda y cierra el libro del experimento antes de actualizar y exportar.'
class WorkbookInUseError(RuntimeError):pass

def assert_available(path):
    path=Path(path)
    if os.name!='nt':return
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    create=kernel.CreateFileW;create.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];create.restype=wintypes.HANDLE
    close=kernel.CloseHandle;close.argtypes=[wintypes.HANDLE];close.restype=wintypes.BOOL
    handle=create(str(path.resolve()),0x80000000,0,None,3,0x80,None)
    if handle==wintypes.HANDLE(-1).value:
        code=ctypes.get_last_error()
        if code in (32,33):raise WorkbookInUseError(EXCEL_IN_USE)
        raise ctypes.WinError(code)
    close(handle)
