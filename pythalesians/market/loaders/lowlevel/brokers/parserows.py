__author__ = 'saeedamen'

import struct

from datetime import timedelta
# from collections import namedtuple

# Numba mixed results here
try:
    from numba import jit
except:
    pass

@jit
def parse_tick_data(data, epoch):
    # tick = namedtuple('Tick', 'Date ask bid askv bidv')

    chunks_list = chunks(data, 20)
    parsed_list = []
    date = []

    # note: Numba can speed up for loops
    for row in chunks_list:
        d = struct.unpack(">LLLff", row)
        date.append((epoch + timedelta(0,0,0, d[0])))

        # SLOW: no point using named tuples!
        # row_data = tick._asdict(tick._make(d))
        # row_data['Date'] = (epoch + timedelta(0,0,0,row_data['Date']))

        parsed_list.append(d)

    return date, parsed_list

def chunks(list, n):
    if n < 1: n = 1

    return [list[i:i + n] for i in range(0, len(list), n)]