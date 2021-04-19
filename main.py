import json
import re
from Task import Task


####################################################
#                AUXILIARY FUNCTIONS               #
####################################################

def AddIntent(name):
    if name not in intents:
        intents[name] = Task(name)

def AddSynonim(key, synonim):
    if key not in synonims:
        synonims[key] = [synonim,]
    else:
        if synonim not in synonims[key]:
            synonims[key] += [synonim,]

def findSlotUsingSpaces(slot, utter):
    modified_slot = slot
    index = 0
    while index != len(slot):
        pattern = re.compile(modified_slot, flags=re.IGNORECASE)
        result = pattern.search(utter)
        if result != None:
            replaceable = "[{}]({})".format(modified_slot, "required_info")
            return pattern.sub(replaceable, utter)
        else:
            modified_slot = slot[:index] + " " + slot[index:]
            index += 1
    return utter

def findRequestedSlotsInUtterance(slots, utter):
    for s in slots:
        s = s.split("-")[1]
        utter = findSlotUsingSpaces(s, utter)
    return utter
            
####################################################
#                CONTROL VARIABLES                 #
####################################################

# variaveis necessárias para o dominio
intents = {}
slots = {}
actions = []
responses = []
training_data = {}
synonims = {}

# variáveis de controlo
current_intent = "NONE"
last_frame = {}
frame_slots = {}
last_turn = None

####################################################
#                   DIALOGUES LOAD                 #
####################################################

# Carregar diálogos dos ficheiros do multiwoz
json_file = []
with open("resourses\\multiwoz\\dev\\dialogues_001.json") as f:
    json_file += json.load(f)

with open("resourses\\multiwoz\\dev\\dialogues_002.json") as f:
    json_file += json.load(f)

####################################################
#      INTENTS, ENTITIES AND SLOTS DEFINITION      #
####################################################

# Percorrer cada diálogo para obter os slots obrigatórios
for item in json_file:
    current_intent = ""

    for turn in item["turns"]:
        # Só se preocupa com as falas do utilizador
        if turn["speaker"] == "SYSTEM":
            continue

        turn["chosen_intents"] = []
        
        frame = list(filter(lambda x: x["state"]["active_intent"] != "NONE", turn["frames"]))
        if frame != []:
            frame = frame[0]
            
            # Identifica as entidades nos exemplos
            # Verificar inform. Isto porque existem valores que são iguais mas para valores de slots diferentes
            utterance = turn["utterance"]
            for slot in frame["state"]["slot_values"].keys():
                if slot not in frame_slots.keys() or (
                    frame["state"]["slot_values"][slot][0] != frame_slots[slot][0] 
                ):
                    slot_values = frame["state"]["slot_values"][slot]
                    for val in slot_values:
                        pattern = re.compile(val, flags=re.IGNORECASE)
                        result = pattern.search(utterance)
                        if result != None:
                            # Porção dos sinónimos #
                            # replaceable = ""
                            # new_val = utterance[result.start(0):].split(" ")[0]
                            # if len(val) == len(new_val) or len(val) > len(new_val):
                            #     replaceable = "[{}]({})".format(val, slot)
                            # else:
                            #     AddSynonim(val, new_val)
                            
                            replaceable = "[{}]({})".format(val, slot)
                            utterance = pattern.sub(replaceable, utterance)
                            break
                        
            if current_intent != frame["state"]["active_intent"]: # Nova intent, ou seja existe uma frase relevante do lado do USER
                
                if current_intent in intents.keys():
                    intents[current_intent].addSlotCount(list(frame_slots.keys())) # O frame_slots vai ter o valor do ultimo frame a ser visto
                
                current_intent = frame["state"]["active_intent"]
                AddIntent(current_intent)
                turn["chosen_intents"] += [current_intent,]
                 

            else: # Considerar como inform
                if list(filter(lambda x: x not in frame_slots.keys() or (
                    frame["state"]["slot_values"][x][0] != frame_slots[x][0] 
                ), frame["state"]["slot_values"].keys())) != []:
                    AddIntent("inform")
                    turn["chosen_intents"] += ["inform",]

            # Adiciona como request caso exista informação questionada ao slots
            if frame["state"]["requested_slots"] != []:
                utterance = findRequestedSlotsInUtterance(frame["state"]["requested_slots"], utterance)
                AddIntent("request")
                turn["chosen_intents"] += ["request",]

            # Obter os slots
            frame_slots = frame["state"]["slot_values"]
            for slot in frame_slots:
                slots[slot] = frame_slots[slot] if slot not in slots.keys() else slots[slot] + frame_slots[slot]

            # Adiciona a classificação de multiplas intents
            if turn["chosen_intents"] != []:
                chosen_intents = turn["chosen_intents"]
                key = chosen_intents[0]
                for i in range(1, len(chosen_intents)):
                    key += "+" + chosen_intents[i]
                if key not in training_data.keys():
                    training_data[key] = [utterance]
                else:
                    training_data[key] += [utterance,]
            else: 
                # BLOCO DE TESTE. PARA RETIRAR
                if "dont_know" not in training_data.keys():
                    training_data["dont_know"] = [utterance]
                else:
                    training_data["dont_know"] += [utterance,]
                

        else:
            pass # Fazer algo quando a intent é NONE
        
        last_turn = turn

