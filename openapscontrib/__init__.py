
"""
Virtual Namespace for 3rd party openaps contributions
"""
from pkg_resources import declare_namespace
from pkgutil import extend_path


__path__ = extend_path(__path__, __name__)
declare_namespace(__name__)
