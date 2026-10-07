import unittest
from unittest.mock import patch
from macro import mouse_devices as devices


class MouseDeviceTests(unittest.TestCase):
    def test_product_names_are_cleaned_and_deduplicated(self):
        with patch.object(devices,'_device_names',return_value=['Logitech G502 HERO', 'Logitech  G502 HERO', ' ', None]):
            self.assertEqual(devices.mouse_names(),['Logitech G502 HERO'])

    def test_missing_driver_metadata_is_informational(self):
        with patch.object(devices,'_device_names',side_effect=OSError('unavailable')):
            self.assertEqual(devices.mouse_names(),[])
        self.assertEqual(devices.mouse_label([]),'Mouse: modello non disponibile')

    def test_multiple_models_are_not_reported_as_one_selected_mouse(self):
        self.assertEqual(devices.mouse_label(['Mouse A','Mouse B']),'Mouse rilevati: Mouse A (+1)')

    def test_named_models_appear_before_generic_hid_endpoints(self):
        with patch.object(devices,'_device_names',return_value=['Mouse compatibile HID','SteelSeries Prime Wireless']):
            self.assertEqual(devices.mouse_names(),['SteelSeries Prime Wireless','Mouse compatibile HID'])


if __name__ == '__main__':
    unittest.main()
