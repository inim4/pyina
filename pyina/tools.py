#!/usr/bin/env python
#
# Author: Mike McKerns (mmckerns @caltech and @uqfoundation)
# Copyright (c) 1997-2015 California Institute of Technology.
# License: 3-clause BSD.  The full license text is available at:
#  - http://trac.mystic.cacr.caltech.edu/project/pathos/browser/pyina/LICENSE
"""
Various mpi python tools

Main function exported are::
    - ensure_mpi: make sure the script is called by mpi-enabled python
    - get_workload: get the workload the processor is responsible for

"""
def ensure_mpi(size = 1, doc = None):
    """
 ensure that mpi-enabled python is being called with the appropriate size

 inputs:
   - size: minimum required size of the MPI world [default = 1]
   - doc: error string to throw if size restriction is violated
    """
    if doc == None:
        doc = "Error: Requires MPI-enabled python with size >= %s" % size
    from pyina.mpi import world
    mpisize = world.Get_size()
    mpirank = world.Get_rank()
    if mpisize < size:
        if mpirank == 0: print doc
        import sys
        sys.exit()
    return

def mpiprint(string="", end="\n", rank=0, comm=None):
    """print the given string to the given rank"""
    from pyina.mpi import world
    if comm is None: comm = world
    if not hasattr(rank, '__len__'): rank = (rank,)
    if comm.rank in rank:
        print string+end,


#XXX: has light load on *last* proc, heavy/equal on first proc
from math import ceil
def get_workload(index, nproc, popsize, skip=None):
    """returns the workload that this processor is responsible for

index: int rank of node to calculate for
nproc: int number of nodes
popsize: int number of jobs
skip: int rank of node upon which to not calculate (i.e. the master)

returns (begin, end) index
    """
    if skip is not None and skip < nproc:
        nproc = nproc - 1
        if index == skip: skip = True
        elif index > skip: index = index - 1
    n1 = nproc
    n2 = popsize
    iend = 0
    for i in range(nproc):
        ibegin = iend
        ai = int( ceil( 1.0*n2/n1 ))
        n2 = n2 - ai
        n1 = n1 - 1
        iend = iend + ai
        if i==index:
           break
    if skip is True:
        return (ibegin, ibegin) if (index < nproc) else (iend, iend)
    return (ibegin, iend) #XXX: (begin, end) index for a single element


#FIXME: has light load on *last* proc, heavy/equal on master proc
import numpy as np
def balance_workload(nproc, popsize, *index, **kwds):
    """divide popsize elements on 'nproc' chunks

nproc: int number of nodes
popsize: int number of jobs
index: int rank of node(s) to calculate for (using slice notation)
skip: int rank of node upon which to not calculate (i.e. the master)

returns (begin, end) index vectors"""
    _skip = False
    skip = kwds.get('skip', None)
    if skip is not None and skip < nproc:
        nproc = nproc - 1
        _skip = True
    count = np.round(popsize/nproc)
    counts = count * np.ones(nproc, dtype=np.int)
    diff = popsize - count*nproc
    counts[:diff] += 1
    begin = np.concatenate(([0], np.cumsum(counts)[:-1]))
   #return counts, index #XXX: (#jobs, begin index) for all elements
    if _skip:
        if skip == nproc: # remember: nproc has been reduced
            begin = np.append(begin, begin[-1]+counts[-1])
            counts = np.append(counts, 0)
        else:
            begin = np.insert(begin, skip, begin[skip])
            counts = np.insert(counts, skip, 0)
    if not index:
        return begin, begin+counts #XXX: (begin, end) index for all elements
   #if len(index) > 1:
   #    return lookup((begin, begin+counts), *index) # index a slice
    return lookup((begin, begin+counts), *index) # index a single element

def lookup(inputs, *index):
    """get tuple of inputs corresponding to the given index"""
    if len(index) == 1: index = index[0]
    else: index = slice(*index)
    return tuple(i.__getitem__(index) for i in inputs)

def isoseconds(time):
    """calculate number of seconds from a given isoformat timestring"""
    if isinstance(time, int): return time #XXX: allow this?
    import datetime
    d = 0
    try: # allows seconds up to 59 #XXX: allow 60+ ?
        t = datetime.datetime.strptime(time, "%S").time()
    except ValueError:
        fmt = str(time).count(":") or 2 # get ValueError if no ":"
        if fmt == 1:
            t = datetime.datetime.strptime(time, "%H:%M").time()
        elif fmt == 3: # allows days (up to 31)
            t = datetime.datetime.strptime(time, "%d:%H:%M:%S")
            d,t = t.day, t.time()
        else: # maxtime is '23:59:59' #XXX: allow 24+ hours instead of days?
            t = datetime.datetime.strptime(time, "%H:%M:%S").time()
    return t.second + 60*t.minute + 3600*t.hour + d*86400

def isoformat(seconds):
    """generate an isoformat timestring for the given time in seconds"""
    import datetime
    d = seconds/86400
    if d > 31: datetime.date(1900, 1, d) # throw ValueError
    h = (seconds - d*86400)/3600
    m = (seconds - d*86400 - h*3600)/60
    s = seconds - d*86400 - h*3600 - m*60
    t = datetime.time(h,m,s).strftime("%H:%M:%S")
    return ("%s:" % d) + t if d else t #XXX: better convert days to hours?

# backward compatability
from pox import which_python, wait_for


if __name__=='__main__':
    n = 7 #12
    pop = 12 #7 
    #XXX: note the two ways to calculate
    assert get_workload(0, n, pop) == balance_workload(n, pop, 0)
    assert [get_workload(i, n, pop) for i in range(n)] == \
                                         zip(*balance_workload(n, pop))
    assert [get_workload(i, n, pop) for i in range(0,n/2)] == \
                                         zip(*balance_workload(n, pop, 0, n/2))

    assert zip(*balance_workload(n,pop,0,n)) == zip(*balance_workload(n,pop))
    assert zip(*balance_workload(n,pop,0,1)) == [balance_workload(n,pop,0)]

    assert get_workload(0,n,pop,skip=0) == balance_workload(n,pop,0,skip=0)
    assert get_workload(0,n,pop,skip=n) == balance_workload(n,pop,0,skip=n)
    assert get_workload(0,n,pop,skip=n+1) == balance_workload(n,pop,0,skip=n+1)

    assert [get_workload(i, n, pop, skip=0) for i in range(n)] == \
                                         zip(*balance_workload(n, pop, skip=0))
    assert [get_workload(i, n, pop, skip=n) for i in range(n)] == \
                                         zip(*balance_workload(n, pop, skip=n))


# End of file
