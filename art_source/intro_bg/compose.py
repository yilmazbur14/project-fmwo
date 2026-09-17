from bg import build_background
import danny
import papers
from pngio import read_png, write_png, scale, crop


def compose():
    cv, _, _ = build_background()
    papers.draw_papers(cv)
    danny.to_canvas(cv, danny.build())
    return cv


if __name__ == '__main__':
    cv = compose()
    cv.save('stage3.png')
    w, h, rows = read_png('stage3.png')
    write_png('stage3_papers_8x.png', scale(crop(rows, 255, 175, 330, 262), 8))
    write_png('stage3_full_2x.png', scale(rows, 2))
