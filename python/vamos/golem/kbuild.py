#
#   golem - analyzes feature dependencies in Linux makefiles
#
# Copyright (C) 2011 Christian Dietrich <christian.dietrich@informatik.uni-erlangen.de>
# Copyright (C) 2011 Reinhard Tartler <tartler@informatik.uni-erlangen.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from vamos.tools import execute, CommandFailed

import logging
import os
import re
import sys

import vamos

class TreeNotConfigured(RuntimeError):
    """ Indicates that this Linux tree is not configured yet """
    pass


class NotALinuxTree(RuntimeError):
    """ Indicates we are not in a Linux tree """
    pass


def apply_configuration(arch=None, subarch=None, filename=None):
    """
    Applies the current configuration

    Expects a complete configuration in '.config'. Updates
    'include/config/auto.conf' and 'include/generated/autoconf.h' to
    match the current configuration.

    If not applying for the default architecture 'x86', the optional
    parameters "arch" (and possibly "subarch") need to be specified.

    If an optional filename is passed, then architecture and subarch are
    guessed using the guess_arch_from_filename() function. Overriding
    either arch or subarch remains possible by explicitly setting arch
    or subarch.
    """

    if filename:
        (guessed_arch, guessed_subarch) = guess_arch_from_filename(filename)
        if not arch:
            arch = guessed_arch
        if not subarch:
            subarch = guessed_subarch

    try:
        call_linux_makefile('silentoldconfig', arch=arch, subarch=subarch)
    except CommandFailed as e:
        if e.returncode == 2:
            raise TreeNotConfigured("target 'silentoldconfig' failed")
        else:
            raise


def files_for_current_configuration(arch=None, subarch=None, how=False):
    """
    to be run in a Linux source tree.

    Returns a list of files that are compiled with the current
    configuration. If the optional parameter 'how' is added, the
    returned list additionally indicates in what way (i.e., module or
    statically compiled) the file is included.

    If not working for the default architecture 'x86', the optional
    parameters "arch" (and possibly "subarch") need to be specified!
    """

    # locate directory for supplemental makefiles
    scriptsdir = find_scripts_basedir()
    assert os.path.exists(os.path.join(scriptsdir, 'Makefile.list_recursion'))

    apply_configuration(arch=arch, subarch=subarch)

    make_args="-f %(basedir)s/Makefile.list UNDERTAKER_SCRIPTS=%(basedir)s" % \
        { 'basedir' : scriptsdir }

    (output, _) = call_linux_makefile('list',
                                      arch=arch,
                                      subarch=subarch,
                                      failok=False,
                                      extra_variables=make_args)

    files = set()
    for line in output:
        if len(line) == 0:
            continue
        try:
            if (how):
                objfile = line
            else:
                objfile = line.split()[0]
            # try to guess the source filename
            sourcefile = objfile[:-2] + '.c'
            if os.path.exists(sourcefile):
                files.add(sourcefile)
            else:
                logging.warning("Failed to guess source file for %s", objfile)
        except IndexError:
            raise RuntimeError("Failed to parse line '%s'" % line)

    return files


def file_in_current_configuration(filename):
    """
    to be run in a Linux source tree.

    Returns the mode (as a string) the file is compiled in the current
    configuration:

        "y" - statically compiled
        "m" - compiled as module
        "n" - not compiled into the kernel

    """

    # locate directory for supplemental makefiles
    scriptsdir = find_scripts_basedir()
    assert(os.path.exists(os.path.join(scriptsdir, 'Makefile.list_recursion')))

    # normalize filename
    filename = os.path.normpath(filename)

    basename = filename.rsplit(".", 1)[0]
    logging.debug("checking file %s", basename)

    apply_configuration(filename=filename)

    make_args = "-f %(basedir)s/Makefile.list UNDERTAKER_SCRIPTS=%(basedir)s compiled='%(filename)s'" % \
        { 'basedir' : scriptsdir,
          'filename': filename.replace("'", "\'")}

    (make_result, _) = call_linux_makefile('list',
                                           filename=filename,
                                           failok=False,
                                           extra_variables=make_args)

    for line in make_result:
        if line.startswith(basename):
            return line.split(" ")[1]

    return "n"


def determine_buildsystem_variables(arch=None):
    """
    returns a list of kconfig variables that are mentioned in Linux Makefiles
    """
    if arch:
        cmd = r"find . \( -name Kbuild -o -name Makefile \) " + \
              r"\( ! -path './arch/*' -o -path './arch/%(arch)s/*' \) " + \
              r"-exec sed -n '/-\$(CONFIG_/p' {} \+"
        cmd = cmd % {'arch': arch}

    else:
        cmd = r"find . \( -name Kbuild -o -name Makefile \) -exec sed -n '/-\$(CONFIG_/p' {} \+"
    find_result = execute(cmd, failok=False)

    ret = set()
    # line might look like this:
    # obj-$(CONFIG_MODULES)           += microblaze_ksyms.o module.o
    for line in find_result[0]:
        m = re.search(r'-\$\(CONFIG_(\w+)\)', line)
        if not m: continue
        config_variable = m.group(1)
        if (config_variable):
            ret.add(config_variable)

    return ret


