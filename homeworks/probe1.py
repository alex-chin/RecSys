class FilterSeq:

    def __init__(self, list_filter):
        self.list_filter = list_filter
        pass

    def prepare(self):
        pass

    def processing(self):
        a = 1
        for f in self.list_filter:
            a = f.trans(a)
        return a


class Filter:
    def __init__(self):
        pass

    def trans(self, a):
        pass


class Plus1(Filter):

    def trans(self, a):
        return a + 1


class Plus2(Filter):

    def trans(self, a):
        return a + 2


class Double(Filter):

    def trans(self, a):
        return 2 * 2


filter = FilterSeq([Plus1(), Plus2(), Double()])
filter.processing()
