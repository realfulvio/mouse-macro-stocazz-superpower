"""Icona nell'area di notifica su Linux: StatusNotifierItem + menu dbusmenu.

Funziona dove esiste uno StatusNotifierWatcher: KDE Plasma, e GNOME con
l'estensione AppIndicator. In gamescope/Steam Deck modalità Gaming non c'è
nessuno shell con il tray: `start()` restituisce False e il programma va
avanti senza icona. Dipende solo da `jeepney` (puro Python); se manca, idem.
Le risposte D-Bus sono costruite da `dispatch()`, che si prova senza bus.
"""
from __future__ import annotations

import os
import threading

try:  # opzionale: senza tray il pannello funziona comunque
    from jeepney import DBusAddress, HeaderFields, MessageType, new_error, new_method_call, new_method_return
    from jeepney.io.blocking import open_dbus_connection
    HAVE_JEEPNEY = True
except ImportError:  # pragma: no cover - dipende dall'ambiente
    HAVE_JEEPNEY = False

ITEM_PATH, MENU_PATH = '/StatusNotifierItem', '/MenuBar'
ITEM_IFACE, MENU_IFACE = 'org.kde.StatusNotifierItem', 'com.canonical.dbusmenu'
WATCHER = ('org.kde.StatusNotifierWatcher', '/StatusNotifierWatcher')
PROPS = 'org.freedesktop.DBus.Properties'
ACTIVE_ACTIONS = ('Activate', 'SecondaryActivate')


class Item:
    """Voce di menu: id numerico stabile, testo, flag. `label None` = separatore."""

    def __init__(self, item_id, label, action=None, checked=None, enabled=True):
        self.id, self.label, self.action, self.checked, self.enabled = item_id, label, action, checked, enabled

    def props(self):
        if self.label is None:
            return {'type': ('s', 'separator')}
        props = {'label': ('s', self.label), 'enabled': ('b', self.enabled), 'visible': ('b', True)}
        if self.checked is not None:
            props['toggle-type'] = ('s', 'checkmark')
            props['toggle-state'] = ('i', 1 if self.checked else 0)
        return props


