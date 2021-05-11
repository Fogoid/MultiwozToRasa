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

def getBestIntent(current, slots):
    intent = "NONE"
    n_slots = -1
    
    current = list(filter(lambda x: x["state"]["active_intent"] != "NONE", current))
    for f in current:
        service_slot_num = 0 if f["service"] not in slots.keys() else len(slots[f["service"]])
        if service_slot_num > n_slots:
            intent = f["state"]["active_intent"]
            n_slots = service_slot_num

    return intent

# SLOTS: { "service_1" : [slot_1, slot_2, ..., slot_n], "service_2" : [slot_1, slot_2, ..., slot_n], ..., "service_m" : [slot_1, slot_2, ..., slot_n]}
def getTurnSlots(previous_slots, current_frame, lt_frames=None):
    slots = {}
    for cf in current_frame:
        if cf["state"]["active_intent"] == "NONE":
            continue
        
        service = cf["service"]
        previous_service_slots = previous_slots[service] if service in previous_slots.keys() else []
        new_slots = []
        for sv in cf["state"]["slot_values"].keys():
            if sv not in previous_service_slots:
                new_slots += [sv]
            else:
                imp_frame = next(filter(lambda x: x["service"] == service, lt_frames))
                if imp_frame["state"]["slot_values"][sv] != cf["state"]["slot_values"][sv]:
                    new_slots += [sv]

        if len(new_slots) > 0:
            slots[service] = new_slots

    return slots

def getRequestedSlots(current):
    requested = []
    for cf in current:
        requested += cf["state"]["requested_slots"]
    return requested
        

####################################################
#                CONTROL VARIABLES                 #
####################################################

# variaveis necessárias para o dominio
intents = { 
    "inform" : Task("inform"), 
    "request" : Task("request"), 
    "goodbye": Task("goodbye"), 
    "dont_know" : Task("dont_know") 
    }
slots = []
actions = ["action_get_requested_information"]
responses = ["utter_need_anything", "utter_say_goodbye"]
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
    this_turn_slots = {}
    verified_intents = []

    for turn in item["turns"]:
        # Só se preocupa com as falas do utilizador
        if turn["speaker"] == "SYSTEM":
            continue

        turn["chosen_intents"] = []
        utterance = turn["utterance"]
        
        # Get slots from this turn
        last_turn_slots = {}
        this_turn_slots = {}
        if last_turn == None:
            this_turn_slots = getTurnSlots(last_turn_slots, turn["frames"])
        else:
            last_turn_slots = getTurnSlots({}, last_turn["frames"])
            this_turn_slots = getTurnSlots(last_turn_slots, turn["frames"], last_turn["frames"])

        # Get and choose intents for this turn
        turn_best_intent = getBestIntent(turn["frames"], this_turn_slots)
        
        if current_intent == turn_best_intent and turn_best_intent != "NONE":
            chosen_intents = ["inform",]
            turn["real_intent"] = turn_best_intent
        else:
            chosen_intents = [turn_best_intent,]
            if current_intent != "":
                AddIntent(current_intent)
                intent_frame = next(filter(lambda x: x["state"]["active_intent"] == current_intent, last_turn["frames"]))
                
                slots += list(filter(lambda x: x not in slots, intent_frame["state"]["slot_values"].keys()))
                intents[current_intent].addSlotCount(list(intent_frame["state"]["slot_values"].keys()))

            current_intent = turn_best_intent

        requested_slots = getRequestedSlots(turn["frames"])
        if requested_slots != []:
            chosen_intents += ["request",]
            utterance = findRequestedSlotsInUtterance(requested_slots, utterance)

        # Encontrar os valores dos slots na utterance
        frames = list(filter(lambda x: x["service"] in this_turn_slots.keys(), turn["frames"]))
        for frame in frames:
            for slot in frame["state"]["slot_values"].keys():
                if slot not in this_turn_slots[frame["service"]]:
                    continue
                slot_values = frame["state"]["slot_values"][slot]
                for val in slot_values:
                    pattern = re.compile(val, flags=re.IGNORECASE)
                    result = pattern.search(utterance)
                    if result != None:                            
                        remainder = utterance[result.lastindex:].split()[0]
                        if ")" in remainder or "]" in remainder:
                            continue

                        replaceable = "[{}]({})".format(val, slot)
                        utterance = pattern.sub(replaceable, utterance)
                        break

        # Get multiple intent classification
        if chosen_intents[0] == "NONE":
            frames_with_active_intent = list(filter(lambda x: x["state"]["active_intent"] != "NONE", turn["frames"]))
            if len(frames_with_active_intent) == 0:
                chosen_intents[0] = "goodbye"
        elif chosen_intents[0] == "inform" and this_turn_slots == {}:
            if len(chosen_intents) > 1:
                chosen_intents = chosen_intents[1:]
            else:
                chosen_intents = ["dont_know"]
        
        turn["chosen_intents"] = chosen_intents
        turn_intent_key = chosen_intents[0]
        for index in range(1, len(chosen_intents)):
            turn_intent_key += "+" + chosen_intents[index]
        turn["intent_key"] = turn_intent_key
        training_data[turn_intent_key] = [utterance,] if turn_intent_key not in training_data.keys() else training_data[turn_intent_key] + [utterance,]

        last_turn = turn

