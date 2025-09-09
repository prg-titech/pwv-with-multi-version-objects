# This file is a template for the transpiler to parse and reuse ASTs.
# It is not executed directly.
import inspect

def __init__(self, *args, **kwargs):
    # Statically inserte codes like below
    # self._v1_instance = self._V1_Impl()
    # .. (v2, v3..)

    # object.__setattr__(self, '_version_instances', [..])

    object.__setattr__(self, '_current_state', self._version_instances[0])

    try:
        self._current_state.__initialize__(*args, _wrapper_self=self, **kwargs)
    except (AttributeError, TypeError):
        # if-else chain to dispatch __initialize__ calls
        pass
