import logging
from collections import defaultdict

PLUG_IN_MANAGERS = {}
CACHED_PLUGIN_INFO = defaultdict(list)

log = logging.getLogger(__name__)


class PluginManager(object):

    def __init__(self, plugin_type):
        self.name = plugin_type
        self.registry = defaultdict(list)
        self._logger = logging.getLogger(
            self.__class__.__module__ + '.' + self.__class__.__name__)
        register_class(self)

    def load_me_later(self, meta, module_name):
        self._logger.debug('load me later: ' + module_name)
        self._logger.debug(meta)

    def load_me_now(self, key, **keywords):
        self._logger.debug("load me now:" + key)
        if keywords:
            self._logger.debug(keywords)

    def dynamic_load_library(self, library_import_path):
        self._logger.debug("import " + library_import_path[0])
        return do_import(library_import_path[0])

    def register_a_plugin(self, cls):
        self._logger.debug("register " + cls.__name__)


def register_class(cls):
    log.debug("register " + cls.name)
    PLUG_IN_MANAGERS[cls.name] = cls
    if cls.name in CACHED_PLUGIN_INFO:
        # check if there is early registrations or not
        for plugin_info, module_name in CACHED_PLUGIN_INFO[cls.name]:
            cls.load_me_later(plugin_info, module_name)

        del CACHED_PLUGIN_INFO[cls.name]


class Plugin(type):
    """sole class registry"""
    def __init__(cls, name, bases, nmspc):
        super(Plugin, cls).__init__(
            name, bases, nmspc)
        register_a_plugin(cls)


def register_a_plugin(cls):
    manager = PLUG_IN_MANAGERS.get(cls.name)
    if manager:
        manager.register_a_plugin(cls)
    else:
        raise Exception("%s has no registry" % cls.name)


def load_me_later(plugin_info):
    log.debug(plugin_info)
    manager = PLUG_IN_MANAGERS.get(plugin_info.name)
    if manager:
        manager.load_me_later(plugin_info)
    else:
        # let's cache it and wait the manager to be registered
        CACHED_PLUGIN_INFO[plugin_info.name].append(plugin_info)


def do_import(plugin_module_name):
    try:
        plugin_module = __import__(plugin_module_name)
        if '.' in plugin_module_name:
            modules = plugin_module_name.split('.')
            for module in modules[1:]:
                plugin_module = getattr(plugin_module, module)
        return plugin_module
    except ImportError:
        log.debug("Failed to import %s" % plugin_module_name)
        raise


def with_metaclass(meta, *bases):
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instantiation that replaces
    # itself with the actual metaclass.  Because of internal type checks
    # we also need to make sure that we downgrade the custom metaclass
    # for one level to something closer to type (that's why __call__ and
    # __init__ comes back from type etc.).
    #
    # This has the advantage over six.with_metaclass in that it does not
    # introduce dummy classes into the final MRO.
    # :copyright: (c) 2014 by Armin Ronacher.
    # :license: BSD, see LICENSE for more details.
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)
    return metaclass('temporary_class', None, {})
