"""Apply span edits to a part file in place: edit(y, x, 'chars') writes chars starting at x."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canvas import load_rows, save_rows

class Part:
    def __init__(self, name):
        self.path = os.path.join(HERE, 'parts', name + '.txt')
        self.g = [list(r) for r in load_rows(self.path)]
    def put(self, y, x, chars):
        for i, c in enumerate(chars):
            if c != '_':
                self.g[y][x + i] = c
    def get(self, y, x0, x1):
        return ''.join(self.g[y][x0:x1 + 1])
    def save(self):
        save_rows(self.path, self.g)
