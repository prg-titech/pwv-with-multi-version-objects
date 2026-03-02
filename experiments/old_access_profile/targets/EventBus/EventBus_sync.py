def _ensure_common_state(wrapper_obj):
    if not hasattr(wrapper_obj, "_event_shadow_records"):
        wrapper_obj._event_shadow_records = {}
    if not hasattr(wrapper_obj, "_next_token"):
        wrapper_obj._next_token = 1
    if not hasattr(wrapper_obj, "_next_order"):
        wrapper_obj._next_order = 1
    if not hasattr(wrapper_obj, "_sync_v1_to_v2_count"):
        wrapper_obj._sync_v1_to_v2_count = 0
    if not hasattr(wrapper_obj, "_sync_v2_to_v1_count"):
        wrapper_obj._sync_v2_to_v1_count = 0

def _sync_from_v1_to_v2(wrapper_obj):
    _ensure_common_state(wrapper_obj)
    wrapper_obj._sync_v1_to_v2_count += 1

    if not wrapper_obj._event_shadow_records:
        listeners = getattr(wrapper_obj, "_listeners", {})
        for event_name, callbacks in listeners.items():
            records = []
            for callback in callbacks:
                records.append({
                    "token": wrapper_obj._next_token,
                    "callback": callback,
                    "priority": 0,
                    "order": wrapper_obj._next_order,
                    "active": True,
                })
                wrapper_obj._next_token += 1
                wrapper_obj._next_order += 1
            wrapper_obj._event_shadow_records[event_name] = records

    subscribers = {}
    token_index = {}
    for event_name, records in wrapper_obj._event_shadow_records.items():
        active_records = [record.copy() for record in records if record["active"]]
        active_records.sort(key=lambda record: (-record["priority"], record["order"]))
        subscribers[event_name] = active_records
        for record in active_records:
            token_index[record["token"]] = record

    wrapper_obj._subscribers = subscribers
    wrapper_obj._token_index = token_index

def _sync_from_v2_to_v1(wrapper_obj):
    _ensure_common_state(wrapper_obj)
    wrapper_obj._sync_v2_to_v1_count += 1

    shadow_records = {}
    for event_name, records in getattr(wrapper_obj, "_event_shadow_records", {}).items():
        shadow_records[event_name] = [record.copy() for record in records]

    if not shadow_records:
        for event_name, records in getattr(wrapper_obj, "_subscribers", {}).items():
            shadow_records[event_name] = [record.copy() for record in records]

    listeners = {}
    for event_name, records in shadow_records.items():
        active_records = [record for record in records if record["active"]]
        active_records.sort(key=lambda record: record["order"])
        listeners[event_name] = [record["callback"] for record in active_records]

    wrapper_obj._event_shadow_records = shadow_records
    wrapper_obj._listeners = listeners
