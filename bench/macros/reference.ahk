#Requires AutoHotkey v2.0
CoordMode 'Mouse', 'Screen'
SendMode 'Input'
start := 0
DllCall('QueryPerformanceFrequency', 'Int64*', &f := 0)
DllCall('QueryPerformanceCounter', 'Int64*', &q0 := 0)
Wait(t) {
  global f, q0
  loop {
    DllCall('QueryPerformanceCounter', 'Int64*', &q := 0)
    r := t - (q - q0) / f
    if r <= 0
      return
    if r > 0.003
      Sleep(1)
  }
}
F8::{
  global q0
  DllCall('QueryPerformanceCounter', 'Int64*', &q0)
  Wait(0.0)
  MouseMove 288, 216, 0
  Click 'Down'
  Wait(0.15)
  MouseMove 288, 216, 0
  Click 'Up'
  Wait(1.05)
  MouseMove 730, 216, 0
  Click 'Down'
  Wait(1.2)
  MouseMove 730, 216, 0
  Click 'Up'
  Wait(2.1)
  MouseMove 1171, 216, 0
  Click 'Down'
  Wait(2.25)
  MouseMove 1171, 216, 0
  Click 'Up'
  Wait(3.15)
  MouseMove 1613, 216, 0
  Click 'Down'
  Wait(3.3)
  MouseMove 1613, 216, 0
  Click 'Up'
  Wait(4.2)
  MouseMove 288, 540, 0
  Click 'Down'
  Wait(4.35)
  MouseMove 288, 540, 0
  Click 'Up'
  Wait(5.25)
  MouseMove 730, 540, 0
  Click 'Down'
  Wait(5.4)
  MouseMove 730, 540, 0
  Click 'Up'
  Wait(6.3)
  MouseMove 1171, 540, 0
  Click 'Down'
  Wait(6.45)
  MouseMove 1171, 540, 0
  Click 'Up'
  Wait(7.35)
  MouseMove 1613, 540, 0
  Click 'Down'
  Wait(7.5)
  MouseMove 1613, 540, 0
  Click 'Up'
  Wait(8.4)
  MouseMove 288, 864, 0
  Click 'Down'
  Wait(8.55)
  MouseMove 288, 864, 0
  Click 'Up'
  Wait(9.45)
  MouseMove 730, 864, 0
  Click 'Down'
  Wait(9.6)
  MouseMove 730, 864, 0
  Click 'Up'
  Wait(10.5)
  MouseMove 1171, 864, 0
  Click 'Down'
  Wait(10.65)
  MouseMove 1171, 864, 0
  Click 'Up'
  Wait(11.55)
  MouseMove 1613, 864, 0
  Click 'Down'
  Wait(11.7)
  MouseMove 1613, 864, 0
  Click 'Up'
  Wait(12.6)
  MouseMove 288, 216, 0
  Click 'Down'
  Wait(13.6)
  MouseMove 1613, 864, 0
  Click 'Up'
  Wait(14.5)
  MouseMove 730, 540, 0
  Click 'WheelDown'
  Wait(15.4)
  MouseMove 730, 540, 0
  Click 'WheelDown'
  Wait(16.3)
  MouseMove 730, 540, 0
  Click 'WheelDown'
}
F12::ExitApp