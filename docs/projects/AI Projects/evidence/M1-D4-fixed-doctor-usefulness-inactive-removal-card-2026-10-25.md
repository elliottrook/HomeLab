# M1/D4 fixed Doctor usefulness inactive removal card — 2026-10-25

Status: **SOURCE READY; NOT AUTHORITY TO REMOVE**

The inactive installation has no predecessor and creates no user, service,
timer or runtime state. Its bounded rollback is therefore removal of only the
eight exact staged files and their then-empty directory.

`scripts/aster-adaptive/remove_fixed_doctor_usefulness_inactive.sh` pins every
installed filename and SHA-256 observed after the successful installation. It
will proceed only when LXC104 and Aster Agent are healthy, the whole-host lease
is ready, no usefulness runner exists, the directory has exact root-only
custody, all eight files match and no output, journal, bytecode cache or extra
object exists. It removes each named file separately and uses `rmdir` for the
directory; it contains no recursive deletion.

Any drift or evidence that the packet has been used causes a fail-closed exit
before removal. The source card neither removes the installed packet nor
authorizes a later removal. Removal would require a fresh decision because it
changes the live guest filesystem.
