# This file is a template for the transpiler to parse and reuse ASTs.
# It is not executed directly.
import re

def __setattr__(self, name, value):
    # Handle special attributes that should not be set directly
    _INTERNAL_INSTANCE_VAR_PATTERN = re.compile(r"^_v\d+_instance$")
    if name == '_current_state' or name == '_version_instances' or _INTERNAL_INSTANCE_VAR_PATTERN.match(name):
        object.__setattr__(self, name, value)
        return

    # 1. Search the attribute in the current version implementation
    if hasattr(self._current_state, name):
        setattr(self._current_state, name, value)
        return
    
    # 2. If not found, search other versions
    for impl_instance in self._version_instances:
        if impl_instance is not self._current_state and hasattr(impl_instance, name):
            version_num = impl_instance._version_number
            self._switch_to_version(version_num)
            setattr(impl_instance, name, value)
            return

    # 3. If not found in any version, set it as a new attribute in the current state
    setattr(self._current_state, name, value)
