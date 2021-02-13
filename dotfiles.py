
import json
import os

from dotfiles import dotspec
from dotfiles import converter

from impulse.args import args
from impulse.core import debug


command = args.ArgumentParser(complete=True)
repo_location = os.path.join(os.environ['HOME'], '.dotfiles')


def CheckUnit(group, unit):
  hostname = os.uname()[1]
  expected_link = hostname if hostname in unit.hosts else 'default'
  expected_link = os.path.join(expected_link, unit.name)    
  expected_link = os.path.join(repo_location, group.groupname, expected_link)
  actual_file = unit.install.replace('$HOME', os.environ['HOME'])
  if not os.path.exists(actual_file):
    # Either does not exist, or is a _broken_ symlink
    if os.path.islink(actual_file):
      return '!!', actual_file, expected_link
    return '!', actual_file, expected_link
  if not os.path.islink(actual_file):
    return '*', actual_file, expected_link
  if os.readlink(actual_file) != expected_link:
    return '~', actual_file, expected_link
  return 'OK', actual_file, expected_link


def GetConfig():
  if not os.path.exists(repo_location):
    print('no dotfiles installation. exiting...')
    return
  dotfiles_info = os.path.join(repo_location, 'dotfiles.json')
  if not os.path.exists(dotfiles_info):
    print('no dotfiles installation. exiting...')
    return
  with open(dotfiles_info) as f:
    return dotspec.ReadSpec(json.loads(f.read()), dotspec.DOTFILE_SPEC)


@command
def init():
  if os.path.exists(repo_location):
    print('dotfiles directory already exists, exiting...')
    return
  os.makedirs(repo_location)
  with open(os.path.join(repo_location, 'dotfiles.json'), 'w') as f:
    f.write('[]')


@command
def convert():
  if not os.path.exists(repo_location):
    print('no existing dotfiles installation. exiting...')
    return

  dotfiles_info = os.path.join(repo_location, 'dotfiles')
  if not os.path.exists(dotfiles_info):
    print('no existing dotfiles installation. exiting...')
    return

  with open(os.path.join(repo_location, 'dotfiles.json'), 'w') as f:
    config = converter.ReadOldConfig(dotfiles_info)
    f.write(json.dumps(dotspec.ToGlob(config), indent=2))
    f.write('\n')


@command
def info(inspect:str='groups'):
  config = GetConfig()
  for seg in inspect.split(':'):
    if type(config) is list:
      index = int(seg)
      if index < len(config):
        config = config[index]
      else:
        print(f'invalid index {index} in {config}')
        return
      continue
    cfg = getattr(config, seg, None)
    if cfg is None:
      print(f'invalid {seg} in {config.__slots__}')
      return
    config = cfg
  print(config)


@command
def status(showall:bool=False):
  hostname = os.uname()[1]
  config = GetConfig()
  for group in config.groups:
    for unit in group.units:
      status, _, link = CheckUnit(group, unit)
      if showall or status != 'OK':
        print(f'[{status}] {unit.install} -> {link}')


@command
def sync(group:str=None):
  hostname = os.uname()[1]
  config = GetConfig()
  for g in config.groups:
    if group is not None and g.groupname != group:
      continue
    for unit in g.units:
      status, link_from, link_to = CheckUnit(g, unit)
      if 'OK' in status:
        print(f'Skipping {g.groupname}/{unit.name} [OK]')
      elif status in ('~', '!!'):
        print(f'Creating link {link_from} -> {link_to}')
        os.system(f'rm {link_from} && ln -s {link_to} {link_from}')
      elif status == '!':
        print(f'Creating link {link_from} -> {link_to}')
        os.system(f'ln -s {link_to} {link_from}')
      elif status == '*':
        print(f'Skipping {g.groupname}/{unit.name}')
        print('file exists and is not a symlink. please check manually')


@command
def mkhosted(dotfile:str, group:str):
  config = GetConfig()
  grps = [g for g in config.groups if g.groupname == group]
  if not grps:
    print(f'Invalid group: {group}')
    return
  grp = grps[0]
  units = [u for u in grp.units if u.name == dotfile]
  if not units:
    avail = [u.name for u in grp.units]
    print(f'Invalid dotfile: {dotfile}. Choose from {avail}')
    return
  hostname = os.uname()[1]
  unit = units[0]
  if hostname in unit.hosts:
    print(f'Already a host specific entry for {dotfile}@{hostname}')
    return

  status, linkname, oldentry = CheckUnit(grp, unit)
  if status != 'OK':
    print(f'Invalid dotfile setup: [{status}]')
    return

  newentry = os.path.join(repo_location, group, hostname, dotfile)
  os.system(f'mkdir -p {os.path.dirname(newentry)}')
  os.system(f'cp {oldentry} {newentry}')
  unit.hosts.append(hostname)
  with open(os.path.join(repo_location, 'dotfiles.json'), 'w') as f:
    f.write(json.dumps(dotspec.ToGlob(config), indent=2))
    f.write('\n')
  os.system(f'rm {linkname} && ln -s {newentry} {linkname}')



@command
def track(dotfile:args.File, group:str, host:bool=False, rename:str=None):
  dotfile = dotfile.value()
  if not os.path.exists(dotfile) or os.path.islink(dotfile):
    print('Can only track a non-link existing file')
    return

  config = GetConfig()
  grp = None
  for g in config.groups:
    if g.groupname == group:
      grp = g
      break

  if grp == None:
    grp = dotspec.GetType(dotspec.GROUP_SPEC)(group, [])
    config.groups.append(grp)

  name = dotfile.split('/')[-1].strip()
  if name.startswith('.'):
    name = name[1:].strip()

  if rename is not None:
    name = rename

  for unit in grp.units:
    if unit.name == name:
      print('dotfile already exists, cant overwrite')
      return

  unit = dotspec.GetType(dotspec.UNIT_SPEC)(name, ['default'], dotfile, [])
  hostname = 'default'
  if host:
    hostname = os.uname()[1]
    unit.hosts.append(hostname)
    print(f'WARNING: creating stub file {name} in {group}/default')

  destination = os.path.join(repo_location, group, hostname, name)
  grp.units.append(unit)

  with open(os.path.join(repo_location, 'dotfiles.json'), 'w') as f:
    f.write(json.dumps(dotspec.ToGlob(config), indent=2))
    f.write('\n')

  os.system(
    f'mkdir -p {os.path.dirname(destination)} && '
    f'mv {dotfile} {destination} && '
    f'ln -s {destination} {dotfile}')



def main():
  command.eval()
