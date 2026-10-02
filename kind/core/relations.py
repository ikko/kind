from kind.builtin.collections import OrderedKindSet

class Relations:
    def __init__(self, owner):
        self._owner = owner
        self._relations = {}

    def __getattr__(self, how):
        if how.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{how}'")

        def relation_proxy(*args, **kwargs):
            if not args and not kwargs:
                raise TypeError(f"'{how}' relation requires at least one argument or keyword argument.")

            # Handle positional arguments
            for arg in args:
                try:
                    kind_arg = self._owner.from_object(arg) # Convert to Kind
                except TypeError:
                    raise TypeError(f"Cannot convert positional argument '{arg}' to Kind for '{how}' relation.")
                self._owner.relate(kind_arg, how=how)

            # Handle keyword arguments
            for key, value in kwargs.items():
                if isinstance(value, list):
                    for item in value:
                        try:
                            kind_item = self._owner.from_object(item) # Convert to Kind
                        except TypeError:
                            raise TypeError(f"Cannot convert list item '{item}' to Kind for '{key}' relation.")
                        self._owner.relate(kind_item, how=key)
                else:
                    try:
                        kind_value = self._owner.from_object(value) # Convert to Kind
                    except TypeError:
                        raise TypeError(f"Cannot convert keyword argument value '{value}' to Kind for '{key}' relation.")
                    self._owner.relate(kind_value, how=key)
            return self._owner

        return relation_proxy

    def add(self, how, related_kind):
        """Strong, ordered references: a relation keeps its target alive, like a child link does."""
        if how not in self._relations:
            self._relations[how] = OrderedKindSet(guard=self._owner._ensure_mutable)
        self._relations[how].add(related_kind)

    def get(self, how):
        """The Kinds related under `how`; an empty, unattached set if there are none."""
        return self._relations.get(how, OrderedKindSet())

    def remove(self, how, related_kind):
        if how in self._relations:
            self._relations[how].discard(related_kind)
            if not self._relations[how]:
                del self._relations[how]

    def items(self):
        return self._relations.items()

    def __iter__(self):
        return iter(self._relations)

    def __len__(self):
        return len(self._relations)

    def __repr__(self):
        return f"<Relations of {self._owner.name}>"