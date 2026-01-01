from dictionary import Entry, Dictionary


class _IdEntry__1__(Entry):
    def match(self, hash_, key):
        return self.hash == hash_ and self.key is key


class IdentityDictionary__1__(Dictionary):
    def _new_entry(self, key, value, hash_):
        return _IdEntry__1__(hash_, key, value, None)