def _ensure_common_state(bus):
    if not hasattr(bus, "_event_shadow_records"):
        bus._event_shadow_records = {}
    if not hasattr(bus, "_next_token"):
        bus._next_token = 1
    if not hasattr(bus, "_next_order"):
        bus._next_order = 1
    if not hasattr(bus, "_sync_v1_to_v2_count"):
        bus._sync_v1_to_v2_count = 0
    if not hasattr(bus, "_sync_v2_to_v1_count"):
        bus._sync_v2_to_v1_count = 0

def _new_record(token, callback, priority, order):
    return {
        "token": token,
        "callback": callback,
        "priority": priority,
        "order": order,
        "active": True,
    }

def _find_active_record(records, callback):
    for record in records:
        if record["callback"] == callback and record["active"]:
            return record
    return None

def _find_inactive_record(records, callback):
    for record in records:
        if record["callback"] == callback and not record["active"]:
            return record
    return None

def _activate_legacy_record(bus, event_name, callback):
    _ensure_common_state(bus)
    records = bus._event_shadow_records.setdefault(event_name, [])
    active_record = _find_active_record(records, callback)
    if active_record is not None:
        return active_record

    inactive_record = _find_inactive_record(records, callback)
    if inactive_record is not None:
        inactive_record["active"] = True
        return inactive_record

    record = _new_record(bus._next_token, callback, 0, bus._next_order)
    bus._next_token += 1
    bus._next_order += 1
    records.append(record)
    return record

def _deactivate_legacy_record(bus, event_name, callback):
    _ensure_common_state(bus)
    records = bus._event_shadow_records.get(event_name, [])
    for record in records:
        if record["callback"] == callback and record["active"]:
            record["active"] = False
            return True
    return False

class EventBus__1__:
    def __init__(self):
        self._listeners = {}
        self._event_shadow_records = {}
        self._next_token = 1
        self._next_order = 1
        self._sync_v1_to_v2_count = 0
        self._sync_v2_to_v1_count = 0

    def on(self, event_name, callback):
        listeners = self._listeners.setdefault(event_name, [])
        if callback not in listeners:
            listeners.append(callback)
        _activate_legacy_record(self, event_name, callback)

    def off(self, event_name, callback):
        listeners = self._listeners.get(event_name, [])
        updated = []
        removed = False
        for existing_callback in listeners:
            if not removed and existing_callback == callback:
                removed = True
                continue
            updated.append(existing_callback)

        if updated:
            self._listeners[event_name] = updated
        elif event_name in self._listeners:
            del self._listeners[event_name]

        _deactivate_legacy_record(self, event_name, callback)
        return removed

    def emit(self, event_name, payload):
        for callback in list(self._listeners.get(event_name, [])):
            callback(payload)

class EventBus__2__:
    def __init__(self):
        self._subscribers = {}
        self._token_index = {}
        self._event_shadow_records = {}
        self._next_token = 1
        self._next_order = 1
        self._sync_v1_to_v2_count = 0
        self._sync_v2_to_v1_count = 0

    def subscribe(self, event_name, callback, priority=0):
        records = self._subscribers.setdefault(event_name, [])
        token = self._next_token
        order = self._next_order
        self._next_token += 1
        self._next_order += 1

        record = _new_record(token, callback, priority, order)
        records.append(record)
        records.sort(key=lambda item: (-item["priority"], item["order"]))
        self._token_index[token] = record

        shadow_records = self._event_shadow_records.setdefault(event_name, [])
        shadow_records.append(record.copy())
        return token

    def unsubscribe(self, token):
        record = self._token_index.pop(token, None)
        if record is None:
            return False

        record["active"] = False
        for event_name, records in self._subscribers.items():
            kept = [item for item in records if item["active"]]
            if kept:
                self._subscribers[event_name] = kept
            else:
                self._subscribers[event_name] = []

            shadow_records = self._event_shadow_records.get(event_name, [])
            for shadow_record in shadow_records:
                if shadow_record["token"] == token and shadow_record["active"]:
                    shadow_record["active"] = False
                    break
        return True

    def publish(self, event_name, payload):
        for record in list(self._subscribers.get(event_name, [])):
            record["callback"](payload)
