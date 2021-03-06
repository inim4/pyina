#!/usr/bin/env python
#
# Author: Mike McKerns (mmckerns @caltech and @uqfoundation)
# Copyright (c) 1997-2015 California Institute of Technology.
# License: 3-clause BSD.  The full license text is available at:
#  - http://trac.mystic.cacr.caltech.edu/project/pathos/browser/pyina/LICENSE
"""
# Testing pyina.mpi.world.bcast
# To run:

python mpipyre2.py
""" 


from mpi.Application import Application
import logging

class SimpleApp(Application):

    def main(self):
        from pyina import mpi

        world = mpi.world
        logging.info("I am rank %d of %d" % (world.rank, world.size))
	root = 0
        if world.rank == root:
            str = "hello world"
            nn = world.bcast(str, root)
            print "Master has: %s " % nn
        else:
            nn = world.bcast("", root)
            print "Slave (%d) has: %s " % (world.rank, nn)
        return

    def _defaults(self):
        self.inventory.launcher.inventory.nodes = 4

    def __init__(self):
        Application.__init__(self, "simple")
        return


# main

if __name__ == "__main__":
    import journal
    #journal.info("mpirun").activate()
    #journal.debug("pyina.mpi.world.bcast").activate()

    app = SimpleApp()
    app.run()

# End of file