def guess_arch_from_filename(filename):
    """
    Guesses the 'best' architecture for the given filename.

    If the file is in the Linux HAL (e.g., 'arch/arm/init.c', then the
    architecture is deduced from the filename

    Defaults to 'vamos.default_architecture' (default: 'x86')

    returns a tuple (arch, subarch) with the architecture identifier (as
    in the subdirectory part) and the preferred "subarchitecture". The
    latter is used e.g. to disable CONFIG_64BIT on 'make allnoconfig'
    when compiling on a 64bit host (default behavior), unless
    vamos.prefer_32bit is set to False.
    """

    m = re.search("^arch/([^/]*)/", os.path.normpath(filename))
    if m:
        arch = m.group(1)
    else:
        arch = vamos.default_architecture

    subarch = arch
    if arch == 'x86' or arch == 'um':
        if vamos.prefer_32bit:
            subarch = 'i386'
        else:
            subarch = 'x86_64'
    else:
        assert(arch==subarch)

    return (arch, subarch)


def call_linux_makefile(target, extra_env="", extra_variables="",
                        filename=None, arch=None, subarch=None,
                        failok=True, dryrun=False):
    """
    Invokes 'make' in a Linux Buildtree.

    This utility function hides details how to set make and environment
    variables that influence kbuild. An important variable is 'ARCH'
    (and possibly later 'SUBARCH'), which can be via the corresponding
    variables.

    If a target points to an existing file (or the optional target
    filename is given)the environment variable for ARCH is derived
    according to the follwing rules:

      - if the file is inside an "arch/$ARCHNAME/", use $ARCHNAME
      - if the "arch" variable is set, use that
      - by default use 'default_arch'
      - if the arch is set to 'x86', set ARCH to 'i386', unless the
        "prefer_64bit" parameter is set to 'True'

    If dryrun is True, then the command line is returned instead of the
    command's execution output. This is mainly useful for testing.

    returns a tuple with
     1. the command's standard output as list of lines
     2. the exitcode
    """

    cmd = "make"
    if extra_env and "ARCH=" in extra_env or extra_variables and "ARCH=" in extra_variables:
        logging.debug("Detected manual (SUB)ARCH override in extra arguments '(%s, %s)'",
                      extra_env, extra_variables)
    else:
        if os.path.exists(target):
            filename = target
        if filename:
            (guessed_arch, guessed_subarch) = guess_arch_from_filename(filename)

            if not arch:
                arch = guessed_arch

            if not subarch:
                subarch = guessed_subarch

    if not arch:
        (arch, subarch) = guess_arch_from_filename('Makefile')

    if not subarch:
        subarch = arch

    extra_env += " ARCH=%s" % arch
    extra_env += " SUBARCH=%s" % subarch

    if not 'KERNELVERSION=' in extra_variables:
        if not vamos.kernelversion:
            (output, rc) = execute("git describe", failok=True)
            if rc == 0:
                vamos.kernelversion = output[-1]
        if vamos.kernelversion:
            extra_env += ' KERNELVERSION="%s"' % vamos.kernelversion

    cmd = "env %(extra_env)s make %(target)s %(extra_variables)s " % \
        { 'extra_env': extra_env,
          'target': target,
          'extra_variables': extra_variables }

    # simulate interactive (re-)configuring by pressing a lot of enter
    if 'oldconfig' in target:
        cmd = 'yes '' | ' + cmd

    if dryrun:
        return (cmd, 0)
    else:
        return execute(cmd, failok=failok)


def get_linux_version():
    """
    Checks that the current working directory is actually a Linux Tree

    Uses a custom Makefile to retrieve the current kernel version. If we
    are in a git tree, additionally compare the git version with the
    version stated in the Makefile for plausibility.

    Raises a 'NotALinuxTree' exception if the version could not be retrieved.
    """

    scriptsdir = find_scripts_basedir()

    if not os.path.exists('Makefile'):
        raise NotALinuxTree("No 'Makefile' found")

    extra_vars = "-f %(basedir)s/Makefile.version UNDERTAKER_SCRIPTS=%(basedir)s" % \
        { 'basedir' : scriptsdir }

    (output, ret) = call_linux_makefile('', extra_variables=extra_vars)
    if ret > 0:
        raise NotALinuxTree("Makefile does not indicate a Linux version")

    version = output[-1] # use last line, if not configured we get additional warning messages
    if os.path.isdir('.git'):
        cmd = "git describe"
        (output, ret) = execute(cmd)
        git_version = output[0]
        if (ret > 0):
            return 'v' + version

        if (not git_version.startswith('v')):
            raise NotALinuxTree("Git does not indicate a Linux version ('%s')" % \
                                    git_version)

        if git_version[1:].startswith(version[0:3]):
            return git_version
        else:
            raise NotALinuxTree("Git version does not look like a Linux version ('%s' vs '%s')" % \
                                    (git_version, version))
    else:
        return 'v' + version


def find_scripts_basedir():
    executable = os.path.realpath(sys.argv[0])
    base_dir   = os.path.dirname(executable)
    for d in [ '../lib', '../scripts']:
        f = os.path.join(base_dir, d, 'Makefile.list')
        if os.path.exists(f):
            return os.path.realpath(os.path.join(base_dir, d))
    raise RuntimeError("Failed to locate Makefile.list")
