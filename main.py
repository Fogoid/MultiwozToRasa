import json
import yaml

current_intent = "NONE"
last_frame = {}
intents = {}
slots = [] 

with open("resourses\\multiwoz\\dev\\dialogues_001.json") as f:
    json_file = json.load(f)
    
    for item in json_file:
        for turn in item["turns"]:
            # Só se preocupa com as falas do utilizador
            if turn["speaker"] == "SYSTEM":
                continue

            frame = list(filter(lambda x: x["state"]["active_intent"] != "NONE", turn["frames"]))
            if frame != []:
                frame = frame[0]

                if current_intent != frame["state"]["active_intent"]: # Nova intent, ou seja existe uma frase relevante do lado do USER
                    current_intent = frame["state"]["active_intent"]
                    intents[current_intent] =  [turn["utterance"],] if current_intent not in intents.keys() else intents[current_intent] + [turn["utterance"],] 
                else: # Considerar como inform 
                    intents["inform"] = [turn["utterance"],] if "inform" not in intents.keys() else intents["inform"] + [turn["utterance"],]
                
                # Adicionar todas as intents que questionam algum parâmetro 
                # Esta implementação pode ter alguma ambiguidade em como resolver as intents
                if frame["state"]["requested_slots"] != []:
                    intent_name = "request"
                    for rs in frame["state"]["requested_slots"]:
                        intent_name += "_" + rs
                    intents[intent_name] = [turn["utterance"],] if intent_name not in intents.keys() else intents[intent_name] + [turn["utterance"],]
                
                # Obter os slots
                frame_slots = frame["state"]["slot_values"]
                slots += list(filter(lambda x: x not in slots, frame_slots))

            else:
                pass # Fazer algo quando a intent é NONE

# Escrever o domain
with open("Model\\domain.yml", "w") as f:
    domain = "intents:\n"
    for intent in intents:
        domain += "  - {}\n".format(intent)
    
    domain += "\nslots:\n"
    for slot in slots: 
        domain += "  {}:\n    type: unfeaturized\n".format(slot) 
    
    f.write(domain)

# Escrever a nlu
with open("Model\\data\\nlu.yml", "w") as f:
    nlu = "nlu:\n"
    for intent in intents.keys():
        nlu += '- intent: {}\n  examples: |\n'.format(intent)
        for example in intents[intent]:
            nlu += '    - {}\n'.format(example)
        nlu += "\n"

    f.write(nlu)

            