class Task():
    def __init__(self, name):
        self.slots = {}
        self.n_dialogues = 0
        self.mandatory = []

    def addSlotCount(self, slots):
        self.n_dialogues += 1
        for slot in slots:
            if slot in self.slots.keys():
                self.slots[slot] += 1
            else:
                self.slots[slot] = 1
                
    def computeSlots(self):
        self.mandatory = list(filter(lambda x: self.slots[x] / self.n_dialogues >= 0.75, self.slots))

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)