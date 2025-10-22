# This file is a template for the transpiler to parse and reuse ASTs.
# It is not executed directly.
import contextlib
@contextlib.contextmanager
def version_lock(self, target_version_num):
    """
    A context manager to temporarily disable version switching.
    """
    # 1. Record the original state
    original_version_num = self._current_state._version_number
    original_locking_state = self._version_locking

    try:
        # 2. Switch to the target version
        #    - if already locked, temporarily unlock
        if original_locking_state:
            self._version_locking = False
        self._switch_to_version(target_version_num)
        self._version_locking = True

        # 3. Run the 'with' block
        yield

    finally:
        # 4. Postprocessing after exiting the 'with' block
        if original_locking_state is False:
            self._version_locking = False
        
        else:
            self._version_locking = False
            self._switch_to_version(original_version_num)
            self._version_locking = True