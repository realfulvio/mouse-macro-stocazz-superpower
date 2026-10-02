import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from macro.engine import PlaybackOptions
from macro.playback_trace import PlaybackTrace


class TraceTests(unittest.TestCase):
    def test_bounded_records_keep_full_counts_without_site_confirmation(self):
        trace=PlaybackTrace(limit=1)
        record={'type':'input_sent','kind':'left_down','cycle':2}
        trace.record(record)
        trace.record({'type':'input_sent','kind':'left_up'})
        record['kind']='changed'
        with tempfile.TemporaryDirectory() as folder:
            path=trace.save(Path(folder),'v0.15 beta',PlaybackOptions(),{},'done')
            data=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(data['measurement'],'input_sent_only')
            self.assertIsNone(data['site_actions_confirmed'])
            self.assertEqual(data['counts']['input_sent'],2)
            self.assertEqual(data['counts']['left_down'],1)
            self.assertEqual(data['counts']['left_up'],1)
            self.assertEqual(data['records'][0]['kind'],'left_down')
            self.assertEqual(data['dropped_records'],1)
            self.assertEqual(data['settings']['min_action_gap_seconds'],.15)
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])

    def test_each_run_gets_its_own_report(self):
        with tempfile.TemporaryDirectory() as folder:
            trace=PlaybackTrace()
            first=trace.save(Path(folder),'v0.15 beta',PlaybackOptions(),{},'stopped')
            second=trace.save(Path(folder),'v0.15 beta',PlaybackOptions(),{},'error','test failure')
            self.assertNotEqual(first,second)
            self.assertEqual(json.loads(first.read_text())['outcome'],'stopped')
            self.assertEqual(json.loads(second.read_text())['error'],'test failure')

    def test_save_failure_leaves_no_partial_report(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('macro.playback_trace.os.replace',side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    PlaybackTrace().save(Path(folder),'v0.15 beta',PlaybackOptions(),{},'done')
            self.assertEqual(list(Path(folder).iterdir()),[])
