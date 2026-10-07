"""Write guard for every god_elements script: any write-mode open, mkdir, remove, rename, copy target or
process launch whose path resolves under the live project raises. Aseprite may run (it only ever gets
scratch paths from these scripts; its args are checked too)."""
import os, sys
PROJECT = os.path.normcase(os.path.realpath(r'C:/Users/theyi/OneDrive/Documents/new-game-project'))
ASEPRITE = os.path.normcase(r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

def _under(p):
    try:
        r = os.path.normcase(os.path.realpath(os.fspath(p)))
    except TypeError:
        return False
    return r == PROJECT or r.startswith(PROJECT + os.sep)

def _hook(event, args):
    if event == 'open':
        path, mode = args[0], args[1]
        if isinstance(path, int) or mode is None:
            return
        if any(c in str(mode) for c in 'wax+') and _under(path):
            raise PermissionError('guard: write into the project refused: %s' % path)
    elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace', 'shutil.copyfile',
                   'shutil.copytree', 'shutil.move', 'shutil.rmtree', 'os.truncate', 'os.symlink', 'os.link'):
        for a in args:
            if isinstance(a, (str, bytes, os.PathLike)) and _under(a):
                if event in ('os.rename', 'os.replace', 'shutil.copyfile', 'shutil.move') and a is args[0]:
                    continue
                raise PermissionError('guard: %s into the project refused: %s' % (event, a))
    elif event == 'subprocess.Popen':
        exe, argv = args[0], args[1]
        if isinstance(argv, str):                   # Windows: one command line
            line = os.path.normcase(argv).lstrip()
            ok = line.startswith('"' + ASEPRITE + '"') or line.startswith(ASEPRITE + ' ')
            if not ok:
                raise PermissionError('guard: process refused: %s' % argv[:120])
            import shlex
            argv = shlex.split(argv, posix=False)
            argv = [a.strip('"') for a in argv]
        prog = os.path.normcase(str(exe or (argv[0] if argv else '')))
        if prog != ASEPRITE:
            raise PermissionError('guard: process refused: %s' % prog)
        for a in argv[1:]:
            s = str(a)
            if s.startswith('src=') or s.startswith('out='):
                s = s.split('=', 1)[1]
            if _under(s) and not s.endswith(('.png', '.aseprite')):
                raise PermissionError('guard: aseprite arg under project refused: %s' % s)

sys.addaudithook(_hook)
