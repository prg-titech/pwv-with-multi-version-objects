# This file is a template for the transpiler to parse and reuse ASTs.
# It is not executed directly.
def __init__(self, *args, **kwargs):
    
    self._current_state = self._VERSION_INSTANCES_SINGLETON[0]

    try:
        self._current_state.__initialize__(*args, _wrapper_self=self, **kwargs)
    except (AttributeError, TypeError):
        # if-else chain to dispatch __initialize__ calls
        pass
