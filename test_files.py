import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from macro.events import LEFT_DOWN, LEFT_UP, MOVE_ABS, MOVE_REL, Macro, MacroEvent


class MacroFileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'macro con spazi à.mmr'
        self.macro=Macro('windows',[MacroEvent(0,MOVE_ABS,x=-100,y=200),
                                    MacroEvent(.1,LEFT_DOWN,x=-100,y=200,snap='reference'),
                                    MacroEvent(.2,LEFT_UP,x=-100,y=200)],screen=[-1920,0,3840,1080])

    def test_roundtrip_preserves_events_screen_and_snapshot(self):
        self.macro.save(str(self.path))
        self.assertEqual(Macro.load(str(self.path)),self.macro)
        self.assertEqual(json.loads(self.path.read_text(encoding='utf-8'))['platform'],'windows')

    def test_saved_file_is_byte_for_byte_the_previous_format(self):
        """Faster save (no dataclasses.asdict deep copy, one-shot C encoder): same bytes as before."""
        import dataclasses
        self.macro.save(str(self.path))
        previous=json.dumps({'platform':self.macro.platform,'screen':self.macro.screen,'layout':self.macro.layout,
                             'events':[dataclasses.asdict(e) for e in self.macro.events]})
        self.assertEqual(self.path.read_text(encoding='utf-8'),previous)

    def test_events_have_no_instance_dict(self):
        """__slots__: a long recording holds hundreds of thousands of events."""
        import sys
        event=MacroEvent(0,LEFT_DOWN)
        if sys.version_info>=(3,10):
            self.assertFalse(hasattr(event,'__dict__'))
            with self.assertRaises(AttributeError):
                event.unknown=1
        self.assertEqual(MacroEvent(**{'t':1,'kind':LEFT_UP,'x':3}),MacroEvent(1,LEFT_UP,x=3))

    def test_legacy_json_without_screen_or_optional_event_fields_is_readable(self):
        self.path.write_text(json.dumps({'platform':'windows','events':[{'t':0,'kind':LEFT_DOWN}]}),encoding='utf-8')
        self.assertEqual(Macro.load(str(self.path)),Macro('windows',[MacroEvent(0,LEFT_DOWN)]))
        Macro('linux',[MacroEvent(0,MOVE_REL,dx=3,dy=-5)]).save(str(self.path))
        self.assertEqual(Macro.load(str(self.path)).events[0].dy,-5)

    def test_corrupted_structure_and_invalid_events_are_rejected(self):
        invalid=[[],{}, {'platform':'other','events':[]},
                 {'platform':'windows','events':None},
                 {'platform':'windows','events':[],'screen':[1]},
                 {'platform':'windows','events':[],'screen':[0,0,-1,1080]},
                 {'platform':'windows','events':[{'t':-1,'kind':LEFT_DOWN}]},
                 {'platform':'windows','events':[{'t':1,'kind':LEFT_DOWN},{'t':0,'kind':LEFT_UP}]},
                 {'platform':'windows','events':[{'t':float('nan'),'kind':LEFT_DOWN}]},
                 {'platform':'windows','events':[{'t':0,'kind':'unknown'}]},
                 {'platform':'windows','events':[{'t':0,'kind':MOVE_REL}]},
                 {'platform':'windows','events':[{'t':0,'kind':LEFT_DOWN,'x':'bad'}]}]
        malformed=[{'platform':'windows','events':[{'kind':LEFT_DOWN}]},
                   {'platform':'windows','events':[{'t':0,'kind':LEFT_DOWN,'extra':1}]},
                   {'platform':'windows','events':[5]}]
        for data in malformed:
            with self.subTest(data=data):
                self.path.write_text(json.dumps(data),encoding='utf-8')
                with self.assertRaises(ValueError):  # readable message, not a raw TypeError
                    Macro.load(str(self.path))
        for data in invalid:
            with self.subTest(data=data):
                self.path.write_text(json.dumps(data),encoding='utf-8')
                with self.assertRaises((ValueError,TypeError)):
                    Macro.load(str(self.path))

    def test_failed_write_preserves_previous_file_and_cleans_temporary_file(self):
        self.macro.save(str(self.path))
        before=self.path.read_bytes()
        real=tempfile.NamedTemporaryFile
        class DiskFull:  # the temporary file exists, then the write fails
            def __init__(self,**options):self.file=real(**options);self.name=self.file.name
            def __enter__(self):return self
            def __exit__(self,*exc):self.file.close()
            def write(self,text):raise OSError('Disk full')
        with patch('tempfile.NamedTemporaryFile',DiskFull):
            with self.assertRaises(OSError):
                Macro('windows',[]).save(str(self.path))
        self.assertEqual(self.path.read_bytes(),before)
        self.assertFalse(list(self.path.parent.glob('.macro-*.tmp')))

    def test_failed_replace_preserves_previous_file(self):
        self.macro.save(str(self.path))
        before=self.path.read_bytes()
        with patch('macro.events.os.replace',side_effect=PermissionError('Access denied')):
            with self.assertRaises(PermissionError):
                Macro('windows',[]).save(str(self.path))
        self.assertEqual(self.path.read_bytes(),before)
        self.assertFalse(list(self.path.parent.glob('.macro-*.tmp')))


if __name__=='__main__':
    unittest.main()
