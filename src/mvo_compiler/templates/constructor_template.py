# This file is a template for the transpiler to parse and reuse ASTs.
# It is not executed directly.
def __init__(self, *args, **kwargs):

    self._CURRENT_STATE_PLACEHOLDER = self._VERSION_INSTANCES_SINGLETON_PLACEHOLDER[0]

    try:
        self._CURRENT_STATE_PLACEHOLDER.__initialize__(*args, _wrapper_self=self, **kwargs)
    except (AttributeError, TypeError):
        # if-else chain to dispatch __initialize__ calls
        pass