class LinuxTray:
    def __init__(self, title, icon_dir, icon_name, items, on_action):
        """`items()` restituisce la lista di Item aggiornata; `on_action(nome)` va chiamata
        dal thread D-Bus: deve solo accodare un comando, mai toccare la UI."""
        self.title, self.icon_dir, self.icon_name = title, str(icon_dir), icon_name
        self.items, self.on_action = items, on_action
        self.revision = 1
        self.registered = False
        self._conn, self._thread, self._stop = None, None, threading.Event()
        # Name under the Flatpak app id, so the sandbox may own it; watchers accept any bus name.
        self.service = f'io.github.realfulvio.MouseMacroStocazzSuperpower.Tray{os.getpid()}'

    # --- risposte D-Bus (testabili senza bus) -------------------------------------------
    def _item_properties(self):
        return {'Category': ('s', 'ApplicationStatus'), 'Id': ('s', 'mouse-macro-stocazz-superpower'),
                'Title': ('s', self.title), 'Status': ('s', 'Active'), 'WindowId': ('u', 0),
                'IconName': ('s', self.icon_name), 'IconThemePath': ('s', self.icon_dir),
                'ItemIsMenu': ('b', False), 'Menu': ('o', MENU_PATH)}

    def _menu_properties(self):
        return {'Version': ('u', 3), 'TextDirection': ('s', 'ltr'), 'Status': ('s', 'normal'),
                'IconThemePath': ('as', [])}

    def _layout(self):
        children = [('(ia{sv}av)', (item.id, item.props(), [])) for item in self.items()]
        return (0, {'children-display': ('s', 'submenu')}, children)

    def dispatch(self, msg):
        """Messaggio di risposta per una chiamata di metodo, oppure None."""
        header = msg.header
        if header.message_type != MessageType.method_call:
            return None
        path, iface, member = (header.fields.get(HeaderFields.path), header.fields.get(HeaderFields.interface),
                               header.fields.get(HeaderFields.member))
        body = msg.body
        if iface == PROPS:
            table = self._item_properties() if path == ITEM_PATH else self._menu_properties()
            if member == 'GetAll':
                return new_method_return(msg, 'a{sv}', (table,))
            if member == 'Get' and body[1] in table:
                return new_method_return(msg, 'v', (table[body[1]],))
            return new_error(msg, 'org.freedesktop.DBus.Error.UnknownProperty', 's', ('Proprietà sconosciuta',))
        if iface == 'org.freedesktop.DBus.Introspectable':
            return new_method_return(msg, 's', ('<node/>',))
        if path == ITEM_PATH and iface == ITEM_IFACE:
            if member in ACTIVE_ACTIONS:
                self.on_action('toggle')
            elif member in ('ContextMenu', 'Scroll'):
                pass  # il menu lo disegna la shell dal dbusmenu
            return new_method_return(msg)
        if path == MENU_PATH and iface == MENU_IFACE:
            if member == 'GetLayout':
                return new_method_return(msg, 'u(ia{sv}av)', (self.revision, self._layout()))
            if member == 'GetGroupProperties':
                wanted = set(body[0])
                rows = [(i.id, i.props()) for i in self.items() if not wanted or i.id in wanted]
                return new_method_return(msg, 'a(ia{sv})', (rows,))
            if member == 'AboutToShow':
                return new_method_return(msg, 'b', (False,))
            if member == 'Event':
                item_id, event = body[0], body[1]
                if event == 'clicked':
                    self.click(item_id)
                return new_method_return(msg)
            if member == 'EventGroup':
                for item_id, event, _data, _time in body[0]:
                    if event == 'clicked':
                        self.click(item_id)
                return new_method_return(msg, 'ai', ([],))
            if member == 'AboutToShowGroup':
                return new_method_return(msg, 'aiai', ([], []))
        return new_error(msg, 'org.freedesktop.DBus.Error.UnknownMethod', 's', ('Metodo sconosciuto',))

    def click(self, item_id):
        for item in self.items():
            if item.id == item_id and item.action and item.enabled:
                self.on_action(item.action)

    # --- connessione ---------------------------------------------------------------------
    def start(self):
        """Prova a registrare l'icona. True se una shell con tray l'ha accettata."""
        if not HAVE_JEEPNEY or not os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
            return False
        try:
            self._conn = open_dbus_connection(bus='SESSION')
            self._conn.send_and_get_reply(new_method_call(
                DBusAddress('/org/freedesktop/DBus', 'org.freedesktop.DBus', 'org.freedesktop.DBus'),
                'RequestName', 'su', (self.service, 4)))
            self.registered = self._register()
        except Exception:
            self.stop()
            return False
        if not self.registered:
            self.stop()
            return False
        self._thread = threading.Thread(target=self._serve, daemon=True, name='tray')
        self._thread.start()
        return True

    def _register(self):
        reply = self._conn.send_and_get_reply(new_method_call(
            DBusAddress(WATCHER[1], WATCHER[0], WATCHER[0]), 'RegisterStatusNotifierItem', 's', (self.service,)),
            timeout=3)
        return reply.header.message_type == MessageType.method_return

    def _serve(self):
        conn = self._conn
        while not self._stop.is_set():
            try:
                msg = conn.receive(timeout=0.5)
            except TimeoutError:
                continue
            except Exception:
                break
            try:
                reply = self.dispatch(msg)
                if reply is not None:
                    conn.send_message(reply)
            except Exception:
                pass  # un messaggio strano non deve far morire il tray

    def refresh(self):
        """Da chiamare quando cambiano le voci (es. spunta): avvisa la shell."""
        self.revision += 1

    def stop(self):
        self._stop.set()
        conn, self._conn = self._conn, None
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        self.registered = False
