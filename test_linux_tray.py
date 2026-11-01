import unittest

try:
    from jeepney import DBusAddress, new_method_call
    from macro.linux_tray import (HAVE_JEEPNEY, Item, LinuxTray, ITEM_PATH, MENU_PATH, ITEM_IFACE, MENU_IFACE, PROPS)
except ImportError:
    HAVE_JEEPNEY = False


def call(path, iface, member, signature=None, body=()):
    return new_method_call(DBusAddress(path, 'org.test.Tray', iface), member, signature, body)


@unittest.skipUnless(HAVE_JEEPNEY, 'jeepney non installato')
class TrayDispatchTests(unittest.TestCase):
    def setUp(self):
        self.actions = []
        self.checked = False
        self.tray = LinuxTray('Mouse Macro', '/opt/icons', 'icon', self.items, self.actions.append)

    def items(self):
        return [Item(1, 'Mostra pannello', 'toggle'), Item(2, None), Item(3, 'Chiudi nel tray', 'close_to_tray', self.checked),
                Item(4, 'Esci', 'quit')]

    def test_layout_lists_items_with_separator_and_checkmark(self):
        reply = self.tray.dispatch(call(MENU_PATH, MENU_IFACE, 'GetLayout', 'iias', (0, -1, [])))
        revision, (root, _props, children) = reply.body
        self.assertEqual((revision, root), (1, 0))
        ids = [child[1][0] for child in children]
        self.assertEqual(ids, [1, 2, 3, 4])
        self.assertEqual(children[1][1][1]['type'], ('s', 'separator'))
        self.assertEqual(children[2][1][1]['toggle-state'], ('i', 0))
        self.assertEqual(children[0][1][1]['label'], ('s', 'Mostra pannello'))

    def test_click_runs_the_action_and_toggle_reflects_state(self):
        self.tray.dispatch(call(MENU_PATH, MENU_IFACE, 'Event', 'isvu', (4, 'clicked', ('i', 0), 0)))
        self.tray.dispatch(call(MENU_PATH, MENU_IFACE, 'Event', 'isvu', (1, 'hovered', ('i', 0), 0)))
        self.tray.dispatch(call(MENU_PATH, MENU_IFACE, 'Event', 'isvu', (2, 'clicked', ('i', 0), 0)))  # separatore
        self.assertEqual(self.actions, ['quit'])
        self.checked = True
        reply = self.tray.dispatch(call(MENU_PATH, MENU_IFACE, 'GetGroupProperties', 'aias', ([3], [])))
        self.assertEqual(reply.body[0][0][1]['toggle-state'], ('i', 1))

    def test_activate_toggles_panel(self):
        self.tray.dispatch(call(ITEM_PATH, ITEM_IFACE, 'Activate', 'ii', (0, 0)))
        self.assertEqual(self.actions, ['toggle'])

    def test_properties(self):
        reply = self.tray.dispatch(call(ITEM_PATH, PROPS, 'GetAll', 's', (ITEM_IFACE,)))
        props = reply.body[0]
        self.assertEqual(props['Menu'], ('o', MENU_PATH))
        self.assertEqual(props['IconThemePath'], ('s', '/opt/icons'))
        self.assertFalse(props['ItemIsMenu'][1])
        one = self.tray.dispatch(call(ITEM_PATH, PROPS, 'Get', 'ss', (ITEM_IFACE, 'Status')))
        self.assertEqual(one.body[0], ('s', 'Active'))

    def test_unknown_method_gets_an_error_not_a_crash(self):
        reply = self.tray.dispatch(call(ITEM_PATH, 'org.example.Nope', 'Boh'))
        self.assertEqual(reply.header.message_type.name, 'error')

    def test_start_without_a_bus_is_a_quiet_no(self):
        import os
        old = os.environ.pop('DBUS_SESSION_BUS_ADDRESS', None)
        try:
            self.assertFalse(self.tray.start())
        finally:
            if old:
                os.environ['DBUS_SESSION_BUS_ADDRESS'] = old


if __name__ == '__main__':
    unittest.main()


@unittest.skipUnless(HAVE_JEEPNEY and __import__('shutil').which('dbus-daemon'), 'serve jeepney e dbus-daemon')
class TrayOnRealBusTests(unittest.TestCase):
    """Bus privato con un finto StatusNotifierWatcher: registrazione e menu su un vero D-Bus."""

    def test_registers_and_serves_menu(self):
        import os, subprocess, threading
        from jeepney import MessageType, new_method_return
        from jeepney.io.blocking import open_dbus_connection
        daemon = subprocess.Popen(['dbus-daemon', '--session', '--print-address', '--nofork'],
                                  stdout=subprocess.PIPE, text=True)
        self.addCleanup(daemon.terminate)
        address = daemon.stdout.readline().strip()
        old = os.environ.get('DBUS_SESSION_BUS_ADDRESS')
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = address
        self.addCleanup(lambda: os.environ.__setitem__('DBUS_SESSION_BUS_ADDRESS', old) if old
                        else os.environ.pop('DBUS_SESSION_BUS_ADDRESS', None))
        watcher = open_dbus_connection(bus='SESSION')
        watcher.send_and_get_reply(new_method_call(DBusAddress('/org/freedesktop/DBus', 'org.freedesktop.DBus',
                                   'org.freedesktop.DBus'), 'RequestName', 'su', ('org.kde.StatusNotifierWatcher', 0)))
        seen = []

        def serve():
            while True:
                try:
                    msg = watcher.receive(timeout=3)
                except Exception:
                    return
                if msg.header.message_type == MessageType.method_call and msg.body and isinstance(msg.body[0], str) \
                        and msg.body[0].startswith('io.github.realfulvio.MouseMacroStocazzSuperpower.Tray'):
                    seen.append(msg.body[0])
                    watcher.send_message(new_method_return(msg))
                    return
        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        actions = []
        tray = LinuxTray('Mouse Macro', '/opt', 'icon', lambda: [Item(1, 'Esci', 'quit')], actions.append)
        self.addCleanup(tray.stop)
        self.assertTrue(tray.start())
        thread.join(5)
        self.assertEqual(seen, [tray.service])
        client = open_dbus_connection(bus='SESSION')
        reply = client.send_and_get_reply(new_method_call(
            DBusAddress(MENU_PATH, tray.service, MENU_IFACE), 'GetLayout', 'iias', (0, -1, [])), timeout=3)
        self.assertEqual(reply.body[1][2][0][1][0], 1)
        client.send_and_get_reply(new_method_call(DBusAddress(MENU_PATH, tray.service, MENU_IFACE),
                                  'Event', 'isvu', (1, 'clicked', ('i', 0), 0)), timeout=3)
        self.assertEqual(actions, ['quit'])
