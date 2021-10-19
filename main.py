import json
import os
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

def findRequestedSlotsInUtterance(slots, utter):
    found_values = []
    for s in slots:
        s = s.split("-")[1]
        utter, found_value = findSlotUsingSpaces(s, utter)
        found_values = found_values + [found_value,] if found_value != None else found_values
    return utter, found_values

def findSlotUsingSpaces(slot, utter):
    modified_slot = slot
    index = 0
    while index != len(slot):
        pattern = re.compile(modified_slot, flags=re.IGNORECASE)
        result = pattern.search(utter)
        if result != None:
            for r in result.regs:
                previous_letter = utter[r[0] - 1] if r[0] != 0 else " "
                next_letter = utter[r[1]] if r[1] < len(utter) else " "
                if previous_letter != " ":
                    continue
                elif re.search(r"[a-zA-Z]", next_letter, re.IGNORECASE) != None:
                    while r[1] < len(utter) and utter[r[1]] not in [" ", ".", ",", "?"]:
                        r = (r[0], r[1] + 1)
                    modified_slot = utter[r[0]:r[1]]
                elif next_letter not in [" ", ".", ",", "?"]:
                    continue
                
                replaceable = "[{}]({})".format(modified_slot, "required_info")
                return utter[:r[0]] + replaceable + utter[r[1]:], modified_slot
            index += 1
        else:
            modified_slot = slot[:index] + " " + slot[index:]
            index += 1
    return utter, None

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

def isPresent(slot_list, slot):
    for s in slot_list:
        if type(s) is tuple and s[0] == slot:
            return True
        elif s == slot:
            return True
    return False 

# Change for the domain that model is being created for (Ignore for Multi domain model)
def validDialog(dialog):
    if re.search(r"SNG", dialog["dialogue_id"]) == None or dialog["services"] != ["restaurant"]:
        return False
    for turn in dialog["turns"]:
        if turn["speaker"] == "SYSTEM":
            continue
        frames = list(filter(lambda x: x["state"]["active_intent"] != "NONE" and x["service"] != "restaurant", turn["frames"]))
        if frames != []:
            return False
    return True

####################################################
#                CONTROL VARIABLES                 #
####################################################

# Domain required variables
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

# Control Variables
current_intent = "NONE"
last_frame = {}
frame_slots = {}
last_turn = None

time_regex = r"(\d){2}:(\d){2}"
number_regex = r"(\d+)"

####################################################
#                   DIALOGUES LOAD                 #
####################################################

# Load MultiWOZ dialogues
json_file = []
directory = "resources\\multiwoz\\train\\"
for _, _, files in os.walk(directory):
    for file in files:
        with open(directory + file) as f:

            json_file += json.load(f) # Comment to create domain specific model 
            #json_file += list(filter(lambda x: validDialog(x), json.load(f))) # Uncomment to create domain specific model 

####################################################
#      INTENTS, ENTITIES AND SLOTS DEFINITION      #
####################################################

# Go threw each dialogue to get the intents, entities, and mandatory slots for each task
for item in json_file:
    current_intent = ""
    this_turn_slots = {}
    verified_intents = []
    last_turn = None

    for t in range(len(item["turns"])):
        turn = item["turns"][t]

        if turn["speaker"] == "SYSTEM":
            continue

        turn["chosen_intents"] = []
        utterance = turn["utterance"]
        utterance = re.sub(r"[.,]", " ", utterance)
        
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
                
                ns = list(filter(lambda x: not isPresent(slots, x), intent_frame["state"]["slot_values"].keys()))
                for i in range(len(ns)):
                    sv = intent_frame["state"]["slot_values"][ns[i]][0]
                    if re.search(time_regex, sv) != None:
                        ns[i] = (ns[i], time_regex)
                    elif re.search(number_regex, sv) != None:
                        ns[i] = (ns[i], number_regex)
                       
                slots += ns
                intents[current_intent].addSlotCount(list(intent_frame["state"]["slot_values"].keys()))

            current_intent = turn_best_intent

        # Find slot values in utterance
        new_this_turn_slots = this_turn_slots.copy()
        frames = list(filter(lambda x: x["service"] in this_turn_slots.keys(), turn["frames"]))
        for frame in frames:
            for slot in frame["state"]["slot_values"].keys():
                original_utterance = utterance
                if slot not in this_turn_slots[frame["service"]]:
                    continue
                slot_values = frame["state"]["slot_values"][slot]
                for val in slot_values:
                    pattern = re.compile(val, flags=re.IGNORECASE)
                    result = pattern.search(utterance)
                    if result != None:
                        for r in result.regs:
                            previous_letter = utterance[r[0] - 1] if r[0] != 0 else " "
                            next_letter = utterance[r[1]] if r[1] < len(utterance) else " "
                            if previous_letter != " ":
                                continue
                            elif re.search(r"[a-zA-Z]", next_letter, re.IGNORECASE) != None:
                                while r[1] < len(utterance) and utterance[r[1]] not in [" ", ".", ",", "?"]:
                                    r = (r[0], r[1] + 1)
                                if re.search(time_regex, utterance[r[0]:r[1]], re.IGNORECASE) == None and re.search(number_regex, utterance[r[0]:r[1]], re.IGNORECASE) == None:
                                    AddSynonim(val, utterance[r[0]:r[1]])
                                val = utterance[r[0]:r[1]]
                            elif next_letter not in [" ", ".", ",", "?"]:
                                continue
                            
                            replaceable = "[{}]({})".format(val, slot)
                            utterance = utterance[:r[0]] + replaceable + utterance[r[1]:]
                            break
                if utterance == original_utterance:
                    new_this_turn_slots[frame["service"]].remove(slot)
                    if new_this_turn_slots[frame["service"]] == []:
                        del new_this_turn_slots[frame["service"]]
        this_turn_slots = new_this_turn_slots

        # Get slots asked by user.
        turn["all_requested"] = []
        requested_slots = getRequestedSlots(turn["frames"])
        if requested_slots != []:
            utterance, requested_info = findRequestedSlotsInUtterance(requested_slots, utterance)
            if requested_info != []:
                chosen_intents += ["request"]
                turn["all_requested"] = requested_info

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

        turn["intent_key"] = turn_intent_key
        training_data[turn_intent_key] = [utterance,] if turn_intent_key not in training_data.keys() else training_data[turn_intent_key] + [utterance,]

        turn["utterance_slots"] = this_turn_slots
        last_turn = turn