# Computa os slots obrigatórios para uma task ser dada como completa
for i in intents.values():
    i.computeSlots()

####################################################
#         RESPONSES AND ACTIONS DEFINITION         #
####################################################

last_frame = {}
index = 0
stories = ()
for item in json_file:
    story = ["- story: dialogue {}\n  steps:\n".format(index),]
    index += 1

    for turn in item["turns"]:
        if turn["speaker"] == "SYSTEM":
            continue

        frame = list(filter(lambda x: x["state"]["active_intent"] != "NONE", turn["frames"]))
        if frame != []:
            frame = frame[0]
            current_intent = frame["state"]["active_intent"]
            frame_slots = frame["state"]["slot_values"]
            
            intent_slots = intents[current_intent].mandatory
            intent_slots = list(filter(lambda x: x not in frame_slots.keys(), intent_slots))
            
            action = ""
            if intent_slots == []:
                action = "action_" + re.sub("-", "_", current_intent)
                if action not in actions:
                    actions += [action,]
            else:
                action = "utter_ask_"
                for s in intent_slots:
                    action += re.sub("-", "_", s) + "_"
                action = action[:-1]
                if action not in responses:
                    responses += [action,]

            for i in turn["chosen_intents"]:
                story += ["  - intent: {}\n".format(i),]
            story += "  - action: {}\n".format(action)

    stories += (story,)

####################################################
#               WRITE MODEL IN FILES               #
####################################################

# Escrever o domain
# Os slots estão a ser considerados como entidades
with open("Model\\domain.yml", "w") as f:
    intents_string = "\nintents:\n"
    for i in intents.keys():
        intents_string += "  - {}\n".format(i)
    
    entities = "\nentities:\n"
    slot_string = "\nslots:\n"

    for slot in slots:
        entities += "  - {}\n".format(slot)
        slot_string += "  {}:\n    type: text\n".format(slot)
    
    entities += "  - required_info\n"

    responses_string = "\nresponses:\n"
    for r in responses:
        responses_string += "  {}:\n  - text: {} response\n".format(r, r)

    actions_string = "\nactions:\n"
    for a in actions:
        actions_string += "  - {}\n".format(a)
        
    f.write("version: 2.0\n" + intents_string + entities + slot_string + responses_string + actions_string)

# Escrever a nlu
with open("Model\\data\\nlu.yml", "w") as f:
    nlu = "version: 2.0\n\nnlu:\n"
    for i in training_data.keys():
        nlu += '- intent: {}\n  examples: |\n'.format(i)
        for example in training_data[i]:
            nlu += '    - {}\n'.format(example)
        nlu += "\n"

    synonims_string = ""
    for s in synonims.keys():
        synonims_string += "\n- synonim: {}\n  examples: |\n".format(s)
        for syn in synonims[s]:
            synonims_string += "    - {}\n".format(syn)

    f.write(nlu + synonims_string)

# Escrever as stories
with open("Model\\data\\stories.yml", "w") as f:
    stories_string = "version: 2.0\n\nstories:\n\n"
    for story in stories:
        for step in story:
            stories_string += step
        stories_string += "\n"
    f.write(stories_string)