"""Builds everything twice, each in its own Python process, and compares every output byte for byte.

    python determinism.py <scratch_dir>
"""
import os
import sys
import hashlib
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def digest_tree(root):
    out = {}
    for d, _, files in os.walk(root):
        if os.path.basename(d) == 'work':
            continue
        for f in files:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root)] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    return out


def main():
    base = sys.argv[1]
    runs = []
    for tag in ('run1', 'run2'):
        out = os.path.join(base, tag)
        r = subprocess.run([sys.executable, os.path.join(HERE, 'build.py'), out], capture_output=True, text=True)
        print(tag, 'exit', r.returncode, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-400:])
        runs.append(digest_tree(out))
    a, b = runs
    keys = sorted(set(a) | set(b))
    bad = [k for k in keys if a.get(k) != b.get(k)]
    for k in keys:
        print('%-8s %s  %s' % ('SAME' if a.get(k) == b.get(k) else 'DIFFER', (a.get(k) or '-')[:16], k))
    print('BYTE-IDENTICAL' if not bad else 'MISMATCH: %s' % bad)


if __name__ == '__main__':
    main()
