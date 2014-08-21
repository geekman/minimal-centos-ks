#!/usr/bin/python
#
# modtrim.py - helps to trim away kernel modules
#
# This tool doesn't perform any file operations - it just parses files and
# prints to stdout. Relies on depmod to have generates modules.dep and
# modules.alias files.
#
# 2014.08.21 darell tan
#

import os, sys
import getopt
import platform
import fnmatch

def get_loaded_modules():
	f = open('/proc/modules')
	modules = []
	for l in f:
		modules.append(l.split()[0])
	f.close()
	return modules

class KModuleName:
	"""Object to hold kernel module filename, used as dict key."""

	def __init__(self, kmodfile):
		self.filename = kmodfile
		self.name = self.get_kmod_name(kmodfile)

	def __hash__(self):
		return hash(self.name)

	def __eq__(self, other):
		return self.name == other if isinstance(other, str) else \
						  self.name == other.name

	def __str__(self):
		return 'm:'+ self.name

	@staticmethod
	def get_kmod_name(name):
		name = os.path.basename(name)
		return name[:-3] if name.endswith('.ko') else name

def get_dep_map(kerneldir):
	"""Reads the module dependencies map from modules.dep file.
	Note that the dependencies file uses filenames instead of module names."""

	f = open(os.path.join(kerneldir, 'modules.dep'))
	deps = {}
	for l in f:
		#print repr(l)
		mod, dep_list_str = l.strip().split(':', 1)
		assert mod not in deps

		kmod = KModuleName(mod)
		dep_list = [KModuleName(x) for x in dep_list_str.strip().split()]
		dep_list.insert(0, kmod)	# prepend ourself as a dependency

		deps[kmod] = dep_list

	f.close()
	return deps

def get_usb_modules(kerneldir):
	f = open(os.path.join(kerneldir, 'modules.alias'))
	usb_modules = {}
	for l in f:
		l = l.strip()
		if l.startswith('#'):
			continue
		_, alias, mod = l.split()

		if alias.startswith('usb:'):
			usb_modules[mod] = True

	f.close()
	return usb_modules.keys()

def get_kmodule(mod, dep_map):
	"""Tries to guess the kernel module filename given its module name,
	with the help of the dependency map. It's either a dash or underscore."""

	_mod = mod
	if mod in dep_map: return mod

	mod = mod.replace('_', '-')
	if mod in dep_map: return mod

	raise ValueError, 'unable to get module name "%s"' % _mod

def resolve_deps(modules, dep_map):
	"""Given a set of modules, resolve for its dependencies from the given
   	dependency map."""

	all_modules = []
	for mod in modules:
		module_deps = dep_map[ get_kmodule(mod, dep_map) ]

		for dep in module_deps:
			if dep not in all_modules:
				all_modules.append(dep)
	
	return all_modules


def main():
	include_usb_modules = False
	include_loaded_modules = False
	show_filenames = False
	invert_list = False
	kerneldir = ''

	# parse options
	opts, args = getopt.getopt(sys.argv[1:], 'liufk:')
	for o, a in opts:
		if o == '-i':
			invert_list = True
		elif o == '-l':
			include_loaded_modules = True
		elif o == '-u':
			include_usb_modules = True
		elif o == '-f':
			show_filenames = True
		elif o == '-k':
			kerneldir = a if '/' in a else \
				   os.path.join('/lib/modules', a)
		else:
			assert False, "unknown option " + o

	# use current kernel's module dir if not specified
	if not kerneldir:
		kerneldir = '/lib/modules/' + platform.release()

		# maybe we are on a bootstrap system?
		if not os.path.isdir(kerneldir):
			dirs = [x for x in os.listdir(kerneldir) if os.path.isdir(os.path.join(kerneldir, x))]
			if len(dirs) == 1:
				kerneldir = os.path.join(kerneldir, dirs[0])

	if not os.path.isfile(os.path.join(kerneldir, 'modules.dep')):
		'invalid kernel modules directory "%s"' % kerneldir

	# main code starts here
	dep_map = get_dep_map(kerneldir)
	modules = []

	# append user-specified modules
	for m in args:
		if '*' in m or '?' in m:
			modules.extend(fnmatch.filter((m.name for m in dep_map), m))
		else:
			modules.append(m)

	if include_loaded_modules:
		modules = get_loaded_modules()

	if include_usb_modules:
		modules += get_usb_modules(kerneldir)

	# resolve module dependencies
	all_modules = resolve_deps(modules, dep_map)

	if invert_list:
		all_modules = set(dep_map.keys()) - set(all_modules)

	for mod in all_modules:
		if show_filenames:
			print os.path.join(kerneldir, mod.filename)
		else:
			print mod.name


if __name__ == '__main__':
	main()

