# This file is a template for the transpiler to parse and reuse ASTs.
# It is not executed directly.
def _switch_to_version(self, version_num):
    if self._version_locking:
        print(f"[Warning] Cannot switch versions to {version_num}.")
        print(f"          Since version locking is enabled, the current version {self._current_state._version_number} will be used.")
        return
    
    current_version_num = self._current_state._version_number

    _SYNC_CALL_PLACEHOLDER_ = None

    self._current_state = self._VERSION_INSTANCES_SINGLETON[version_num - 1]
