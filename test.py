def merge(times):

    saved = list(times[0])
    print(saved)
    for st, en in sorted([sorted(t) for t in times]):
        print(st, en)
        if st <= saved[1]:
            saved[1] = max(saved[1], en)
        else:
            yield tuple(saved)
            saved[0] = st
            saved[1] = en
    yield tuple(saved)

data = [
    [(1, 5), (2, 4), (3, 6)],
    [(1, 3), (2, 4), (5, 8)],
    [(2, 3), (1, 4), (5, 8)]
    ]

for times in data:
    print(list(merge(times)))