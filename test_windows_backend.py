import threading
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

if sys.platform == 'win32':
    from macro import windows_backend as backend
from macro.events import (LEFT_DOWN,LEFT_UP,RIGHT_DOWN,RIGHT_UP,MIDDLE_DOWN,MIDDLE_UP,
                          MOVE_ABS,WHEEL,MacroEvent)


@unittest.skipUnless(sys.platform == 'win32', 'Windows native backend')
class WindowsBackendTests(unittest.TestCase):
    def test_recorded_movements_buttons_scroll_and_snapshots(self):
        recorder=backend.WindowsRecorder()
        pixels=bytes([50])*40*40*4
        with patch.object(backend.mouse,'Listener') as listener, \
                patch.object(backend,'grab_region',return_value=pixels), \
                patch.object(backend.time,'perf_counter',side_effect=[100,100.1,100.2,100.3,100.4,100.5,100.6,100.7]):
            recorder.start()
            recorder._on_move(-10,20)
            for button in (backend.mouse.Button.left,backend.mouse.Button.right,backend.mouse.Button.middle):
                recorder._on_click(-10,20,button,True)
                recorder._on_click(-10,20,button,False)
            recorder._on_scroll(-10,20,0,-2)
            events=recorder.stop()
        listener.return_value.start.assert_called_once()
        listener.return_value.stop.assert_called_once()
        self.assertEqual([e.kind for e in events],[MOVE_ABS,LEFT_DOWN,LEFT_UP,RIGHT_DOWN,RIGHT_UP,MIDDLE_DOWN,MIDDLE_UP,WHEEL])
        self.assertTrue(all(e.x==-10 and e.y==20 for e in events))
        self.assertEqual(events[-1].wheel,-2)
        self.assertEqual(backend.decode_snap(events[1].snap),pixels)
        self.assertTrue(all(events[i].snap for i in (1,3,5)))
        self.assertTrue(all(not events[i].snap for i in (0,2,4,6,7)))

    def player(self):
        with patch.object(backend.mouse,'Controller'),patch.object(backend.keyboard,'Controller'):
            return backend.WindowsPlayer()

    def test_playback_routes_positions_all_buttons_and_scroll(self):
        player=self.player()
        for down,up,button in ((LEFT_DOWN,LEFT_UP,backend.mouse.Button.left),
                               (RIGHT_DOWN,RIGHT_UP,backend.mouse.Button.right),
                               (MIDDLE_DOWN,MIDDLE_UP,backend.mouse.Button.middle)):
            player.apply_event(MacroEvent(0,down,x=123,y=456))
            player._ctrl.press.assert_called_with(button)
            player.apply_event(MacroEvent(.1,up,x=234,y=567))
            player._ctrl.release.assert_called_with(button)
            self.assertEqual(player._ctrl.position,(234,567))
        player.apply_event(MacroEvent(.2,MOVE_ABS,x=-10,y=20))
        self.assertEqual(player._ctrl.position,(-10,20))
        player.apply_event(MacroEvent(.3,WHEEL,x=-10,y=20,wheel=-2))
        player._ctrl.scroll.assert_called_once_with(0,-2)
        player.release_held({'left','right','middle'})
        self.assertEqual(player._ctrl.release.call_count,6)

    def test_page_ready_missing_snapshot_match_timeout_and_stop(self):
        player=self.player()
        pixels=bytes([50])*40*40*4
        event=MacroEvent(0,LEFT_DOWN,x=123,y=456,snap=backend.encode_snap(pixels))
        self.assertTrue(player.wait_until_ready(MacroEvent(0,LEFT_DOWN),0,threading.Event()))
        with patch.object(backend,'grab_region',return_value=pixels):
            self.assertTrue(player.wait_until_ready(event,1,threading.Event()))
        with patch.object(backend,'grab_region',return_value=bytes(len(pixels))):
            self.assertFalse(player.wait_until_ready(event,0,threading.Event()))
            stop=threading.Event()
            stop.set()
            self.assertFalse(player.wait_until_ready(event,10,stop))

    def test_page_wait_notifies_once_and_resumes_on_matching_pixels(self):
        player=self.player()
        pixels=bytes([80])*40*40*4
        event=MacroEvent(0,LEFT_DOWN,snap=backend.encode_snap(pixels))
        waiting=MagicMock()
        with patch.object(backend,'grab_region',side_effect=[bytes(len(pixels)),bytes(len(pixels)),pixels]), \
                patch.object(backend.time,'sleep'):
            self.assertTrue(player.wait_until_ready(event,1,threading.Event(),on_waiting=waiting))
        waiting.assert_called_once()

    def test_page_wait_ignores_surroundings_but_not_the_button(self):
        def snapshot(border,center):
            rows=[]
            for y in range(40):
                inside=8<=y<32
                rows.append(bytes([border])*8*4+bytes([center if inside else border])*24*4+bytes([border])*8*4)
            return b''.join(rows)
        recorded=snapshot(40,200)
        event=MacroEvent(0,LEFT_DOWN,snap=backend.encode_snap(recorded))
        player=self.player()
        # un altro cavallo: cornice diversa, stesso pulsante al centro
        with patch.object(backend,'grab_region',return_value=snapshot(230,200)):
            self.assertTrue(player.wait_until_ready(event,0,threading.Event()))
        # pagina non pronta: il pulsante al centro manca
        with patch.object(backend,'grab_region',return_value=snapshot(40,40)):
            self.assertFalse(player.wait_until_ready(event,0,threading.Event(),backend.TOLERANCE_LOOSE))
        self.assertEqual(len(backend.center_crop(recorded)),24*24*4)

    def test_close_tab_uses_ctrl_w_and_releases_key(self):
        player=self.player()
        with patch.object(backend.time,'sleep'):
            player.close_tab()
        player._kbd.pressed.assert_called_once_with(backend.keyboard.Key.ctrl)
        player._kbd.press.assert_called_once_with('w')
        player._kbd.release.assert_called_once_with('w')
        player._kbd.pressed.return_value.__exit__.assert_called_once()

    def test_global_hotkeys_registration_dispatch_and_cleanup(self):
        callback=MagicMock()
        hotkeys=backend.GlobalHotkeys(callback)
        user32=MagicMock()
        kernel32=MagicMock()
        kernel32.GetCurrentThreadId.return_value=123
        user32.RegisterHotKey.side_effect=[True,False,True]
        def get_message(message,*args):
            if callback.call_count:
                return 0
            message._obj.message=backend._WM_HOTKEY
            message._obj.wParam=backend.HOTKEY_EMERGENCY
            return 1
        user32.GetMessageW.side_effect=get_message
        with patch.object(backend.ctypes,'windll',SimpleNamespace(user32=user32,kernel32=kernel32)):
            hotkeys._run()
            hotkeys.stop()
        self.assertEqual(hotkeys.failed,['F10'])
        callback.assert_called_once_with(backend.HOTKEY_EMERGENCY)
        self.assertEqual(user32.UnregisterHotKey.call_count,2)
        user32.PostThreadMessageW.assert_called_once_with(123,backend._WM_QUIT,0,0)


if __name__=='__main__':
    unittest.main()
