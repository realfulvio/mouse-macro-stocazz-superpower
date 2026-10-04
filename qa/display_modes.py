import ctypes as C,struct,json
u=C.windll.user32
modes=[]
for i in range(1000):
 b=C.create_string_buffer(220);struct.pack_into('H',b,68,220)
 if not u.EnumDisplaySettingsW(None,i,b):break
 mode=struct.unpack_from('III',b,168)
 if mode not in modes:modes.append(mode)
print(json.dumps(modes))
