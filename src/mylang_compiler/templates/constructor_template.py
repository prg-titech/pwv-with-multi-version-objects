# This file is a template for the transpiler to parse and reuse ASTs.
# It is not executed directly.
import inspect

def __init__(self, *args, **kwargs):
    # Statically inserte codes like below
    # self._v1_instance = self._V1_Impl()
    # .. (v2, v3..)

    # self._version_instances = [..]

    # self._current_state = self._v1_instance

    try:
        self._current_state.__initialize__(*args, **kwargs)
    except (AttributeError, TypeError):
        # if-else chain to dispatch __initialize__ calls
        pass
