import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('resource_tools', Path(__file__).resolve().parents[1] / 'ci/resource_tools.py')
resources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resources)


class ResourceSummaryTests(unittest.TestCase):
    def test_cpu_uses_elapsed_time_and_private_memory_is_peak(self):
        rows = [dict(t_s='0', procs='1', cpu_pct_of_core='', private_mb='3'),
                dict(t_s='1', procs='1', cpu_pct_of_core='10', private_mb='4'),
                dict(t_s='3', procs='2', cpu_pct_of_core='40', private_mb='7')]
        result = resources.summarize_resources(rows)
        self.assertEqual(result['cpu_core_pct_mean'], 30)
        self.assertEqual(result['private_mib_max'], 7)
        self.assertEqual(result['observed_seconds'], 3)

    def test_disappeared_process_is_not_zero_cpu(self):
        rows = [dict(t_s='0', procs='1', cpu_pct_of_core='', private_mb='3'),
                dict(t_s='1', procs='0', cpu_pct_of_core='0', private_mb='0')]
        with self.assertRaisesRegex(ValueError, 'processo assente'):
            resources.summarize_resources(rows)


if __name__ == '__main__':
    unittest.main()