# Computes the mandatory slots for each task be marked as complete
for i in intents.values():
    i.computeSlots()
    # print(i.name, i.mandatory) # Uncomment to see what are the mandatory slots for each intent 

# ####################################################
# #         RESPONSES AND ACTIONS DEFINITION         #
# ####################################################

# Creating actions, responses, stories and rules going threw the MultiWOZ dialogues again 

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
                if turn["utterance_slots"] != {} or turn["all_requested"] != []:
                    story += ["    entities:\n",]
                    for s in turn["utterance_slots"].keys():
                        sls = next(filter(lambda x: x["service"] == s, turn["frames"]))["state"]["slot_values"]
                        for slot in turn["utterance_slots"][s]:
                            story += ["    - {}: {}\n".format(slot, sls[slot][0])]
                    
                    for r in turn["all_requested"]:
                        story += ["    - required_info: {}\n".format(r)]
                    
                story += ["  - action: {}\n".format(action),]

    if specific_intent == "dont_know":
        continue

    stories += (story,)

####################################################
#               WRITE MODEL IN FILES               #
####################################################

del intents["dont_know"]
del training_data["dont_know"]
del intents["NONE"]

# Write Rasa domain
# Slots are considered both Rasa slots and entitities
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
        slot_value = slot
        if type(slot) is tuple:
            slot_value = slot[0]
        
        entities += "  - {}\n".format(slot_value)
        slot_string += "  {}:\n    type: text\n".format(slot_value)
    
    entities += "  - required_info\n"

    responses_string = "\nresponses:\n"
    for r in responses:
        responses_string += "  {}:\n  - text: {} response\n".format(r, r)

    actions_string = "\nactions:\n"
    for a in actions:
        actions_string += "  - {}\n".format(a)
        
    f.write("version: \"2.0\"\n" + intents_string + entities + slot_string + responses_string + actions_string)

# Write NLU training data
with open("Model\\data\\nlu.yml", "w") as f:
    nlu = "version: \"2.0\"\n\nnlu:\n"

    for slot in slots:
        if type(slot) is not tuple:
            continue
        nlu += "- regex: {}\n  examples: |\n    - {}\n\n".format(slot[0], slot[1])

    for i in training_data.keys():
        nlu += '- intent: {}\n  examples: |\n'.format(i)
        for example in training_data[i]:
            nlu += '    - {}\n'.format(example)
        nlu += "\n"

    synonims_string = ""
    for s in synonims.keys():
        synonims_string += "\n- synonym: {}\n  examples: |\n".format(s)
        for syn in synonims[s]:
            synonims_string += "    - {}\n".format(syn)

    f.write(nlu + synonims_string)

# Writing Stories
with open("Model\\data\\stories.yml", "w") as f:
    stories_string = "version: \"2.0\"\n\nstories:\n\n"
    for story in stories:
        for step in story:
            stories_string += step
        stories_string += "\n"
    f.write(stories_string)

# Writing Rules
with open("Model\\data\\rules.yml", "w") as f:
    rules_string = '''version: \"2.0\"

rules:

- rule: give requested info
  steps:
  - intent: request
  - action: action_get_requested_information'''
    f.write(rules_string)   
