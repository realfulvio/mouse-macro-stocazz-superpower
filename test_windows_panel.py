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
    def setUp(self):
        # Policy tests use synthetic coordinates, not the test runner's desktop.
        guard = patch.object(ui, 'ensure_input_integrity')
        self.integrity_check = guard.start()
        self.addCleanup(guard.stop)

    def panel(self):
        # The classic sizes below are those of Unicorno; Bambola has its own tests.
        ui.apply_skin('unicorno')
        self.addCleanup(ui.apply_skin, ui.DEFAULT_SKIN)
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
        p.layer = ui.Layer()
        p.shown_text, p.shown_enabled = {}, {}
        p.repeats = 1
        p.clamp = lambda x,y,w,h: (max(-1920,min(x,-w)),max(0,min(y,1080-h)))
        p.active_work_area = lambda: SimpleNamespace(left=-1920,right=0,top=0,bottom=1080)
        def layout(dpi):
            p.width,p.height = ui.window_size(p.active_view,p.expanded)
        p.layout = layout
        return p

    def update_panel(self, state=None, settings=None):
        p=self.panel();p.session=SimpleNamespace(state=state or ui.State.READY,message='')
        p.settings=dict(settings or {});p.dialog_open=False
        p.update={'state':'checking','latest':None,'release':None}
        p.install_update=MagicMock(return_value=False);p.write_settings=MagicMock();p.render=MagicMock()
        return p

    def test_startup_check_offers_new_version_and_remembers_no(self):
        p=self.update_panel()
        p.worker_result('update_checked','available',{'version':'9.0.0'},False)
        p.install_update.assert_called_once_with(startup=True)
        self.assertEqual(p.settings['skip_update'],'9.0.0')
        p.install_update.reset_mock()
        p.worker_result('update_checked','available',{'version':'9.0.0'},False)
        p.install_update.assert_not_called()

    def test_startup_check_never_interrupts_recording_or_replay(self):
        for state in (ui.State.RECORDING, ui.State.PLAYING):
            p=self.update_panel(state)
            p.worker_result('update_checked','available',{'version':'9.0.0'},False)
            p.install_update.assert_not_called()

    def test_manual_check_and_current_version_ask_nothing(self):
        p=self.update_panel()
        p.worker_result('update_checked','available',{'version':'9.0.0'},True)
        p.worker_result('update_checked','current',{'version':ui.VERSION},False)
        p.install_update.assert_not_called()

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

    def test_bambola_cover_layout_and_micro_bar_sizes(self):
        self.addCleanup(ui.apply_skin, ui.DEFAULT_SKIN)
        ui.apply_skin('bambola')
        extra = ui.hero_extra()
        self.assertGreater(extra, 0)
        self.assertEqual(ui.window_size(False, False), (340, 600 + extra))
        self.assertEqual(ui.window_size(False, True), (640, 608 + extra))
        self.assertEqual(ui.window_size(True, False), (300, 72))
        ui.apply_skin('palio')
        self.assertEqual((ui.hero_extra(), ui.active_size()), (0, ui.ACTIVE_SIZE))
        self.assertEqual(ui.window_size(False, True), (640, 608))

    def test_old_saved_skin_is_reset_once_to_bambola(self):
        settings = {'skin': 'unicorno'}
        self.assertTrue(ui.migrate_default_skin(settings))
        self.assertEqual(settings, {'skin': 'bambola', 'skin_default': 'bambola'})
        settings['skin'] = 'palio'  # the user's later choice is kept
        self.assertFalse(ui.migrate_default_skin(settings))
        self.assertEqual(settings['skin'], 'palio')

    def test_animation_repaints_only_the_horse_rectangle(self):
        p = self.panel()
        p.dpi = 120
        p.theme = SimpleNamespace(animated=[(10, 20, 100, 50)])
        with patch.object(ui.U, 'InvalidateRect') as invalidate:
            p.invalidate_mascot()
            hwnd, ref, erase = invalidate.call_args[0]
            self.assertEqual((hwnd, erase), (123, False))
            box = ref._obj
            self.assertEqual((box.left, box.top, box.right, box.bottom), (10, 23, 140, 90))
            p.theme.animated = []  # nothing drawn yet: repaint everything
            p.invalidate_mascot()
            self.assertIsNone(invalidate.call_args[0][1])

    def test_render_pushes_text_and_enabled_state_only_when_they_change(self):
        """Every SetWindowText repaints an owner-drawn control and render() runs ten times a second."""
        p = self.panel()
        p.hwnd = 7
        p.controls = {cid: 1000 + cid for cid in (1,2,3,4,10,11,12,21,22,23,24,25,31,32,40,41,42,101,102,104,202,204,205)}
        p.session = SimpleNamespace(state=ui.State.READY, message='ok', macro=SimpleNamespace(events=[]), last_trace=None)
        p.record_started = p.play_started = None
        p.speed, p.next_tab, p.slow, p.human, p.infinite = 1.0, False, False, False, False
        p.update = {'state': 'unknown', 'latest': None, 'release': None}
        p.metrics = lambda: ('0', '0:00')
        with patch.object(ui.U, 'SetWindowTextW') as text, patch.object(ui.U, 'EnableWindow') as enable, \
                patch.object(ui.U, 'InvalidateRect'):
            p.render()
            first = (text.call_count, enable.call_count)
            self.assertGreater(first[0], 0)
            self.assertGreater(first[1], 0)
            p.render()  # nothing changed: nothing pushed to the controls
            self.assertEqual((text.call_count, enable.call_count), first)
            p.session.message = 'altro'  # a changed text is pushed once
            p.render()
            self.assertEqual(text.call_count, first[0] + 1)
            p.session.state = ui.State.RECORDING  # a changed state updates texts and enabled flags
            p.render()
            self.assertGreater(text.call_count, first[0] + 1)
            self.assertGreater(enable.call_count, first[1])

    def render_panel(self, state):
        p = self.panel()
        p.hwnd = 7
        p.controls = {cid: 1000 + cid for cid in (1,2,3,4,10,11,12,21,22,23,24,25,31,32,40,41,42,101,102,104,202,204,205)}
        p.session = SimpleNamespace(state=state, message='ok', macro=SimpleNamespace(events=[]), last_trace=None, completed=0)
        p.record_started = p.play_started = None
        p.speed, p.next_tab, p.slow, p.human, p.infinite = 1.0, False, False, False, False
        p.update = {'state': 'unknown', 'latest': None, 'release': None}
        return p

    def test_compact_bar_repaints_only_its_detail_line_when_counters_change(self):
        """While recording the count changes ten times a second: the bar and its mascot stay."""
        p = self.render_panel(ui.State.RECORDING)
        p.active_view = True
        p.session.recorder = SimpleNamespace(current_event_count=1)
        counts = iter(range(1, 100))
        p.metrics = lambda: (str(next(counts)), '00:01.250')
        with patch.object(ui.U, 'SetWindowTextW'), patch.object(ui.U, 'EnableWindow'), \
                patch.object(ui.U, 'InvalidateRect') as invalidate:
            p.render()  # first view: everything
            self.assertIsNone(invalidate.call_args_list[0][0][1])
            invalidate.reset_mock()
            p.render()  # new count only: one rectangle, the detail line, and no control
            self.assertEqual(invalidate.call_count, 1)
            hwnd, ref, erase = invalidate.call_args[0]
            box = ref._obj
            self.assertEqual((hwnd, erase), (7, False))
            self.assertEqual((box.left, box.top, box.right, box.bottom), p.detail_box())
            x, y, w, h = 48, 28, 154, 19  # the detail line of paint_active() for this skin, at 100%
            self.assertTrue(box.left <= x and box.top <= y and box.right >= x + w and box.bottom >= y + h)
            invalidate.reset_mock()
            p.session.state = ui.State.STOPPING  # a new state redraws the whole bar
            p.render()
            self.assertIsNone(invalidate.call_args_list[0][0][1])

    def test_title_follows_state_at_once_and_counters_at_most_once_a_second(self):
        p = self.render_panel(ui.State.RECORDING)
        p.active_view = True
        p.session.recorder = SimpleNamespace(current_event_count=1)
        counts = iter(range(1, 100))
        p.metrics = lambda: (str(next(counts)), '00:01.250')
        titles = []
        with patch.object(ui.U, 'SetWindowTextW', side_effect=lambda h, t: titles.append(t) if h == 7 else None), \
                patch.object(ui.U, 'EnableWindow'), patch.object(ui.U, 'InvalidateRect'), \
                patch.object(ui.time, 'monotonic', return_value=100.0) as clock:
            p.render(); p.render(); p.render()
            self.assertEqual(len(titles), 1)  # same second: the count waits
            self.assertNotIn('.250', titles[0])  # no milliseconds in the title
            clock.return_value = 101.0
            p.render()
            self.assertEqual(len(titles), 2)
            p.session.state = ui.State.STOPPING
            p.render()  # a new state: at once
            self.assertEqual(len(titles), 3)
            self.assertIn(ui.State.STOPPING.value, titles[-1])

    def test_paint_always_ends_even_when_drawing_fails(self):
        """Without EndPaint the window stays invalid and Windows sends WM_PAINT again at once, forever."""
        p = self.panel()
        p.paint_dc = MagicMock(side_effect=RuntimeError('GDI+ 3'))
        with patch.object(ui.U, 'BeginPaint', return_value=55), patch.object(ui.U, 'EndPaint') as end:
            with self.assertRaises(RuntimeError):
                p.paint(123)
            end.assert_called_once()

    def test_repeating_failure_is_written_to_the_log_once(self):
        import tempfile
        from pathlib import Path
        p = self.panel()
        p.width = 100
        p.session = SimpleNamespace(request_stop=MagicMock(), error=MagicMock(), state=ui.State.READY)
        p.paint = MagicMock(side_effect=RuntimeError('GDI+ 3'))
        with tempfile.TemporaryDirectory() as folder, patch.object(ui, 'FOLDER', Path(folder)), \
                patch.object(ui.U, 'DefWindowProcW', return_value=0):
            log = Path(folder) / 'errore.log'
            p.wndproc(123, 0xF, 0, 0)
            self.assertIn('GDI+ 3', log.read_text('utf-8'))
            log.unlink()
            p.wndproc(123, 0xF, 0, 0)  # same failure again: not rewritten
            self.assertFalse(log.exists())
            p.paint.side_effect = RuntimeError('altro')
            p.wndproc(123, 0xF, 0, 0)  # a different one is
            self.assertIn('altro', log.read_text('utf-8'))
            self.assertEqual(p.session.error.call_count, 3)

    def test_settings_are_replaced_whole(self):
        import json, tempfile
        from pathlib import Path
        p = self.panel()
        with tempfile.TemporaryDirectory() as folder, patch.object(ui, 'FOLDER', Path(folder)):
            target = Path(folder) / 'panel-v016.json'
            target.write_text('{"skin": "vecchia"}', 'utf-8')
            p.settings = {'skin': 'bambola', 'position': [10, 20]}
            p.write_settings()
            self.assertEqual(json.loads(target.read_text('utf-8')), p.settings)
            self.assertEqual(sorted(x.name for x in Path(folder).iterdir()), ['panel-v016.json'])
            with patch.object(ui.os, 'replace', side_effect=PermissionError('in uso')):
                p.settings['skin'] = 'unicorno'
                p.write_settings()  # swap refused: plain write, as before
            self.assertEqual(json.loads(target.read_text('utf-8'))['skin'], 'unicorno')
            self.assertEqual(sorted(x.name for x in Path(folder).iterdir()), ['panel-v016.json'])

    def test_replay_trace_file_is_valid_json_with_every_record(self):
        import json, tempfile
        from pathlib import Path
        records = [{'type': 'playback_start', 'elapsed_seconds': 0.0, 'cycle': 1},
                   {'type': 'input_sent', 'click': [1, 2], 'kind': 'left_down', 'message': 'perché'}]
        header = {'version': ui.VERSION, 'options': {'speed': 1.0, 'mode': 'repeat_count'}, 'outcome': 'pronto'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'ultimo-replay.json'
            ui.save_replay_trace(path, header, records)
            self.assertEqual(json.loads(path.read_text('utf-8')), dict(header, records=records))
            self.assertEqual([x.name for x in Path(folder).iterdir()], ['ultimo-replay.json'])

    def test_mascot_layer_survives_a_paint_beside_it(self):
        layer = ui.Layer()
        layer.set_box((0, 0, 87, 75))
        self.assertFalse(layer.overlaps((87, 24, 150, 22)))  # the bar's detail line, right of the head
        self.assertTrue(layer.overlaps((86, 24, 150, 22)))
        self.assertTrue(layer.overlaps((0, 0, 300, 72)))
        layer.set_box(None)
        self.assertFalse(layer.overlaps((0, 0, 300, 72)))

    def test_mascot_layer_only_matches_its_own_box_and_forgets_on_change(self):
        layer = ui.Layer()
        self.assertFalse(layer.matches((1, 2, 3, 4)))  # no box yet
        layer.set_box((10, 20, 110, 90))
        self.assertTrue(layer.matches((10, 20, 100, 70)))
        self.assertFalse(layer.matches((10, 20, 100, 71)))  # any other dirty rectangle: full path
        layer.valid = True
        layer.set_box((10, 20, 110, 90))  # same box: still valid
        self.assertTrue(layer.valid)
        layer.set_box((11, 20, 110, 90))  # moved or resized: cached background is stale
        self.assertFalse(layer.valid)
        layer.set_box(None)
        self.assertFalse(layer.matches((11, 20, 99, 70)))

    def test_animation_timer_runs_only_while_an_animated_skin_is_visible(self):
        p = self.panel()
        p.shown = p.minimized = p.animating = False
        with patch.object(ui.U, 'SetTimer') as start, patch.object(ui.U, 'KillTimer') as stop:
            ui.apply_skin('bambola')
            self.addCleanup(ui.apply_skin, ui.DEFAULT_SKIN)
            p.sync_animation_timer()  # not shown yet
            start.assert_not_called()
            p.shown = True
            p.sync_animation_timer()
            p.sync_animation_timer()  # idempotent
            start.assert_called_once_with(123, 2, 16, None)
            p.minimized = True  # minimized or hidden in the tray: no ticks
            p.sync_animation_timer()
            stop.assert_called_once_with(123, 2)
            p.minimized = False
            ui.apply_skin('palio')  # a static skin needs no timer
            p.sync_animation_timer()
            self.assertEqual(start.call_count, 1)
            self.assertFalse(p.animating)

    def test_bambola_animates_other_skins_do_not(self):
        ui.apply_skin('bambola')
        self.addCleanup(ui.apply_skin, ui.DEFAULT_SKIN)
        frames = {ui.frame_index(t / 100) for t in range(0, 600)}
        self.assertEqual(len(frames), 97)
        ui.apply_skin('unicorno')
        self.assertEqual({ui.frame_index(t / 100) for t in range(0, 600)}, {0})

    def test_bambola_bar_is_centered_with_its_own_size(self):
        p = self.panel()
        ui.apply_skin('bambola')
        with patch.object(ui,'window_rect',return_value=[-450,100,-110,700]),patch.object(ui,'U') as u:
            u.SetLayeredWindowAttributes.return_value = True
            p.set_active_view(True)
            u.SetWindowPos.assert_called_with(123,None,-1110,504,300,72,0x14)

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

    def test_integrity_warning_prevents_playback_after_bar_placement(self):
        p = self.panel()
        macro = Macro('windows', [])
        self.integrity_check.side_effect = ValueError('Esegui come amministratore')
        with patch.object(p, 'place_playback_bar') as place:
            with self.assertRaisesRegex(ValueError, 'amministratore'):
                p.preflight(macro)
            place.assert_called_once_with(macro)
            self.integrity_check.assert_called_once_with(macro.events)

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

    def test_fit_dpi_keeps_the_panel_inside_the_work_area(self):
        self.assertEqual(ui.fit_dpi(96, (340, 648), (1920, 1040)), 96)      # fits: unchanged
        self.assertEqual(ui.fit_dpi(144, (340, 648), (2560, 1400)), 144)
        fitted = ui.fit_dpi(120, (340, 648), (1024, 708))                     # 1024x768 at 125%
        self.assertLess(fitted, 120)
        self.assertLessEqual(round(648 * fitted / 96), 708)
        self.assertGreater(round(648 * (fitted + 1) / 96), 708)               # the largest that fits
        self.assertEqual(ui.fit_dpi(120, (340, 648), (300, 300)), ui.MIN_FIT_DPI)  # never unreadable

    def test_layout_scales_bambola_panel_down_on_1024x768_at_125_percent(self):
        ui.apply_skin('bambola')
        self.addCleanup(ui.apply_skin, ui.DEFAULT_SKIN)
        p = self.panel()
        del p.layout, p.clamp  # the real ones
        p.repeat_font = None
        p.controls = {22: 222, 202: 1202}
        work = SimpleNamespace(left=0, top=0, right=1024, bottom=708)
        with patch.object(ui, 'window_rect', return_value=[600, 20, 1000, 700]), \
                patch.object(ui.Panel, 'work_area', staticmethod(lambda x, y: work)), \
                patch.object(ui, 'U') as u, patch.object(ui, 'G'):
            p.layout(120)
            x, y, w, h = u.SetWindowPos.call_args_list[0][0][2:6]
        self.assertEqual(p.monitor_dpi, 120)
        self.assertLess(p.dpi, 120)
        self.assertLessEqual(y + h, 708)
        self.assertGreaterEqual(y, 0)
        self.assertLessEqual(x + w, 1024)
        p.active_view = True  # the micro bar always fits: drawn at the monitor scale
        with patch.object(ui, 'window_rect', return_value=[600, 20, 1000, 700]), \
                patch.object(ui.Panel, 'work_area', staticmethod(lambda x, y: work)), \
                patch.object(ui, 'U'), patch.object(ui, 'G'):
            p.layout(p.monitor_dpi)
        self.assertEqual(p.dpi, 120)

    def test_downloaded_update_waits_for_the_end_of_a_recording(self):
        p = self.update_panel(ui.State.RECORDING)
        p.update = {'state': 'installing', 'latest': '9.0.0', 'release': {'version': '9.0.0'}}
        p.session.message = ''
        target = ui.Path('C:/x/MouseMacroStocazzSuperpower-Windows-v9.0.0')
        with patch.object(ui.subprocess, 'Popen') as popen, patch.object(ui, 'U') as u:
            p.worker_result('update_installed', str(target))
            popen.assert_not_called()  # closing now would throw the recording away
            self.assertIn('si riavvia appena finisci', p.session.message)
            self.assertFalse(p.install_update.called)
            p.session.state = ui.State.READY
            self.assertTrue(p.restart_if_idle())
            popen.assert_called_once()
            self.assertEqual(popen.call_args[0][0][0], str(target / 'runtime' / 'pythonw.exe'))
            u.PostMessageW.assert_called_once_with(p.hwnd, ui.WM_CLOSE, 0, 0)
            self.assertFalse(p.restart_if_idle())  # only once

    def test_no_second_check_or_download_while_downloading(self):
        p = self.update_panel()
        p.update = {'state': 'installing', 'latest': '9.0.0', 'release': {'version': '9.0.0'}}
        with patch.object(ui.threading, 'Thread') as thread:
            p.check_updates(manual=True)
            thread.assert_not_called()
        self.assertEqual(p.update['state'], 'installing')
        del p.install_update  # the real one
        with patch.object(ui, 'U') as u:
            self.assertFalse(p.install_update())
            u.MessageBoxW.assert_not_called()

    def test_screen_change_prevents_start(self):
        p=self.panel()
        with patch.object(ui,'screen_geometry',return_value=[[0,0,1920,1080]]):
            with self.assertRaisesRegex(ValueError,'Schermo'):
                p.preflight(Macro('windows',[],[[0,0,1280,800]]))


if __name__ == '__main__':
    unittest.main()
