
import re

from dotfiles import dotspec


def ReadOldConfig(file):
  groups = {}
  with open(file) as f:
    read_groups(groups, (l for l in f.readlines()))
  return dotspec.ReadSpec(
    {'groups': list(groups.values())}, dotspec.DOTFILE_SPEC)



def read_groups(groups, lines):
  groupline = re.compile(r'\[\[([a-zA-Z0-9]+)\]\]( @ ([a-zA-Z0-9]+))?')
  unitline = re.compile(r'(.*) -> (.*)')
  in_group = False
  groupname = None
  host_specific = 'default'
  groupunits = {}
  while True:
    try:
      line = next(lines)
      if not line.strip():
        in_group = False
        groupname = None
        host_specific = 'default'
        continue

      if in_group:
        unit_def = unitline.match(line)
        if not unit_def:
          raise ValueError(f'bad line: {line}\nexpected "A -> B"')
        actual_name = unit_def.groups()[0].split('/')[-1]
        install = unit_def.groups()[1]
        if install.startswith('.'):
          install = f'$HOME/{install}'
        if actual_name not in  groupunits[groupname]:
          groupunits[groupname][actual_name] = {
            'name': actual_name,
            'hosts': [],
            'install': install,
            'depends': []
          }
        if host_specific not in groupunits[groupname][actual_name]['hosts']:
          groupunits[groupname][actual_name]['hosts'].append(host_specific)
        groups[groupname]['units'] = list(groupunits[groupname].values())
        continue
        

      is_new_group = groupline.match(line)
      if not is_new_group:
        raise ValueError('not spec decl, group, or empty')
      in_group = True
      groupname = is_new_group.groups()[0]
      if groupname not in groups:
        groups[groupname] = {'groupname': groupname, 'units': []}
        groupunits[groupname] = {}
      host_specific = is_new_group.groups()[2] or 'default'
    except StopIteration:
      return