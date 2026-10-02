import importlib
import inspect
import pkgutil
import warnings

from kind import builtin
from kind import core


def _get_available_mixins():
    """
    Discovers all available mixin classes in the kind.builtin and kind.core packages.
    """
    mixins = {}

    def find_mixins_in_path(path, package_name):
        for _, name, ispkg in pkgutil.iter_modules(path):
            if ispkg:
                continue

            module_name = f"{package_name}.{name}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if inspect.isclass(attr) and attr.__module__ == module_name:
                        # Heuristic to identify mixins: not a base class and not private
                        if attr_name not in ['Kind', 'BaseKind', 'LazyKind', 'GraphTraversal'] and not attr_name.startswith('_'):
                            mixins[attr_name] = attr
            except Exception as e:
                warnings.warn(f"Could not import module {module_name}: {repr(e)}")

    find_mixins_in_path(builtin.__path__, 'kind.builtin')
    find_mixins_in_path(core.__path__, 'kind.core')

    return mixins
