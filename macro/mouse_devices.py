"""Read installed Windows mouse names through SetupAPI and Configuration Manager."""
import ctypes as C
from ctypes import wintypes as W
import sys
import uuid


class GUID(C.Structure):
    _fields_ = [('data', C.c_ubyte * 16)]

    @classmethod
    def parse(cls, value):
        return cls((C.c_ubyte * 16).from_buffer_copy(uuid.UUID(value).bytes_le))


class DEVPROPKEY(C.Structure):
    _fields_ = [('guid', GUID), ('pid', W.DWORD)]


class DEVICE_INFO(C.Structure):
    _fields_ = [('size', W.DWORD), ('class_guid', GUID),
                ('device', W.DWORD), ('reserved', C.c_size_t)]


def _device_names():
    if sys.platform != 'win32':
        return []
    setup = C.WinDLL('setupapi', use_last_error=True)
    config = C.WinDLL('cfgmgr32')
    setup.SetupDiGetClassDevsW.argtypes = [C.POINTER(GUID), W.LPCWSTR, W.HWND, W.DWORD]
    setup.SetupDiGetClassDevsW.restype = W.HANDLE
    setup.SetupDiEnumDeviceInfo.argtypes = [W.HANDLE, W.DWORD, C.POINTER(DEVICE_INFO)]
    setup.SetupDiEnumDeviceInfo.restype = W.BOOL
    setup.SetupDiDestroyDeviceInfoList.argtypes = [W.HANDLE]
    setup.SetupDiDestroyDeviceInfoList.restype = W.BOOL
    config.CM_Get_DevNode_PropertyW.argtypes = [W.DWORD, C.POINTER(DEVPROPKEY),
        C.POINTER(W.DWORD), C.c_void_p, C.POINTER(W.DWORD), W.DWORD]
    config.CM_Get_DevNode_PropertyW.restype = W.DWORD
    config.CM_Get_Parent.argtypes = [C.POINTER(W.DWORD), W.DWORD, W.DWORD]
    config.CM_Get_Parent.restype = W.DWORD
    mouse_class = GUID.parse('4d36e96f-e325-11ce-bfc1-08002be10318')
    properties = GUID.parse('a45c254e-df1c-4efd-8020-67d146a850e0')
    bus_description = DEVPROPKEY(GUID.parse('540b947e-8b40-45bc-a8a2-6a0b894cbda2'), 4)

    def property_text(device, key):
        value = C.create_unicode_buffer(1024)
        size, kind = W.DWORD(C.sizeof(value)), W.DWORD()
        status = config.CM_Get_DevNode_PropertyW(device, C.byref(key), C.byref(kind),
                                                value, C.byref(size), 0)
        return value.value if status == 0 and kind.value == 0x12 else ''

    handle = setup.SetupDiGetClassDevsW(C.byref(mouse_class), None, None, 2)  # present devices
    if handle == W.HANDLE(-1).value:
        return []
    names = []
    try:
        index = 0
        while True:
            info = DEVICE_INFO(); info.size = C.sizeof(info)
            if not setup.SetupDiEnumDeviceInfo(handle, index, C.byref(info)):
                break
            index += 1
            name = (property_text(info.device, DEVPROPKEY(properties, 14)) or
                    property_text(info.device, DEVPROPKEY(properties, 2)))
            device = info.device
            for _ in range(3):
                description = property_text(device, bus_description)
                generic = ('usb input device', 'hid-compliant mouse', 'usb composite device')
                if (description and description.lower() not in generic and
                        not any(word in description.lower() for word in ('keyboard', 'tastiera', 'hub'))):
                    name = description
                    break
                parent = W.DWORD()
                if config.CM_Get_Parent(C.byref(parent), device, 0) != 0:
                    break
                enumerator = property_text(parent.value, DEVPROPKEY(properties, 24))
                if not enumerator.lower().startswith(('usb', 'hid', 'bth')):
                    break  # a PS/2 controller or PCI bus is not the mouse model
                device = parent.value
            if name:
                names.append(name)
    finally:
        setup.SetupDiDestroyDeviceInfoList(handle)
    return names


def mouse_names():
    """Unavailable driver metadata must never prevent recording or playback."""
    try:
        values = _device_names()
        names = list(dict.fromkeys(' '.join(value.split()) for value in values
                                  if isinstance(value, str) and value.strip()))
        return sorted(names, key=lambda name: 'hid' in name.lower() or 'ps/2' in name.lower())
    except (OSError, ValueError):
        return []


def mouse_label(names):
    if not names:
        return 'Mouse: modello non disponibile'
    if len(names) == 1:
        return 'Mouse: ' + names[0]
    return f'Mouse rilevati: {names[0]} (+{len(names)-1})'
