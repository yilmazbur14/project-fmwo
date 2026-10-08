"""Safety net: refuse any write, move, delete or mkdir whose real path is inside the live project,
and any process launch other than Aseprite (whose path arguments must also stay out of the project).
Import this FIRST in every script of this job."""
import os
import sys

LIVE = os.path.normcase(os.path.realpath(r'C:\Users\theyi\OneDrive\Documents\new-game-project'))
ASE_RAW = r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe'
ASE = os.path.normcase(ASE_RAW)


ALLOWED = set()          # exact real paths an explicit --ship may write (see allow())


def allow(paths):
    """Let exactly these files be written inside the project (an explicit --ship only)."""
    for p in paths:
        ALLOWED.add(os.path.normcase(os.path.realpath(p)))


def _inside(p):
    try:
        rp = os.path.normcase(os.path.realpath(os.fspath(p)))
    except Exception:
        return False
    if rp in ALLOWED:
        return False
    return rp == LIVE or rp.startswith(LIVE + os.sep)


def _hook(event, args):
    if event == 'open':
        path, mode = args[0], args[1]
        if isinstance(path, int) or path is None:
            return
        m = mode if isinstance(mode, str) else ''
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        writing = any(c in m for c in 'wax+') or (flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and _inside(path):
            raise PermissionError('guard: write into the live project refused: %s' % path)
    elif event in ('os.remove', 'os.rename', 'os.replace', 'os.mkdir', 'os.rmdir', 'shutil.copyfile',
                   'shutil.copytree', 'shutil.move', 'shutil.rmtree', 'os.truncate'):
        paths = [a for a in args if isinstance(a, (str, bytes, os.PathLike))]
        # rename/replace: the destination is the second path
        if event in ('os.rename', 'os.replace', 'shutil.copyfile', 'shutil.copytree', 'shutil.move'):
            paths = paths[1:2] or paths
        for p in paths:
            if _inside(p):
                raise PermissionError('guard: %s into the live project refused: %s' % (event, p))
    elif event == 'subprocess.Popen':
        exe, argv = args[0], args[1]
        if isinstance(argv, (list, tuple)):
            first, rest = (str(argv[0]) if argv else str(exe)), [str(a) for a in argv[1:]]
        else:                                   # Windows: already one command line
            cmd = str(argv)
            q = '"%s"' % ASE_RAW
            if cmd.lower().startswith(q.lower()):
                first, rest = ASE_RAW, cmd[len(q):].split()
            elif cmd.lower().startswith(ASE_RAW.lower()):
                first, rest = ASE_RAW, cmd[len(ASE_RAW):].split()
            else:
                first, rest = cmd, []
        if os.path.normcase(first) != ASE:
            raise PermissionError('guard: process launch refused: %s' % (first,))
        live_l = LIVE.lower()
        for a in rest:
            a2 = a.strip('"')
            if _inside(a2) or live_l in os.path.normcase(a2).lower():
                raise PermissionError('guard: Aseprite pointed into the live project: %s' % a)
    elif event in ('os.system', 'os.startfile', 'os.exec', 'os.spawn', 'os.posix_spawn'):
        raise PermissionError('guard: %s refused' % event)


sys.addaudithook(_hook)
sys.dont_write_bytecode = True
