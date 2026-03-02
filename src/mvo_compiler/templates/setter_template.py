@[ATTR].setter
def [ATTR](self, value):
    try:
        self._[ATTR]
    except AttributeError:
        self._SWITCH_TO_VERSION_PLACEHOLDER([VERSION])
    self._MVO_RECORD_ACCESS_PLACEHOLDER("attr_write", "[ATTR]")
    self._[ATTR] = value
