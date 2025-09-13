# This file is a template for the transpiler to parse and reuse ASTs.
# It is not executed directly.
def _switch_to_version(self, version_num):
    current_version_num = self._current_state._version_number

    sync_method_name = f"_sync_from_v{current_version_num}_to_v{version_num}"
    
    if hasattr(self, sync_method_name):
        sync_method = getattr(self, sync_method_name)
        sync_method(self)

    self._current_state = self._VERSION_INSTANCES_SINGLETON[version_num - 1]
