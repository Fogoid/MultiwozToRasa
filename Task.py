class Task():
    def __init__(self, name, utterance):
        self.name = name
        self.slots = {}
        self.n_dialogues = 0
        self.utterances = [utterance]

    def addSlotCount(self, slots):
        self.n_dialogues += 1
        for slot in slots:
            if slot in self.slots.keys():
                self.slots[slot] += 1
            else:
                self.slots[slot] = 1
                
    def getSlotDefinitions(self):
        mandatory = []
        optional = []

        for slot in self.slots.keys():
            if self.slots[slot] / self.n_dialogues >= 0.90:
                mandatory += [slot,]
            else:
                optional += [slot,]

        return mandatory, optional

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)