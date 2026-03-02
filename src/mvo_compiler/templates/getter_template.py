@property
def [ATTR](self):
    try:
        _mvo_value = self._[ATTR]
    except AttributeError:
        self._SWITCH_TO_VERSION_PLACEHOLDER([VERSION])
        _mvo_value = self._[ATTR]
    self._MVO_RECORD_ACCESS_PLACEHOLDER("attr_read", "[ATTR]")
    return _mvo_value