# Computa os slots obrigatórios para uma task ser dada como completa
for i in intents.values():
    i.computeSlots()

# ####################################################
# #         RESPONSES AND ACTIONS DEFINITION         #
# ####################################################

last_frame = {}
index = 0
stories = ()
for item in json_file:
    story = ["- story: dialogue {}\n  steps:\n".format(index),]
    index += 1
    specific_intent = "NONE"

    for turn in item["turns"]:
        if turn["speaker"] == "SYSTEM":
            continue

        if turn["intent_key"] == "goodbye":
            story += ["  - intent: goodbye\n",]
            story += ["  - action: utter_say_goodbye\n",]
        else:
            specific_intent = turn["chosen_intents"][0]
            if specific_intent != "request":
                if specific_intent == "inform":
                    specific_intent = turn["real_intent"]
                elif specific_intent == "dont_know":
                    break
                
                intent_frame = next(filter(lambda x: x["state"]["active_intent"] == specific_intent, turn["frames"]))
                frame_slots = intent_frame["state"]["slot_values"]
                    
                intent_slots = intents[specific_intent].mandatory
                intent_slots = list(filter(lambda x: x not in frame_slots.keys(), intent_slots))
                    
                action = ""
                if intent_slots == []:
                    action = "action_" + re.sub("-", "_", specific_intent)
                    if action not in actions:
                        actions += [action,]
                else:
                    action = "utter_ask_"
                    for s in intent_slots:
                        action += re.sub("-", "_", s) + "_"
                    action = action[:-1]
                    if action not in responses:
                        responses += [action,]
                
                story += ["  - intent: {}\n".format(turn["intent_key"]),]
                story += ["  - action: {}\n".format(action),]
            
            if "request" in turn["chosen_intents"]:
                story += ["  - action: action_get_requested_information\n",]

    if specific_intent == "dont_know":
        continue

    stories += (story,)

####################################################
#               WRITE MODEL IN FILES               #
####################################################

del intents["dont_know"]
del training_data["dont_know"]
del intents["NONE"]

# Escrever o domain
# Os slots estão a ser considerados como entidades
with open("Model\\domain.yml", "w") as f:
    intents_string = "\nintents:\n"
    for i in intents.keys():
        intents_string += "  - {}\n".format(i)
    extra_intents = filter(lambda x: x not in intents.keys(), training_data.keys())
    for i in extra_intents:
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
        
    f.write("version: \"2.0\"\n" + intents_string + entities + slot_string + responses_string + actions_string)

# Escrever a nlu
with open("Model\\data\\nlu.yml", "w") as f:
    nlu = "version: \"2.0\"\n\nnlu:\n"
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
    stories_string = "version: \"2.0\"\n\nstories:\n\n"
    for story in stories:
        for step in story:
            stories_string += step
        stories_string += "\n"
    f.write(stories_string)
