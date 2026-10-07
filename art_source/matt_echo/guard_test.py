import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard
tests = []
def t(name, fn):
    try:
        fn(); tests.append((name, 'ALLOWED'))
    except PermissionError as e:
        tests.append((name, 'refused'))
live = r'C:\Users\theyi\OneDrive\Documents\new-game-project\Assets\Characters\Matt\__guard_probe.png'
short = r'C:\Users\theyi\OneDrive\DOCUME~1\NEW-GA~1\Assets\__probe.txt'
t('open w live', lambda: open(live, 'wb'))
t('open w 8.3', lambda: open(short, 'w'))
t('replace live', lambda: os.replace(__file__ + '.nope', live))
t('mkdir live', lambda: os.mkdir(r'C:\Users\theyi\OneDrive\Documents\new-game-project\zz_probe'))
import subprocess
t('popen python', lambda: subprocess.run(['python', '-c', 'print(1)']))
t('read live', lambda: open(r'C:\Users\theyi\OneDrive\Documents\new-game-project\Assets\Characters\Matt\matt.png','rb').close())
scratch = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_probe.txt')
t('open w scratch', lambda: open(scratch, 'w').close())
os.remove(scratch)
for n, r in tests: print('%-16s %s' % (n, r))
print('probe exists?', os.path.exists(live))
ASE = r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe'
t('aseprite --version', lambda: subprocess.run([ASE, '--version'], capture_output=True, check=True))
t('aseprite into live', lambda: subprocess.run([ASE, '-b', 'x.png', '--save-as', r'C:\Users\theyi\OneDrive\Documents\new-game-project\Assets\zz.aseprite'], capture_output=True))
for n, r in tests[-2:]: print('%-20s %s' % (n, r))
