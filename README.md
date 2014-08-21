Mininmal CentOS Kickstart Config
=================================
Serve this `ks.cfg` to CentOS/RHEL over HTTP for a minimal installation.
Modify `ks.cfg` to add additional packages to be installed, as well as 
post-processing to be done.

See http://fedoraproject.org/wiki/Anaconda/Kickstart for details.

modtrim
--------
`modtrim.py` is used to strip unnecessary kernel modules from a system.
It can be used as a standalone tool to query and remove kernel modules.

