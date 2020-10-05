class CycleIterator:
    def __init__(self, lst: list):
        self.list: list = lst
        self.list_len: int = len(self.list)
        self.position: int = 0
        self.element = None

    def __next__(self):
        self.element = self.get()
        self.next_position()
        return self.element

    def __iter__(self):
        return self

    def get(self):
        try:
            return self.list[self.position]
        except IndexError:
            raise StopIteration

    def next_position(self):
        if self.position != self.list_len - 1:
            self.position += 1
        else:
            self.position = 0

    def delete(self, element=None):
        if self.position != 0:
            position = self.position - 1
        else:
            position = self.list_len - 1
        if self.list[position] == element or element is None:
            self.list.pop(position)
            if position != self.list_len - 1:
                self.position -= 1
            self.list_len = len(self.list)
