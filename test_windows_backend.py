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
            listener.return_value.is_alive.return_value=False
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
        with patch.object(backend,'CheckedMouse'),patch.object(backend,'CheckedKeyboard'):
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

    def test_focus_loss_blocks_inputs_and_tab_close_without_refocusing(self):
        player=self.player()
        player._target_window=123
        with patch.object(backend._user32,'GetForegroundWindow',return_value=456):
            with self.assertRaises(backend.TargetWindowChanged):
                player.apply_event(MacroEvent(0,LEFT_DOWN,x=10,y=20))
            with self.assertRaises(backend.TargetWindowChanged):
                player.close_tab()
        player._ctrl.press.assert_not_called()
        player._kbd.press.assert_not_called()

    def test_overlay_blocks_click_even_with_matching_pixels(self):
        player=self.player()
        player._target_window=123
        with patch.object(backend._user32,'GetForegroundWindow',return_value=123), \
                patch.object(backend._user32,'WindowFromPoint',return_value=456), \
                patch.object(backend._user32,'GetAncestor',return_value=456):
            with self.assertRaises(backend.TargetWindowChanged):
                player.wait_until_ready(MacroEvent(0,LEFT_DOWN),10,threading.Event())
        player._ctrl.press.assert_not_called()

    def test_stop_wins_over_matching_pixels_and_missing_snapshot(self):
        player=self.player()
        stop=threading.Event()
        stop.set()
        pixels=bytes([80])*40*40*4
        with patch.object(backend,'grab_region',return_value=pixels) as grab:
            for snap in ('',backend.encode_snap(pixels)):
                self.assertFalse(player.wait_until_ready(MacroEvent(0,LEFT_DOWN,snap=snap),10,stop))
        grab.assert_not_called()

    def test_lock_target_requires_foreground_window_at_first_click(self):
        player=self.player()
        def title(hwnd,buffer,size):
            buffer.value='Local test browser'
            return len(buffer.value)
        with patch.object(backend._user32,'GetForegroundWindow',return_value=123), \
                patch.object(backend._user32,'GetWindowTextW',side_effect=title), \
                patch.object(backend._user32,'WindowFromPoint',return_value=124), \
                patch.object(backend._user32,'GetAncestor',return_value=123):
            player.lock_target_window(MacroEvent(0,LEFT_DOWN,x=10,y=20))
        self.assertEqual(player._target_window,123)

    def test_lock_target_rejects_app_window(self):
        player=self.player()
        def title(hwnd,buffer,size):
            buffer.value='Mouse Macro Stocazz Superpower'
            return len(buffer.value)
        with patch.object(backend._user32,'GetForegroundWindow',return_value=123), \
                patch.object(backend._user32,'GetWindowTextW',side_effect=title):
            with self.assertRaises(backend.TargetWindowChanged):
                player.lock_target_window(MacroEvent(0,LEFT_DOWN))
        self.assertIsNone(player._target_window)

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

@unittest.skipUnless(sys.platform == 'win32', 'Windows native injection')
class InjectionFailureTests(unittest.TestCase):
    def test_failed_native_injection_is_visible(self):
        with patch.object(backend,'SendInput',return_value=0):
            with self.assertRaisesRegex(OSError,'non ha accettato'):
                backend.CheckedMouse().press(backend.mouse.Button.left)
    def test_failure_during_tab_switch_releases_both_keys(self):
        player=WindowsBackendTests().player()
        player._kbd.press.side_effect=[None,OSError('tab failed')]
        with self.assertRaises(OSError):
            player.next_tab(threading.Event())
        self.assertEqual(player._kbd.release.call_count,2)

    def test_failed_tab_release_still_releases_control(self):
        player=WindowsBackendTests().player()
        player._kbd.release.side_effect=[OSError('release failed'),None]
        with self.assertRaises(OSError):
            player.next_tab(threading.Event())
        self.assertEqual(player._kbd.release.call_count,2)

    def test_failed_button_release_still_attempts_remaining_buttons(self):
        player=WindowsBackendTests().player()
        player._held={'left','right'}
        player._ctrl.release.side_effect=[OSError('release failed'),None]
        with self.assertRaises(OSError):
            player.close()
        self.assertEqual(player._ctrl.release.call_count,2)
        self.assertEqual(len(player._held),1)

    def test_global_recording_accepts_desktop_other_apps_and_browser_toolbar(self):
        recorder = backend.WindowsRecorder(excluded_window=99, capture_snapshots=False)
        with patch.object(backend, 'window_rect', return_value=[800, 0, 1200, 700]), \
                patch.object(backend, 'browser_name', side_effect=AssertionError('No browser gate')), \
                patch.object(backend, 'root_at', side_effect=AssertionError('No window gate')):
            for x, y in ((100, 20), (200, 300), (400, 300)):
                recorder._on_click(x, y, backend.mouse.Button.left, True)
                recorder._on_click(x, y, backend.mouse.Button.left, False)
            recorder._on_scroll(400, 300, 0, -1)
            recorder._on_click(900, 300, backend.mouse.Button.left, True)
            recorder._on_click(900, 300, backend.mouse.Button.left, False)
        self.assertEqual([e.kind for e in recorder._events], [LEFT_DOWN, LEFT_UP]*3+[WHEEL])
        self.assertEqual(recorder.error, '')
        self.assertFalse(recorder._held_buttons)

    def test_recording_scroll_in_another_window_is_rejected(self):
        recorder=backend.WindowsRecorder(capture_snapshots=False,browser_only=True)
        with patch.object(backend,'root_at',return_value=2), \
                patch.object(backend._user32,'GetForegroundWindow',return_value=1):
            recorder._on_scroll(100,200,0,-1)
        self.assertEqual(recorder._events,[])
        self.assertIn('Chrome o Firefox',recorder.error)

    def test_wheel_only_recording_locks_layout(self):
        recorder=backend.WindowsRecorder(capture_snapshots=False,browser_only=True)
        layout={'dpi':96,'window_rect':[0,0,900,700]}
        with patch.object(backend,'root_at',return_value=1), \
                patch.object(backend._user32,'GetForegroundWindow',return_value=1), \
                patch.object(backend,'browser_name',return_value='Chrome'), \
                patch.object(backend,'window_rect',return_value=[0,0,900,700]), \
                patch.object(backend._user32,'GetDpiForWindow',return_value=96), \
                patch.object(backend,'browser_layout',return_value=layout):
            recorder._on_scroll(100,200,0,-1)
        self.assertEqual(recorder.target_window,1)
        self.assertEqual(recorder.layout,layout)
        self.assertEqual([e.kind for e in recorder._events],[WHEEL])
