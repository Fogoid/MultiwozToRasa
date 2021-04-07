import json
import re
from Task import Task

current_intent = "NONE"
last_frame = {}
intents = {}
slots = {}
frame_slots = {}

last_turn = None

# Carregar diálogos dos ficheiros do multiwoz
json_file = []
with open("resourses\\multiwoz\\dev\\dialogues_001.json") as f:
    json_file += json.load(f)

with open("resourses\\multiwoz\\dev\\dialogues_002.json") as f:
    json_file += json.load(f)

# Percorrer cada diálogo
for item in json_file:
    for turn in item["turns"]:
        # Só se preocupa com as falas do utilizador
        if turn["speaker"] == "SYSTEM":
            continue
        
        frame = list(filter(lambda x: x["state"]["active_intent"] != "NONE", turn["frames"]))
        if frame != []:
            frame = frame[0]
            
            # Identifica as identidades nos exemplos
            # Verificar inform. Isto porque existem valores que são iguais mas para valores de slots diferentes
            utterance = turn["utterance"]
            for slot in frame["state"]["slot_values"].keys():
                if slot not in frame_slots:
                    slot_values = frame["state"]["slot_values"][slot]
                    for val in slot_values:
                        pattern = re.compile(val, flags=re.IGNORECASE)
                        result = pattern.search(utterance)
                        if result != None:
                            replaceable = "[{}]({})".format(val, slot)
                            utterance = pattern.sub(replaceable, utterance)
                            break
                        
            if current_intent != frame["state"]["active_intent"]: # Nova intent, ou seja existe uma frase relevante do lado do USER
                
                if current_intent in intents.keys():
                    intents[current_intent].addSlotCount(list(frame_slots.keys())) # O frame_slots vai ter o valor do ultimo frame a ser visto
                
                current_intent = frame["state"]["active_intent"]
                
                if current_intent in intents.keys():
                    intents[current_intent].utterances += [utterance,]
                else:
                    intents[current_intent] = Task(current_intent, utterance)
                
            else: # Considerar como inform
                
                if "inform" in intents.keys():
                    intents["inform"].utterances += [utterance,]
                else:
                    intents["inform"] = Task(current_intent, utterance)

            
            # Adicionar todas as intents que questionam algum parâmetro
            # Esta implementação pode ter alguma ambiguidade em como resolver as intents
            if frame["state"]["requested_slots"] != []:
                intent_name = "request"
                for rs in frame["state"]["requested_slots"]:
                    intent_name += "_" + rs
                
                if intent_name in intents.keys():
                    intents[intent_name].utterances += [utterance,]
                else:
                    intents[intent_name] = Task(intent_name, utterance)
                
            # Obter os slots
            frame_slots = frame["state"]["slot_values"]
            for slot in frame_slots:
                slots[slot] = frame_slots[slot] if slot not in slots.keys() else slots[slot] + frame_slots[slot]

        else:
            pass # Fazer algo quando a intent é NONE
        
        last_turn = turn

# Escrever o domain
# Os slots estão a ser considerados como entidades
with open("Model\\domain.yml", "w") as f:
    domain = "intents:\n"
    for intent in intents.keys():
        domain += "  - {}\n".format(intent)
    
    entities = "\nentities:\n"
    slot_string = "\nslots:\n"

    for slot in slots:
        entities += "  - {}\n".format(slot)
        slot_string += "  {}:\n    type: unfeaturized\n".format(slot) 
    
    f.write(domain + entities + slot_string)

# Escrever a nlu
with open("Model\\data\\nlu.yml", "w") as f:
    nlu = "nlu:\n"
    for intent in intents.keys():
        nlu += '- intent: {}\n  examples: |\n'.format(intent)
        for example in intents[intent].utterances:
            nlu += '    - {}\n'.format(example)
        nlu += "\n"

    f.write(nlu)