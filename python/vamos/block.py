# Copyright (C) 2014 Valentin Rothberg <valentinrothberg@gmail.com>

"""Utilities for conditional CPP blocks."""

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
import whatthepatch
import vamos.tools as tools


class Block(object):
    """Represents a conditional block."""
    def __init__(self, srcfile):
        object.__init__(self)
        self.srcfile = srcfile
        self.bid = ""
        self.range = (0, 0)
        self.defect = "no_defect"
        self.match = None
        self.ref_items = set()
        self.mus = ""  # path to the MUS report

    def update_range(self, pos, value):
        """Update the block's ranges with respect to the given position."""
        if pos <= self.range[0]:
            self.range = (self.range[0] + value, self.range[1])
        if pos <= self.range[1]:
            self.range = (self.range[0], self.range[1] + value)

    def __str__(self):
        """To string method of block."""
        return self.srcfile + ":" \
                + self.bid + ":" \
                + str(self.range[0]) + ":" \
                + str(self.range[1]) + ":" \
                + self.defect

    def is_defect(self):
        """Return true if the block is a defect."""
        return self.defect != "no_defect"

    @staticmethod
    def parse_blocks(path):
        """Parse C source file and return a dictionary of
        blocks {block id:  block}."""
        blocks = {}
        (output, _) = tools.execute("undertaker -j blockrange %s" % path,
                failok=False)
        for out in output:
            block = Block(path)
            split = out.split(":")
            block.bid = split[1]
            block.range = (int(split[2]), int(split[3]))
            if block.range[0] != 0:
                (precond, _) = tools.execute("undertaker -j blockpc %s:%i:1" %
                        (path, block.range[0]+1), failok=False)
                for pre in precond:
                    block.ref_items.update(tools.get_kconfig_items(pre))
            blocks[block.bid] = block
        return blocks

    @staticmethod
    def update_block_ranges(blocks, threshold, value):
        """Update ranges of each block in the @blocks list above threshold with
        @value and return them."""
        for block in blocks:
            block.update_range(threshold, value)
        return blocks

    @staticmethod
    def matchrange(block_a, block_b):
        """Return true if both blocks cover the same lines."""
        if block_a.range[0] == block_b.range[0] and \
                block_a.range[1] == block_b.range[1]:
            return True
        return False

    @staticmethod
    def parse_patchfile(patchfile, block_dict):
        """Parse the patchfile and update corresponding block ranges."""
        # https://pypi.python.org/pypi/whatthepatch/0.0.2
        diffs = []
        with open(patchfile) as stream:
            diffs = whatthepatch.parse_patch(stream.read())
        for diff in diffs:
            curr_file = diff.header.old_path
            # change format: [line before patch, line after patch, text]
            for change in diff.changes:
                # line removed
                if change[0] and not change[1]:
                    curr_line = int(change[0])
                    blocks = block_dict.get(curr_file, [])
                    blocks = Block.update_block_ranges(blocks, curr_line, -1)
                    block_dict[curr_file] = blocks
                # line added
                elif not change[0] and change[1]:
                    curr_line = int(change[1])
                    blocks = block_dict.get(curr_file, [])
                    blocks = Block.update_block_ranges(blocks, curr_line-1, 1)
                    block_dict[curr_file] = blocks
        return block_dict

    @staticmethod
    def get_block_id(report):
        """Return block ID of undertaker defect report."""
        match = re.match(r".+\.(B[0-9]+)\..+", report)
        if not match:
            raise ValueError("Could not get id of '%s'" % report)
        return match.groups()[0]

    @staticmethod
    def get_block_defect(report):
        """Return defect string of undertaker defect report."""
        match = re.match(r".+\.B[0-9]+\.(.+)", report)
        if not match:
            raise ValueError("Could not get defect of '%s'" % report)
        return match.groups()[0]

    @staticmethod
    def get_block_file(report):
        """Return the source file of undertaker defect report."""
        match = re.match(r"(.+)\.B[0-9]+\..+", report)
        if not match:
            raise ValueError("Could not get file of '%s'" % report)
        return match.groups()[0]

