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
            elif event == "guide":
                self.VisualGuide(conversation_id, value)
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

    @dbus.service.signal(INTERFACE, signature="ss")
    def VisualGuide(self, conversation_id, serialized_result):
        pass

    @dbus.service.method(INTERFACE, out_signature="bbbs")
    def GetStatus(self):
        status = self.service.status()
        return (dbus.Boolean(status["api_key_configured"]),
                dbus.Boolean(status["credential_store_available"]),
                dbus.Boolean(status["live_demo"]),
                dbus.String(status["settings"]["model_id"]))

    @dbus.service.method(INTERFACE, out_signature="s")
    def GetSettings(self):
        return json.dumps(self.service.get_settings(), ensure_ascii=False)

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
        self.service.require_live_ai_data_enabled()
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
        self.service.require_live_ai_data_enabled()
        self.service.storage.add_message(str(conversation_id), str(role), str(content))
        return dbus.Boolean(True)

    @dbus.service.method(INTERFACE, in_signature="ss", out_signature="b")
    def StartGeneration(self, conversation_id, prompt):
        self.service.start_generation(str(conversation_id), str(prompt))
        return dbus.Boolean(True)

    @dbus.service.method(INTERFACE, out_signature="b")
    def CancelGeneration(self):
        return dbus.Boolean(self.service.cancel_generation())

    @dbus.service.method(INTERFACE, out_signature="s")
    def ListVisibleWindows(self):
        return json.dumps(self.service.list_visible_windows(), ensure_ascii=False)

    @dbus.service.method(INTERFACE, in_signature="u", out_signature="s")
    def CaptureActiveWindowPreview(self, window_id):
        return self.service.capture_visual_preview(int(window_id))

    @dbus.service.method(INTERFACE, in_signature="us", out_signature="s")
    def GetAccessibleControlBounds(self, window_id, target_id):
        return json.dumps(self.service.get_accessible_control_bounds(int(window_id), str(target_id)),
                          ensure_ascii=False)

    @dbus.service.method(INTERFACE, in_signature="ssss", out_signature="b")
    def StartVisualGeneration(self, conversation_id, prompt, image_data_url, context):
        self.service.start_visual_generation(str(conversation_id), str(prompt),
                                             str(image_data_url), str(context))
        return dbus.Boolean(True)

    @dbus.service.method(INTERFACE, out_signature="s")
    def ListMemories(self):
        return json.dumps(self.service.storage.list_memories(), ensure_ascii=False)

    @dbus.service.method(INTERFACE, in_signature="ssb", out_signature="u")
    def AddMemory(self, category, content, inferred):
        self.service.require_live_ai_data_enabled()
        return dbus.UInt32(self.service.storage.add_memory(str(category), str(content), bool(inferred)))

    @dbus.service.method(INTERFACE, in_signature="ussb", out_signature="b")
    def UpdateMemory(self, memory_id, category, content, inferred):
        self.service.require_live_ai_data_enabled()
        return dbus.Boolean(self.service.storage.update_memory(int(memory_id), str(category),
                                                                str(content), bool(inferred)))

    @dbus.service.method(INTERFACE, in_signature="u", out_signature="b")
    def DeleteMemory(self, memory_id):
        return dbus.Boolean(self.service.storage.delete_memory(int(memory_id)))

    @dbus.service.method(INTERFACE, out_signature="u")
    def ClearMemories(self):
        if self.service.live_demo:
            return dbus.UInt32(0)
        return dbus.UInt32(self.service.storage.clear_memories())

    @dbus.service.method(INTERFACE, out_signature="u")
    def ClearHistory(self):
        if self.service.live_demo:
            return dbus.UInt32(0)
        return dbus.UInt32(self.service.storage.clear_history())

    @dbus.service.method(INTERFACE, out_signature="s")
    def ExportData(self):
        self.service.require_live_ai_data_enabled()
        return self.service.storage.export_json()

    @dbus.service.method(INTERFACE, in_signature="uu", out_signature="s")
    def PruneData(self, history_days, memory_days):
        if self.service.live_demo:
            return json.dumps({"memories": 0, "conversations": 0})
        return json.dumps(self.service.storage.prune(int(history_days), int(memory_days)))

    @dbus.service.method(INTERFACE, out_signature="s")
    def ListInstalledApps(self):
        return json.dumps(self.service.tools.list_installed_apps(), ensure_ascii=False)

    @dbus.service.method(INTERFACE, in_signature="s", out_signature="s")
    def OpenApp(self, app_id):
        return json.dumps(self.service.tools.open_app(str(app_id)), ensure_ascii=False)

    @dbus.service.method(INTERFACE, out_signature="s")
    def GetSystemInfo(self):
        return json.dumps(self.service.tools.system_info(), ensure_ascii=False)

    @dbus.service.method(INTERFACE, in_signature="s", out_signature="s")
    def OpenURL(self, url):
        return json.dumps(self.service.tools.open_url(str(url)), ensure_ascii=False)

    @dbus.service.method(INTERFACE, in_signature="s", out_signature="s")
    def OpenSystemSetting(self, setting):
        return json.dumps(self.service.tools.open_settings(str(setting)), ensure_ascii=False)

    @dbus.service.method(INTERFACE, in_signature="s", out_signature="s")
    def OpenXfceSetting(self, setting):
        return json.dumps(self.service.tools.open_settings(str(setting)), ensure_ascii=False)


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
