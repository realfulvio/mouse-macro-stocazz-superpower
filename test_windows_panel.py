"""Native panel policy tests. Real desktop acceptance is a separate step."""
import sys
import queue
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

if sys.platform == 'win32':
    import windows_main as ui
    from macro.events import Macro, MacroEvent, LEFT_DOWN, LEFT_UP, MOVE_ABS, WHEEL


@unittest.skipUnless(sys.platform == 'win32', 'Native Windows panel')
class PanelTests(unittest.TestCase):
    def panel(self):
        p = ui.Panel.__new__(ui.Panel)
        p.hwnd = 123
        p.dpi = 96
        p.exstyle = 0x08040008
        p.expanded = False
        p.active_view = False
        p.active_position = None
        p.normal_position = None
        p.last_view = None
        p.controls = {22:222}
        p.repeats = 1
        p.clamp = lambda x,y,w,h: (max(-1920,min(x,-w)),max(0,min(y,1080-h)))
        p.active_work_area = lambda: SimpleNamespace(left=-1920,right=0,top=0,bottom=1080)
        def layout(dpi):
            p.width,p.height = ui.ACTIVE_SIZE if p.active_view else (640,608) if p.expanded else (340,600)
        p.layout = layout
        return p

    def test_edit_creation_notification_before_handle_assignment_is_ignored(self):
        p=self.panel();p.controls={};p.session=SimpleNamespace(state=ui.State.READY)
        p.read_repeats=MagicMock(side_effect=AssertionError('Handle not assigned yet'))
        self.assertEqual(p.wndproc(123,ui.WM_COMMAND,(0x300<<16)|22,456),0)
        p.read_repeats.assert_not_called()

    def test_edit_update_notification_does_not_read_count(self):
        p=self.panel();p.session=SimpleNamespace(state=ui.State.READY)
        p.read_repeats=MagicMock(side_effect=AssertionError('Only change/focus notifications matter'))
        self.assertEqual(p.wndproc(123,ui.WM_COMMAND,(0x400<<16)|22,222),0)
        p.read_repeats.assert_not_called()

    def test_invalid_count_losing_focus_is_not_replaced_with_last_valid_count(self):
        p=self.panel();p.session=SimpleNamespace(state=ui.State.READY,error=MagicMock())
        p.read_repeats=MagicMock(side_effect=ValueError('Imposta da 1 a 999 ripetizioni.'))
        p.sync_repeats=MagicMock()
        p.wndproc(123,ui.WM_COMMAND,(0x200<<16)|22,222)
        p.sync_repeats.assert_not_called()
        p.session.error.assert_called_once()

    def test_count_accepts_any_integer_one_through_999(self):
        for n in range(1,1000):
            self.assertEqual(ui.parse_repeats(str(n)),n)
        self.assertEqual(ui.parse_repeats(' 20 '),20)

    def test_click_repeat_input_explicitly_activates_and_focuses_edit(self):
        for state in (ui.State.READY, ui.State.ERROR):
            p=self.panel();p.session=SimpleNamespace(state=state)
            with patch.object(ui,'U') as u:
                u.WindowFromPoint.return_value=222
                self.assertEqual(p.wndproc(123,0x21,123,0),3)
                self.assertEqual(u.method_calls[-2:],[
                    unittest.mock.call.SetForegroundWindow(123),
                    unittest.mock.call.SetFocus(222)])

    def test_other_controls_and_active_session_do_not_activate_panel(self):
        for state,target in ((ui.State.READY,999),(ui.State.RECORDING,222),
                             (ui.State.PLAYING,222),(ui.State.STOPPING,222)):
            p=self.panel();p.session=SimpleNamespace(state=state)
            with patch.object(ui,'U') as u:
                u.WindowFromPoint.return_value=target
                self.assertEqual(p.wndproc(123,0x21,123,0),3)
                u.SetForegroundWindow.assert_not_called()
                u.SetFocus.assert_not_called()

    def test_invalid_count_is_rejected(self):
        for text in ('','0','1000','-1','2.5','abc','２０','1e2'):
            with self.subTest(text=text),self.assertRaises(ValueError):
                ui.parse_repeats(text)

    def test_bar_is_tiny_and_only_slightly_transparent(self):
        self.assertEqual(ui.ACTIVE_SIZE,(288,64))
        self.assertGreaterEqual(ui.ACTIVE_ALPHA,240)
        self.assertLess(ui.ACTIVE_ALPHA,255)

    def test_center_on_negative_coordinate_monitor_without_activation(self):
        p = self.panel()
        with patch.object(ui,'window_rect',return_value=[-450,100,-110,700]),patch.object(ui,'U') as u:
            u.SetLayeredWindowAttributes.return_value = True
            p.set_active_view(True)
            self.assertEqual(p.normal_position,[-450,100])
            u.SetWindowPos.assert_called_with(123,None,-1104,508,288,64,0x14)
            u.SetLayeredWindowAttributes.assert_called_with(123,0,242,2)
            self.assertTrue(p.active_view)

    def test_center_uses_physical_size_at_150_percent(self):
        p = self.panel();p.dpi=144
        with patch.object(ui,'window_rect',return_value=[-450,100,-110,700]),patch.object(ui,'U') as u:
            u.SetLayeredWindowAttributes.return_value = True
            p.set_active_view(True)
            u.SetWindowPos.assert_called_with(123,None,-1176,492,432,96,0x14)

    def test_restore_position_expanded_mode_and_opacity(self):
        p=self.panel();p.active_view=True;p.expanded=True;p.normal_position=[-800,80]
        with patch.object(ui,'window_rect',return_value=[-1104,508,-816,572]),patch.object(ui,'U') as u:
            p.set_active_view(False)
            self.assertFalse(p.active_view)
            self.assertTrue(p.expanded)
            self.assertEqual(p.active_position,[-1104,508])
            self.assertEqual((p.width,p.height),(640,608))
            u.SetWindowLongPtrW.assert_called_with(123,-20,p.exstyle)
            u.SetLayeredWindowAttributes.assert_called_with(123,0,255,2)
            u.SetWindowPos.assert_called_with(123,None,-800,80,0,0,0x15)

    def test_transition_is_idempotent(self):
        p=self.panel()
        with patch.object(ui,'U') as u:
            p.set_active_view(False)
            u.SetWindowPos.assert_not_called()

    def test_layered_window_failure_restores_normal_panel(self):
        p=self.panel()
        with patch.object(ui,'window_rect',return_value=[-450,100,-110,700]),patch.object(ui,'U') as u:
            u.SetLayeredWindowAttributes.return_value=False
            with self.assertRaises(OSError):
                p.set_active_view(True)
            self.assertFalse(p.active_view)
            self.assertEqual((p.width,p.height),(340,600))

    def test_bar_is_prepared_before_recorder_starts(self):
        p=self.panel();p.queue=queue.SimpleQueue();p.queue.put('record')
        p.session=SimpleNamespace(state=ui.State.READY)
        order=[]
        p.set_active_view=lambda _:order.append('bar')
        p.session.toggle_record=lambda:order.append('record')
        p.render=lambda:None
        p.drain()
        self.assertEqual(order,['bar','record'])

    def test_invalid_count_never_starts_player_or_shrinks_panel(self):
        p=self.panel();p.queue=queue.SimpleQueue();p.queue.put('play')
        p.session=SimpleNamespace(state=ui.State.READY,error=MagicMock(),toggle_play=MagicMock())
        p.read_repeats=MagicMock(side_effect=ValueError('count'))
        p.set_active_view=MagicMock();p.render=lambda:None
        p.drain()
        p.set_active_view.assert_not_called()
        p.session.toggle_play.assert_not_called()
        p.session.error.assert_called_once()

    def test_preflight_keeps_clear_bar(self):
        p=self.panel();p.active_view=True
        events=[MacroEvent(0,LEFT_DOWN,x=-1800,y=80),MacroEvent(.2,LEFT_UP,x=-1800,y=80)]
        with patch.object(ui,'window_rect',return_value=[-1104,508,-816,572]),patch.object(ui,'U') as u:
            p.preflight(Macro('windows',events))
            u.SetWindowPos.assert_not_called()

    def test_preflight_relocates_bar_from_click_and_drag_path(self):
        for events in ([MacroEvent(0,LEFT_DOWN,x=-1000,y=540),MacroEvent(.2,LEFT_UP,x=-1000,y=540)],
                       [MacroEvent(0,LEFT_DOWN,x=-1200,y=540),MacroEvent(.2,MOVE_ABS,x=-700,y=540),MacroEvent(.3,LEFT_UP,x=-700,y=540)],
                       [MacroEvent(0,WHEEL,x=-1000,y=540,wheel=1)]):
            p=self.panel();p.active_view=True
            rect=[-1104,508,-816,572]
            def move(hwnd,z,x,y,w,h,flags):
                rect[:]=[x,y,x+288,y+64];return True
            with patch.object(ui,'window_rect',side_effect=lambda _:rect[:]),patch.object(ui,'U') as u:
                u.SetWindowPos.side_effect=move
                p.preflight(Macro('windows',events))
                self.assertTrue(u.SetWindowPos.called)
                self.assertFalse(rect[1]<=540<rect[3] and rect[0]<=-1000<rect[2])

    def test_no_safe_position_prevents_start(self):
        p=self.panel();p.active_view=True
        events=[MacroEvent(0,LEFT_DOWN,x=-1920,y=0),MacroEvent(.1,MOVE_ABS,x=0,y=1080),MacroEvent(.2,LEFT_UP,x=0,y=1080)]
        with patch.object(ui,'window_rect',return_value=[-1104,508,-816,572]),patch.object(ui,'U') as u:
            with self.assertRaisesRegex(ValueError,'spazio libero'):
                p.preflight(Macro('windows',events))
            u.SetWindowPos.assert_not_called()

    def test_screen_change_prevents_start(self):
        p=self.panel()
        with patch.object(ui,'screen_geometry',return_value=[[0,0,1920,1080]]):
            with self.assertRaisesRegex(ValueError,'Schermo'):
                p.preflight(Macro('windows',[],[[0,0,1280,800]]))


if __name__ == '__main__':
    unittest.main()
