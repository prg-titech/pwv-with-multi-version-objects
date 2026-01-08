@[ATTR].setter
def [ATTR](self, value):
    try:
        self._[ATTR]
    except AttributeError:
        self._test_switch_to_version([VERSION])
    self._[ATTR] = value

