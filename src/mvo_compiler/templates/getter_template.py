@property
def [ATTR](self):
    try:
        return self._[ATTR]
    except AttributeError:
        self._test_switch_to_version([VERSION])
        return self._[ATTR]

