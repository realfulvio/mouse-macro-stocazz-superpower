import asyncio
import inspect
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import flet as ft
import main as app
from macro.engine import LoopMode, PlaybackEnd
from macro.events import LEFT_DOWN, LEFT_UP, Macro, MacroEvent


class PageStub:
    def __init__(self):
        self.window=SimpleNamespace()
        self.services=[]
        self.controls=[]
        self.dialogs=[]
    def add(self,*controls):
        self.controls.extend(controls)
    def update(self):
        pass
    def show_dialog(self,dialog):
        self.dialogs.append(dialog)
    def pop_dialog(self):
        self.dialogs.pop()


class InlineThread:
    def __init__(self,target,**kwargs):
        self.target=target
    def start(self):
        self.target()


def controls(page):
    pending=list(page.controls)+list(page.dialogs)
    seen=set()
    while pending:
        control=pending.pop(0)
        if id(control) in seen:
            continue
        seen.add(id(control))
        yield control
        content=getattr(control,'content',None)
        if isinstance(content,ft.Control):
            pending.append(content)
        pending.extend(getattr(control,'controls',[]) or [])
        pending.extend(getattr(control,'actions',[]) or [])


@unittest.skipUnless(sys.platform == 'win32', 'Windows UI callbacks')
class UiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'macro.mmr'
        Macro('windows',[MacroEvent(0,LEFT_DOWN,x=10,y=20),
                         MacroEvent(.03,LEFT_UP,x=10,y=20)]).save(str(self.path))
        self.page=PageStub()
        with patch('macro.windows_backend.GlobalHotkeys') as hotkeys:
            hotkeys.return_value.failed=[]
            app.main(self.page)
            self.hotkey_callback=hotkeys.call_args.args[0]
            self.hotkeys=hotkeys.return_value
        self.items=list(controls(self.page))

    def load(self):
        result=[{'id':1,'path':str(self.path),'name':self.path.name,
                 'size':self.path.stat().st_size}]
        self.pick_click(ft.Icons.FOLDER_OPEN_ROUNDED,result)

    def file_button(self,icon):
        return next(c for c in self.items if isinstance(c,ft.OutlinedButton) and c.icon==icon)

    def pick_click(self,icon,result=None,error=None):
        button=self.file_button(icon)
        self.assertTrue(inspect.iscoroutinefunction(button.on_click))
        page=SimpleNamespace(web=False,platform=SimpleNamespace(is_mobile=lambda:False))
        with patch.object(ft.FilePicker,'page',new_callable=PropertyMock,return_value=page), \
                patch.object(ft.FilePicker,'_invoke_method',new_callable=AsyncMock,
                             return_value=result,side_effect=error) as invoke:
            asyncio.run(button.on_click(None))
        return invoke

    def play_button(self):
        return next(c for c in self.items if isinstance(c,ft.Container)
                    and isinstance(c.content,ft.Row)
                    and any(isinstance(t,ft.Text) and t.value=='RIPRODUCI  (F10)'
                            for t in c.content.controls))

    def status_values(self):
        return [c.value for c in self.items if isinstance(c,ft.Text)]

    def count_field(self):
        row=next(c for c in self.items if isinstance(c,ft.Row)
                 and any(isinstance(t,ft.Text) and t.value=='volte' for t in c.controls))
        return next(c for c in row.controls if isinstance(c,ft.TextField))

    def action_button(self,label):
        return next(c for c in self.items if isinstance(c,ft.Container)
                    and isinstance(c.content,ft.Row)
                    and any(isinstance(t,ft.Text) and t.value==label
                            for t in c.content.controls))

    def chip(self,label):
        return self.action_button(label)

    def setting_switch(self,label):
        row=next(c for c in self.items if isinstance(c,ft.Row)
                 and any(isinstance(t,ft.Text) and t.value==label for t in c.controls))
        return next(c for c in row.controls if isinstance(c,ft.Switch))

    def open_settings(self):
        button=next(c for c in self.items if isinstance(c,ft.OutlinedButton)
                    and c.icon==ft.Icons.SETTINGS_ROUNDED)
        button.on_click(None)
        self.items=list(controls(self.page))

    def variation_switch(self):
        row=next(c for c in self.items if isinstance(c,ft.Row)
                 and any(isinstance(t,ft.Text) and t.value=='Varia i tempi a ogni giro'
                         for t in c.controls))
        return next(c for c in row.controls if isinstance(c,ft.Switch))

    def test_default_and_variation_options_reach_engine(self):
        self.load()
        self.count_field().value='7'
        self.open_settings()
        switches=[c for c in self.items if isinstance(c,ft.Switch)]
        self.assertEqual(len(switches),3)
        variation=self.variation_switch()
        self.assertFalse(variation.value)
        for enabled,expected in [(False,0),(True,.12)]:
            variation.value=enabled
            variation.on_change(None)
            with patch.object(app,'make_player',return_value=MagicMock()), \
                    patch.object(app,'play',return_value=PlaybackEnd.DONE) as play_mock, \
                    patch.object(app.threading,'Thread',InlineThread):
                self.play_button().on_click(None)
                self.assertAlmostEqual(play_mock.call_args.args[1].timing_variation_seconds,expected)
                self.assertEqual(play_mock.call_args.args[1].mode,LoopMode.REPEAT_COUNT)
                self.assertEqual(play_mock.call_args.args[1].repeat_count,7)
                self.assertAlmostEqual(play_mock.call_args.args[1].min_click_hold_seconds,.15)

    def test_backend_error_is_visible_and_buttons_recover(self):
        self.load()
        self.count_field().value='2'
        with patch.object(app,'make_player',return_value=MagicMock()), \
                patch.object(app,'play',side_effect=OSError('Test backend failure')), \
                patch.object(app.threading,'Thread',InlineThread):
            self.play_button().on_click(None)
        self.assertIn('Errore durante la riproduzione',self.status_values())
        self.assertIn('Test backend failure',self.status_values())
        self.assertIsNotNone(self.play_button())

    def test_incompatible_macro_does_not_become_playable(self):
        Macro('linux',[MacroEvent(0,LEFT_DOWN),MacroEvent(.03,LEFT_UP)]).save(str(self.path))
        self.load()
        self.assertIn('Macro non compatibile',self.status_values())
        with patch.object(app,'make_player') as player:
            self.play_button().on_click(None)
            player.assert_not_called()
        self.assertIn('Nessuna macro',self.status_values())

    def test_settings_close_and_reopen_preserve_values(self):
        self.open_settings()
        field=next(c for c in self.items if isinstance(c,ft.TextField) and c.value=='150')
        field.value='200'
        field.on_change(SimpleNamespace())
        variation=self.variation_switch()
        variation.value=True
        variation.on_change(None)
        self.page.pop_dialog()
        self.items=list(controls(self.page))
        self.open_settings()
        self.assertIn(field,self.items)
        self.assertEqual(field.value,'200')
        self.assertIn(variation,self.items)
        self.assertTrue(variation.value)
        self.load()
        self.count_field().value='2'
        with patch.object(app,'make_player',return_value=MagicMock()), \
                patch.object(app,'play',return_value=PlaybackEnd.DONE) as play_mock, \
                patch.object(app.threading,'Thread',InlineThread):
            self.play_button().on_click(None)
            self.assertAlmostEqual(play_mock.call_args.args[1].min_click_hold_seconds,.20)

    def test_startup_has_compact_controls_and_preserves_defaults(self):
        self.assertEqual(self.page.window.height,720)
        self.assertEqual(self.page.window.width,560)
        self.assertIn(f'{app.VERSION} · powered by hcok',self.status_values())
        # Nella schermata principale c'è solo l'attesa pagina, attiva di base.
        self.assertEqual([c.value for c in self.items if isinstance(c,ft.Switch)],[True])
        self.assertTrue(self.setting_switch('Aspetta che la pagina sia pronta prima di cliccare').value)
        self.assertFalse(self.page.dialogs)
        self.assertIn('Durata minima di click e pause',self.status_values())
        self.assertNotIn('A fine giro chiudi la scheda (Ctrl+W)',self.status_values())
        self.assertIn('150',[c.value for c in self.items if isinstance(c,ft.TextField)])
        count_row=next(c for c in self.items if isinstance(c,ft.Row)
                       and any(isinstance(t,ft.Text) and t.value=='volte' for t in c.controls))
        self.assertTrue(count_row.visible)
        self.assertEqual(self.count_field().value,'')
        self.open_settings()
        self.assertIn('A fine giro chiudi la scheda (Ctrl+W)',self.status_values())
        self.assertEqual(len([c for c in self.items if isinstance(c,ft.Switch)]),3)
        fields=[c.value for c in self.items if isinstance(c,ft.TextField)]
        self.assertTrue({'','10','150','120'}.issubset(fields))
        # Le due opzioni del dialogo restano spente.
        self.assertEqual(sorted(c.value for c in self.items if isinstance(c,ft.Switch)),[False,False,True])

    def test_repeat_count_empty_or_invalid_does_not_start_player(self):
        self.load()
        for count in ('','abc','0','-2','2.5','NaN'):
            with self.subTest(count=count), patch.object(app,'make_player') as player:
                self.count_field().value=count
                self.play_button().on_click(None)
                player.assert_not_called()
                self.assertIn('Imposta il numero di giri',self.status_values())

    def test_infinite_mode_does_not_require_repeat_count(self):
        self.load()
        chip=next(c for c in self.items if isinstance(c,ft.Container)
                  and isinstance(c.content,ft.Row)
                  and any(isinstance(t,ft.Text) and t.value=='Infinito' for t in c.content.controls))
        chip.on_click(None)
        with patch.object(app,'make_player',return_value=MagicMock()), \
                patch.object(app,'play',return_value=PlaybackEnd.DONE) as play_mock, \
                patch.object(app.threading,'Thread',InlineThread):
            self.play_button().on_click(None)
            self.assertEqual(play_mock.call_args.args[1].mode,LoopMode.INFINITE)
            self.assertIsNone(play_mock.call_args.args[1].repeat_count)

    def test_load_button_awaits_native_dialog_and_enables_save(self):
        result=[{'id':1,'path':str(self.path),'name':self.path.name,'size':self.path.stat().st_size}]
        invoke=self.pick_click(ft.Icons.FOLDER_OPEN_ROUNDED,result)
        invoke.assert_awaited_once()
        method,args=invoke.call_args.args
        self.assertEqual(method,'pick_files')
        self.assertFalse(args['allow_multiple'])
        self.assertEqual(args['allowed_extensions'],['mmr','json'])
        self.assertIn('Macro caricata',self.status_values())
        self.assertFalse(self.file_button(ft.Icons.SAVE_ROUNDED).disabled)
        self.assertEqual(self.play_button().opacity,1)

    def test_save_button_awaits_native_dialog_and_roundtrips_full_macro(self):
        recorded=Macro('windows',[MacroEvent(0,LEFT_DOWN,x=123,y=456,snap='saved-snapshot'),
                                  MacroEvent(.2,LEFT_UP,x=123,y=456)],screen=[-1920,0,3840,1080])
        recorded.save(str(self.path))
        self.load()
        target=Path(self.temp.name)/'scelta personale.mmr'
        invoke=self.pick_click(ft.Icons.SAVE_ROUNDED,str(target))
        invoke.assert_awaited_once()
        method,args=invoke.call_args.args
        self.assertEqual(method,'save_file')
        self.assertEqual(args['file_name'],'macro.mmr')
        self.assertEqual(args['allowed_extensions'],['mmr'])
        self.assertEqual(Macro.load(str(target)),recorded)
        self.assertIn('Macro salvata',self.status_values())

    def test_cancelled_file_dialogs_leave_macro_and_status_unchanged(self):
        self.load()
        before=self.status_values()
        self.pick_click(ft.Icons.FOLDER_OPEN_ROUNDED,[])
        self.assertEqual(self.status_values(),before)
        self.pick_click(ft.Icons.SAVE_ROUNDED,None)
        self.assertEqual(self.status_values(),before)
        target=Path(self.temp.name)/'still-loaded.mmr'
        self.pick_click(ft.Icons.SAVE_ROUNDED,str(target))
        self.assertEqual(Macro.load(str(target)),Macro.load(str(self.path)))

    def test_bad_file_and_picker_errors_preserve_previous_macro(self):
        self.load()
        expected=Macro.load(str(self.path))
        self.path.write_text('{broken',encoding='utf-8')
        self.load()
        self.assertIn('Errore nel caricamento',self.status_values())
        self.pick_click(ft.Icons.FOLDER_OPEN_ROUNDED,error=OSError('Dialog unavailable'))
        self.assertIn('Dialog unavailable',self.status_values())
        target=Path(self.temp.name)/'preserved.mmr'
        self.pick_click(ft.Icons.SAVE_ROUNDED,str(target))
        self.assertEqual(Macro.load(str(target)),expected)

    def test_save_errors_are_visible_and_empty_macro_does_not_open_dialog(self):
        invoke=self.pick_click(ft.Icons.SAVE_ROUNDED,'unused.mmr')
        invoke.assert_not_awaited()
        self.assertIn('Nessuna macro',self.status_values())
        self.load()
        with patch.object(Macro,'save',side_effect=PermissionError('Accesso negato')):
            self.pick_click(ft.Icons.SAVE_ROUNDED,str(Path(self.temp.name)/'denied.mmr'))
        self.assertIn('Errore nel salvataggio',self.status_values())
        self.assertIn('Accesso negato',self.status_values())
        self.pick_click(ft.Icons.SAVE_ROUNDED,error=OSError('Save dialog unavailable'))
        self.assertIn('Save dialog unavailable',self.status_values())

    def test_loading_empty_macro_disables_save_and_play(self):
        Macro('windows',[]).save(str(self.path))
        self.load()
        self.assertTrue(self.file_button(ft.Icons.SAVE_ROUNDED).disabled)
        self.assertEqual(self.play_button().opacity,.4)
        with patch.object(app,'make_player') as player:
            self.play_button().on_click(None)
            player.assert_not_called()

    def test_record_button_start_stop_removes_click_on_stop_button(self):
        record=self.action_button('REGISTRA  (F9)')
        events=Macro.load(str(self.path)).events
        recorder=MagicMock()
        recorder.stop.return_value=events+[MacroEvent(.4,LEFT_DOWN,x=99,y=99),MacroEvent(.5,LEFT_UP,x=99,y=99)]
        with patch.object(app,'make_recorder',return_value=recorder), \
                patch.object(app.threading,'Thread'), \
                patch('macro.windows_backend.screen_geometry',return_value=[0,0,1920,1080]):
            record.on_click(SimpleNamespace())
            recorder.start.assert_called_once()
            self.assertEqual(record.content.controls[1].value,'INTERROMPI  (F9)')
            self.assertTrue(self.file_button(ft.Icons.SAVE_ROUNDED).disabled)
            with patch.object(app,'make_player') as player:
                self.play_button().on_click(None)
                player.assert_not_called()
            self.pick_click(ft.Icons.FOLDER_OPEN_ROUNDED,[]).assert_not_awaited()
            self.pick_click(ft.Icons.SAVE_ROUNDED,None).assert_not_awaited()
            record.on_click(SimpleNamespace())
        target=Path(self.temp.name)/'recorded.mmr'
        self.pick_click(ft.Icons.SAVE_ROUNDED,str(target))
        self.assertEqual(Macro.load(str(target)),Macro('windows',events,screen=[0,0,1920,1080]))
        self.assertEqual(record.content.controls[1].value,'REGISTRA  (F9)')

    def test_record_hotkey_preserves_last_real_click_and_emergency_stops(self):
        from macro.windows_backend import HOTKEY_RECORD,HOTKEY_EMERGENCY
        events=Macro.load(str(self.path)).events
        recorder=MagicMock()
        recorder.stop.return_value=events
        with patch.object(app,'make_recorder',return_value=recorder), \
                patch.object(app.threading,'Thread'), \
                patch('macro.windows_backend.screen_geometry',return_value=[]):
            self.hotkey_callback(HOTKEY_RECORD)
            self.hotkey_callback(HOTKEY_EMERGENCY)
        self.assertIn('Registrazione completata',self.status_values())
        target=Path(self.temp.name)/'hotkey.mmr'
        self.pick_click(ft.Icons.SAVE_ROUNDED,str(target))
        self.assertEqual(Macro.load(str(target)).events,events)

    def test_record_start_and_stop_failures_are_visible(self):
        record=self.action_button('REGISTRA  (F9)')
        with patch.object(app,'make_recorder',side_effect=OSError('Recorder unavailable')):
            record.on_click(None)
        self.assertIn('Errore all’avvio della registrazione'.replace('’',"'"),self.status_values())
        recorder=MagicMock()
        recorder.stop.side_effect=OSError('Stop failed')
        with patch.object(app,'make_recorder',return_value=recorder),patch.object(app.threading,'Thread'):
            record.on_click(None)
            record.on_click(None)
        self.assertIn('Errore nel fermare la registrazione',self.status_values())
        self.assertEqual(record.content.controls[1].value,'INTERROMPI  (F9)')

    def test_stop_button_and_emergency_hotkey_signal_playback(self):
        from macro.windows_backend import HOTKEY_EMERGENCY,HOTKEY_PLAY
        for emergency in (False,True):
            with self.subTest(emergency=emergency):
                self.load()
                self.count_field().value='2'
                button=self.play_button()
                backend=MagicMock()
                with patch.object(app,'make_player',return_value=backend),patch.object(app.threading,'Thread') as thread:
                    self.hotkey_callback(HOTKEY_PLAY)
                    run=thread.call_args.kwargs['target']
                    self.assertEqual(button.content.controls[0].icon,ft.Icons.STOP_ROUNDED)
                    with patch.object(app,'make_recorder') as recorder:
                        self.action_button('REGISTRA  (F9)').on_click(None)
                        recorder.assert_not_called()
                    if emergency:
                        self.hotkey_callback(HOTKEY_EMERGENCY)
                    else:
                        button.on_click(None)
                def fake_play(*args):
                    self.assertTrue(args[5].is_set())
                    return PlaybackEnd.STOPPED
                with patch.object(app,'play',side_effect=fake_play):
                    run()
                backend.close.assert_called_once()
                self.assertEqual(button.content.controls[1].value,'RIPRODUCI  (F10)')
                self.assertEqual(button.content.controls[0].icon,ft.Icons.PLAY_ARROW_ROUNDED)

    def test_changed_screen_prevents_playback_and_backend_start_error_recovers(self):
        Macro('windows',Macro.load(str(self.path)).events,screen=[0,0,1920,1080]).save(str(self.path))
        self.load()
        self.count_field().value='1'
        with patch('macro.windows_backend.screen_geometry',return_value=[0,0,2560,1440]), \
                patch.object(app,'make_player') as player:
            self.play_button().on_click(None)
            player.assert_not_called()
        self.assertIn('Schermo diverso dalla registrazione',self.status_values())
        with patch('macro.windows_backend.screen_geometry',return_value=[0,0,1920,1080]), \
                patch.object(app,'make_player',side_effect=OSError('Player unavailable')):
            self.play_button().on_click(None)
        self.assertIn('Errore all’avvio della riproduzione'.replace('’',"'"),self.status_values())
        self.assertEqual(self.play_button().content.controls[0].icon,ft.Icons.PLAY_ARROW_ROUNDED)

    def test_duration_speed_and_invalid_numeric_fields_reach_engine(self):
        self.load()
        self.chip('Durata').on_click(None)
        row=next(c for c in self.items if isinstance(c,ft.Row)
                 and any(isinstance(t,ft.Text) and t.value=='minuti' for t in c.controls))
        next(c for c in row.controls if isinstance(c,ft.TextField)).value='3'
        slider=next(c for c in self.items if isinstance(c,ft.Slider))
        slider.value=2.5
        slider.on_change(None)
        self.assertIn('2.50x',self.status_values())
        for invalid in ('','abc','NaN','Infinity'):
            field=next(c for c in self.items if isinstance(c,ft.TextField) and c.value=='150')
            field.value=invalid
            with patch.object(app,'make_player',return_value=MagicMock()), \
                    patch.object(app,'play',return_value=PlaybackEnd.DONE) as play_mock, \
                    patch.object(app.threading,'Thread',InlineThread):
                self.play_button().on_click(None)
            options=play_mock.call_args.args[1]
            self.assertEqual(options.mode,LoopMode.DURATION)
            self.assertEqual(options.duration_seconds,180)
            self.assertEqual(options.speed,2.5)
            self.assertEqual(options.min_click_hold_seconds,.15)
            field.value='150'

    def test_sync_tab_and_tolerance_settings_are_wired_to_playback(self):
        from macro.windows_backend import TOLERANCE_LOOSE
        self.load()
        self.count_field().value='2'
        self.open_settings()
        for label in ('A fine giro chiudi la scheda (Ctrl+W)',
                      'Aspetta che la pagina sia pronta prima di cliccare'):
            switch=self.setting_switch(label)
            switch.value=True
            switch.on_change(None)
        self.chip('Tollerante').on_click(None)
        backend=MagicMock()
        backend.wait_until_ready.return_value=False
        def fake_play(*args):
            self.assertFalse(args[6](args[0][0]))
            args[7]()
            return PlaybackEnd.SYNC_TIMEOUT
        with patch.object(app,'make_player',return_value=backend), \
                patch.object(app,'play',side_effect=fake_play), \
                patch.object(app.threading,'Thread',InlineThread), \
                patch('threading.Event.wait',return_value=False):
            self.play_button().on_click(None)
        self.assertEqual(backend.wait_until_ready.call_args.args[1],10)
        self.assertEqual(backend.wait_until_ready.call_args.args[3],TOLERANCE_LOOSE)
        backend.close_tab.assert_called_once()
        self.assertIn('Fermato: pagina non pronta al click n° 1',self.status_values())

    def test_help_and_useless_dialogs_open_and_close(self):
        help_button=next(c for c in self.items if isinstance(c,ft.IconButton)
                         and c.icon==ft.Icons.HELP_OUTLINE_ROUNDED)
        for button in (help_button,next(c for c in self.items if isinstance(c,ft.Container)
                                       and isinstance(c.content,ft.Text) and c.content.value=='PULSANTE INUTILE')):
            button.on_click(None)
            self.assertEqual(len(self.page.dialogs),1)
            self.page.dialogs[-1].actions[0].on_click(None)
            self.assertFalse(self.page.dialogs)

    def test_session_cleanup_stops_recording_and_unregisters_hotkeys(self):
        recorder=MagicMock()
        with patch.object(app,'make_recorder',return_value=recorder),patch.object(app.threading,'Thread'):
            self.action_button('REGISTRA  (F9)').on_click(None)
            self.page.on_disconnect(None)
        recorder.stop.assert_called_once()
        self.hotkeys.stop.assert_called_once()

    def test_keyboard_fallback_records_when_global_hotkeys_are_unavailable(self):
        recorder=MagicMock()
        recorder.stop.return_value=Macro.load(str(self.path)).events
        self.hotkeys.failed=['F9']
        event=SimpleNamespace(key='F9',ctrl=False,alt=False)
        with patch.object(app,'make_recorder',return_value=recorder), \
                patch.object(app.threading,'Thread'), \
                patch('macro.windows_backend.screen_geometry',return_value=[]):
            self.page.on_keyboard_event(event)
            self.page.on_keyboard_event(event)
        recorder.start.assert_called_once()
        recorder.stop.assert_called_once()
        self.assertIn('Registrazione completata',self.status_values())

    def test_primary_actions_are_outside_scroll_area(self):
        def is_inside(control,target):
            page=PageStub()
            page.controls=[control]
            return target in list(controls(page))
        scrolling=[c for c in self.items if isinstance(c,ft.Column) and c.scroll==ft.ScrollMode.AUTO]
        play=self.play_button()
        settings=self.file_button(ft.Icons.SETTINGS_ROUNDED)
        self.assertTrue(scrolling)
        self.assertTrue(all(not is_inside(c,play) for c in scrolling))
        self.assertTrue(all(not is_inside(c,settings) for c in scrolling))


if __name__=='__main__':
    unittest.main()
