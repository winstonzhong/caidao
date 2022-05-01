'''
Created on 2022年3月1日

@author: winston
'''
import sys


class CmdProgress(object):
    def __init__(self, maxval=None):
        self.maxval = maxval
        self.count = 0

    def update(self, step=1):
        self.count += step
#         pct = int((self.count * 1.0 / self.maxval) * 100.0)
        self.display()

    def display(self):
        pct = int((self.count * 1.0 / self.maxval) * 100.0)
        line_end = '\n' * (self.count >= self.maxval)
        sys.stdout.write("\r[%d/%d] %d%%" %
                         (self.count, self.maxval, pct) + line_end)
        sys.stdout.flush()

    def update_simple(self, step=1):
        self.count += step
        sys.stdout.write("\r%d" % self.count)
        sys.stdout.flush()


if __name__ == '__main__':
    pass
