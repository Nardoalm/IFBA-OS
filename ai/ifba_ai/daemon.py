"""D-Bus session service for IFBA OS assistant state."""

import json
import sys

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib
except ImportError:
    sys.stderr.write("IFBA AI service requires the system D-Bus and GLib Python bindings.\n")
    raise SystemExit(1)

from .service import AssistantService


BUS_NAME = "org.ifba.OS.AI"
OBJECT_PATH = "/org/ifba/OS/AI"
INTERFACE = "org.ifba.OS.AI1"


class AssistantObject(dbus.service.Object):
    def __init__(self, bus, service):
        self.service = service
        super().__init__(bus, OBJECT_PATH)

    def publish(self, event, conversation_id, value):
        def emit_on_main_loop():
            if event == "delta":
                self.MessageDelta(conversation_id, value)
            elif event == "finished":
                self.GenerationFinished(conversation_id, value)
            else:
                self.GenerationFailed(conversation_id, value)
            return False
        GLib.idle_add(emit_on_main_loop)

    @dbus.service.signal(INTERFACE, signature="ss")
    def MessageDelta(self, conversation_id, text):
        pass

    @dbus.service.signal(INTERFACE, signature="ss")
    def GenerationFinished(self, conversation_id, state):
        pass

    @dbus.service.signal(INTERFACE, signature="ss")
    def GenerationFailed(self, conversation_id, message):
        pass

    @dbus.service.method(INTERFACE, out_signature="bbs")
    def GetStatus(self):
        status = self.service.status()
        return (dbus.Boolean(status["api_key_configured"]),
                dbus.Boolean(status["credential_store_available"]),
                dbus.String(status["settings"]["model_id"]))

    @dbus.service.method(INTERFACE, out_signature="s")
    def GetSettings(self):
        return json.dumps(self.service.settings.read(), ensure_ascii=False)

    @dbus.service.method(INTERFACE, in_signature="s", out_signature="b")
    def SaveSettings(self, serialized):
        self.service.save_settings(str(serialized))
        return dbus.Boolean(True)

    @dbus.service.method(INTERFACE, in_signature="s", out_signature="b")
    def StoreApiKey(self, secret):
        self.service.store_api_key(str(secret))
        return dbus.Boolean(True)

    @dbus.service.method(INTERFACE, out_signature="b")
    def DeleteApiKey(self):
        self.service.delete_api_key()
        return dbus.Boolean(True)

    @dbus.service.method(INTERFACE, in_signature="s", out_signature="s")
    def CreateConversation(self, title):
        return dbus.String(self.service.storage.create_conversation(str(title)))

    @dbus.service.method(INTERFACE, out_signature="a(sss)")
    def ListConversations(self):
        rows = self.service.storage.list_conversations()
        return [(dbus.String(row["id"]), dbus.String(row["title"]),
                 dbus.String(row["updated_at"])) for row in rows]

    @dbus.service.method(INTERFACE, in_signature="s", out_signature="a(sss)")
    def ListMessages(self, conversation_id):
        rows = self.service.storage.list_messages(str(conversation_id))
        return [(dbus.String(row["role"]), dbus.String(row["content"]),
                 dbus.String(row["created_at"])) for row in rows]

    @dbus.service.method(INTERFACE, in_signature="sss", out_signature="b")
    def AddMessage(self, conversation_id, role, content):
        self.service.storage.add_message(str(conversation_id), str(role), str(content))
        return dbus.Boolean(True)

    @dbus.service.method(INTERFACE, in_signature="ss", out_signature="b")
    def StartGeneration(self, conversation_id, prompt):
        self.service.start_generation(str(conversation_id), str(prompt))
        return dbus.Boolean(True)

    @dbus.service.method(INTERFACE, out_signature="b")
    def CancelGeneration(self):
        return dbus.Boolean(self.service.cancel_generation())


def main():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    name = dbus.service.BusName(BUS_NAME, bus)
    service = AssistantService()
    obj = AssistantObject(bus, service)
    service.emit = obj.publish
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
