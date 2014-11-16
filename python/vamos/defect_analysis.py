# Copyright (C) 2014 Valentin Rothberg <valentinrothberg@gmail.com>

"""Utilities to detect and analyze defects in a given source file."""

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


import re
import os
import tempfile
import vamos.tools as tools
from vamos.block import Block


def defect_analysis(srcfile, models, flag=""):
    """Defect analysis using the Undertaker tool.
    Returns list of defect reports."""
    reports = []
    defect_pattern = re.compile(r"[\S]+\.[cSh]\.B[0-9]+[\S]+")
    (output, _) = tools.execute("undertaker -v -m %s %s %s" %
            (models, srcfile, flag), failok=True)
    for report in output:
        if not report.startswith("I:"):
            continue
        matches = defect_pattern.findall(report)
        if matches:
            defect = matches[0].strip()
            if not defect.endswith(".mus"):
                # we just need to know if there is a defect, but do not need
                # the defect report
                os.remove(defect)
            # no_kconfig defects cannot be correlated to problems
            # with Kconfig itself (e.g., #ifdef DEBUG), so we ignore them
            if "globally" in defect and not "no_kconfig" in defect:
                reports.append(defect)
    return reports


def batch_analysis(srclist, models, flags=""):
    """Batch defect analysis of files in @srclist. Assign defects to the blocks
    of the files and return a dictionary {file: [blocks]}."""
    # make a temporary batchfile
    batchfile = tempfile.mkstemp()[1]
    with open(batchfile, "w") as stream:
        for srcfile in srclist:
            stream.write("%s\n" % srcfile)

    # parse blocks for each source files
    blocks = {}
    for srcfile in srclist:
        blocks[srcfile] = Block.parse_blocks(srcfile)

    # defect analysis and assignment of defects to each source file
    flags += " -b %s" % batchfile
    for report in defect_analysis("", models, flags):
        # get block id, source file and defect class from report
        bid = Block.get_block_id(report)
        bfile = Block.get_block_file(report)
        bdefect = Block.get_block_defect(report)
        # assign information to the blocks of the source file
        srcblocks = blocks[bfile]
        srcblocks[bid].defect = bdefect
        if report.endswith(".mus"):
            srcblocks[bid].mus = report

    for srcfile in blocks:
        blocks[srcfile] = list(blocks[srcfile].values())  # dict to list

    os.remove(batchfile)
    return blocks


def compare_and_report(blocks_a, blocks_b):
    """Compare both block lists and report if a defect is introduced, fixed,
    changed or unchanged. Return a list of all unique defects."""
    defects = []

    for block_a in blocks_a:
        for block_b in blocks_b:
            if Block.matchrange(block_a, block_b):
                block_a.match = block_b
                block_b.match = block_a

    for block_b in [b for b in blocks_b if not b.match and b.is_defect()]:
        print "New defect: %s" % block_b
        defects.append(block_b)

    for block_a in blocks_a:
        block_b = block_a.match

        if not block_b:
            if block_a.is_defect():
                print "Defect repaired (removed): %s" % block_a
            continue
        if block_a.defect == block_b.defect:
            if block_a.is_defect():
                print "Unchanged defect: %s" % block_b
                defects.append(block_b)
        else:
            if block_a.is_defect() and not block_b.is_defect():
                print "Defect repaired: %s" % block_a
            elif not block_a.is_defect() and block_b.is_defect():
                print "New defect: %s" % block_b
                defects.append(block_b)
            else:
                print "Changed defect: from %s to %s " % (block_a, block_b)
                defects.append(block_b)

    return defects


def check_missing_defect(block, model):
    """Check the missing defect."""
    # missing item is referenced in macro?
    in_macro = False
    in_dependencies = False
    missings = []
    for item in block.ref_items:
        if not model.is_defined(item):
            in_macro = True
            missings.append(item)
            print "%s: %s referenced but not defined" % (block, item)
    if in_macro:
        return missings
    # missing item is in dependencies of the block?
    for item in block.ref_items:
        (interesting, _) = tools.execute("undertaker -j interesting %s -m %s" %
                (item, model.path))
        interesting = tools.get_kconfig_items(interesting[0])
        for intr in interesting:
            if not model.is_defined(intr):
                in_dependencies = True
                missings.append(item)
                print "%s: %s is in dependencies but not defined" % \
                        (block, intr)
    if not in_dependencies:
        print "%s: could not detect cause of defect" % block
    return missings


def check_kconfig_defect(block, model):
    """Check the kconfig defect. Return true if cause is identified."""
    identified = False
    for item in block.ref_items:
        if item in model.always_on_items:
            print "%s: referenced item %s is always on" % (block, item)
            identified = True
        elif item in model.always_off_items:
            print "%s: referenced item %s is always off" % (block, item)
            identified = True
            continue
        (interesting, _) = tools.execute("undertaker -j interesting %s -m %s" %
                (item, model.path))
        interesting = tools.get_kconfig_items(interesting[0])
        for intr in interesting:
            if item in model.always_on_items:
                print "%s: %s is in dependencies and always on" % \
                        (block, intr)
                identified = True
            elif item in model.always_off_items:
                print "%s: %s is in dependencies and always off" % \
                        (block, intr)
                identified = True
    return identified


def check_code_defect(block):
    """ Check the code defect."""
    defines = []
    undefines = []
    is_define = False
    # defines
    (output, _) = tools.execute(r"grep '^\s*#def' %s" % block.srcfile)
    for out in output:
        defines.extend(tools.get_kconfig_items(out))
    # undefines
    (output, _) = tools.execute(r"grep '^\s*#undef' %s" % block.srcfile)
    for out in output:
        undefines.extend(tools.get_kconfig_items(out))

    for ref in block.ref_items:
        if ref in defines:
            print "%s: referencing previously defined item %s" % (block, ref)
            is_define = True
        elif ref in undefines:
            print "%s: referencing previously undefined item %s" % (block, ref)
            is_define = True
    if is_define:
        return

    # display the block's precondition
    reason = "contradiction"
    if "undead" in block.defect:
        reason = "tautology"
    print "%s: there is a %s in the block's precondition" % (block, reason)
    block_loc = block.srcfile + ":" + str(block.range[0]+1) + ":1"
    (output, _) = tools.execute("undertaker -j blockpc %s" % block_loc,
            failok=False)
    for out in output:
        print out
