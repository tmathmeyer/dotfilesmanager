
from collections import namedtuple

from impulse.core import debug


PACKAGE_SPEC = {
  'arch': str,
  'debian': str,
}


SOURCE_SPEC = {
  'repo': str,
  'command': str,
}


TARGET_SPEC = {
  'pkg': [PACKAGE_SPEC],
  'src': SOURCE_SPEC,
}


DEPENDS_SPEC = {
  'type': str,
  'target': TARGET_SPEC,
}


UNIT_SPEC = {
  'name': str,
  'hosts': [str],
  'install': str,
  'depends': [DEPENDS_SPEC],
}


GROUP_SPEC = {
  'groupname': str,
  'units': [UNIT_SPEC]
}


DOTFILE_SPEC = {
  'groups': [GROUP_SPEC]
}


def ToGlob(obj):
  if type(obj) in (int, str):
    return obj
  if type(obj) == list:
    return [ToGlob(o) for o in obj]
  if obj.__class__.__name__ == '_spec':
    return obj.glob()
  return None


def GetType(spec):
  keys = ['spec', *spec.keys()]
  class _spec(namedtuple('JSONTYPE', keys)):
    def glob(self):
      return {k:ToGlob(getattr(self, k)) for k,v in self.spec.items()}
    def __str__(self):
      return str({k:getattr(self,k) for k in self.spec})
    def __repr__(self):
      return str(self)
  def wrapper(*args, **kwargs):
    return _spec(spec, *args, **kwargs)
  return wrapper


def ReadSpec(content, spec):
  def TypeMismatch(a, b):
    if debug.IsDebug():
      raise TypeError(f'{a}\nDoes not match\n{b}')
    raise TypeError(
      f'content type({type(a)}) does not match {type(b)}')

  if type(content) == list:
    if type(spec) != list:
      TypeMismatch(content, spec)
    return [ReadSpec(c, spec[0]) for c in content]

  if type(content) == dict:
    if type(spec) != dict:
      TypeMismatch(content, spec)
    evaluated = {k: ReadSpec(content.get(k, None), v) for k,v in spec.items()}
    return GetType(spec)(**evaluated)

  if spec == int:
    return int(content)

  if spec == str:
    return str(content)

  raise ValueError(f'No matched type for {spec}')



Package = GetType(PACKAGE_SPEC)
Source = GetType(SOURCE_SPEC)
Target = GetType(TARGET_SPEC)
Depends = GetType(DEPENDS_SPEC)
Group = GetType(GROUP_SPEC)
Unit = GetType(UNIT_SPEC)
Dotfile = GetType(DOTFILE_SPEC)