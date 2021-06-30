from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import string
import math
import random
import json
import re
import datetime

db_dir = "D:/Develop/MultiwozToRasa/resources/database/"

#########################################
#               BOOKINGS                #
#########################################

class ActionBookRestaurant(Action):
    def name(self) -> Text:
        return "action_book_restaurant"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Obter os parâmetros importantes
        name = tracker.get_slot("restaurant-name")
        date = tracker.get_slot("restaurant-bookday")
        time = tracker.get_slot("restaurant-booktime") 
        n_people = int(tracker.get_slot("restaurant-bookpeople")) 

        # Efetuar reserva de mesa
        all_reservations = {}
        with open(db_dir + "reservation_db.json") as f:
            all_reservations = json.load(f)

        important_reservations = filter(lambda x: x["name"] == name and x["time"] == time, all_reservations["restaurant"])
        n = n_people
        for i in important_reservations:
            n += i["seats"] 
        
        if n > 10:
            # Não há lugares suficientes para esta hora
            dispatcher.utter_message(text = "I'm sorry. We don't have avaiability for that time. Can you tell us another time?")
            return [SlotSet("restaurant-booktime"), None]
        
        reference = "".join(random.sample(string.ascii_letters, 4)) 
        reservation = {"name": name, "date": date, "time": time, "seats": n_people, "ref": reference}
        all_reservations["restaurant"] += [reservation,]
        
        with open(db_dir + "reservation_db.json", "w") as f:
            f.write(json.dumps(all_reservations))

        dispatcher.utter_message(text = "Your booking for {}, on {} at {} for {} people was made successfully. The reference number is {}.".format(
            name, date, time, n_people, reference 
        ))
        dispatcher.utter_message(response = "utter_need_anything")

        return []

class ActionBookHotel(Action):
    def name(self) -> Text:
        return "action_book_hotel"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Obter dados da reserva
        name = tracker.get_slot("hotel_name")
        check_in = tracker.get_slot("hotel-bookday")
        stay = int(tracker.get_slot("hotel-book-tay"))
        n_people = int(tracker.get_slot("hotel-bookpeople"))

        # Efetuar reserva dos quartos
        all_reservations = {}
        with open(db_dir + "reservation_db.json") as f:
            all_reservations = json.load(f)

        important_reservations = filter(lambda x: x["name"] == name and x["date"] == check_in, all_reservations["hotel"])
        n = math.ceil(n_people/2)
        for i in important_reservations:
            n += i["rooms"] 
        
        if n > 10:
            # Não há lugares suficientes para este hotel
            dispatcher.utter_message(text = "I'm sorry. We don't have avaiability for that day. Can you tell us another day?")
            return [SlotSet("restaurant-bookday"), None]
        
        reference = "".join(random.sample(string.ascii_letters, 4)) 
        reservation = {"name": name, "date": check_in, "stay": stay, "rooms": n_people, "ref": reference}
        all_reservations["hotel"] += [reservation,]
        
        with open(db_dir + "reservation_db.json", "w") as f:
            f.write(json.dumps(all_reservations))

        dispatcher.utter_message(text = "Your booking for {}, on {} for {} days for {} people was made successfully. The reference number is {}.".format(
            name, check_in, stay, n_people, reference 
        ))
        dispatcher.utter_message(response="utter_need_anything")

        return []

class ActionBookTrain(Action):
    def name(self) -> Text:
        return "action_book_train"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Obter dados da reserva
        day = tracker.get_slot("train-bookday")
        departure = tracker.get_slot("train-departure")
        destination = tracker.get_slot("train-destination")
        n_people = int(tracker.get_slot("train-bookpeople"))

        # Efetuar reserva dos quartos
        all_reservations = {}
        with open(db_dir + "reservation_db.json") as f:
            all_reservations = json.load(f)

        important_reservations = filter(lambda x: x["day"] == day and x["departure"] == departure and x["destination"] == destination, all_reservations["train"])
        n = n_people
        for i in important_reservations:
            n += i["seats"] 
        
        if n > 50:
            # Não há lugares suficientes para este comboio
            dispatcher.utter_message(text = "I'm sorry. We don't have avaiability for that day. Can you tell us another day?")
            return [SlotSet("train-bookday"), None]
        
        reference = "".join(random.sample(string.ascii_letters, 4)) 
        reservation = {"day": day, "departure": departure, "destination": destination, "seats": n_people, "ref": reference}
        all_reservations["train"] += [reservation,]
        
        with open(db_dir + "reservation_db.json", "w") as f:
            f.write(json.dumps(all_reservations))

        dispatcher.utter_message(text = "Your booking from {} to {} on {} for {} people was made successfully. The reference number is {}.".format(
            day, departure, destination, n_people, reference 
        ))
        dispatcher.utter_message(response="utter_need_anything")

        return []

#####################################
#               FIND                #
#####################################

def getDifference(t, l):

    t = t.split(":")
    t = datetime.time(t[0], t[1])
    
    l = l.split(":")
    l = datetime.time(l[0], l[1])
    
    delta = l - t
    
    return abs(delta.minute)
    
class ActionFindRestaurant(Action):
    
    def name(self) -> Text:
        return "action_find_restaurant"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name = tracker.get_slot("restaurant-name")

        if name != None:
            f = open(db_dir + "restaurant_db.json")
            restaurants = json.load(f)
            f.close()

            r = next(filter(lambda x: re.search(name, x["name"], re.IGNORECASE) != None, restaurants))

            [prange, food, area, address, pc] = [r["pricerange"], r["food"], r["area"], r["address"], r["postcode"]]

            dispatcher.utter_message(text = "{} is a {} {} restaurant in the {} located at {} {}".format(name, prange, food, area, pc, address))
            dispatcher.utter_message(text = "Do you want me to make a booking for you?")
        else:
            prange = tracker.get_slot("restaurant-pricerange")
            food = tracker.get_slot("restaurant-food")
            area = tracker.get_slot("restaurant-area")

            if prange != None and food != None and area != None:
                f = open(db_dir+"restaurant_db.json")
                restaurants = json.load(f)
                f.close()

                restaurants = list(filter(lambda x: x["pricerange"] == prange and x["food"] == food and x["area"] == area, restaurants))
                if len(restaurants) == 1:
                    restaurant = next(restaurants)
                    dispatcher.utter_message(text = "{} matches your criteria. Do you want to make a reservation?".format(restaurant["name"]))
                    return [SlotSet("restaurant-name"), restaurant["name"]]
                elif len(restaurants) == 0:
                    dispatcher.utter_message(text = "I'm sorry, I can't find a restaurant that fits your criteria. Do you want to change some?")
                else:
                    restaurants = list(restaurants)
                    r = min(3, len(restaurants))
                    message = restaurants[0]["name"]
                    for i in range(1, r):
                        message += "," +  restaurants[i]["name"]
                    dispatcher.utter_message(text = "{} match your criteria. Can you choose one of them?".format(message))
            else:
                details = filter(lambda x: x[1] is None, [("price range" ,prange),("type of food", food),("area", area)])
                message = "Could you please tell me what is the "
                for d in details:
                    message += d[0] + ", "
                message += "so we can narrow down the search for you?"
                dispatcher.utter_message(text = message)

        return []

class ActionFindHotel(Action):

    def name(self) -> Text:
        return "action_find_hotel"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
        name = tracker.get_slot("hotel-name")
        
        print("-- Action: Find Hotel --")
        print("Name: {}".format(tracker.get_slot("hotel-name")))
        print("Type: {}".format(tracker.get_slot("hotel-type")))
        print("Area: {}".format(tracker.get_slot("hotel-area")))
        print("Price Range {}:".format(tracker.get_slot("hotel-pricerange")))

        if name != None:
            f = open(db_dir+"hotel_db.json")
            hotels = json.load(f)
            f.close()

            h = next(filter(lambda x: re.search(name, x["name"], re.IGNORECASE) != None, hotels))
            extras = [("internet", h["internet"]), ("parking", h["parking"])]

            message = "{} is a {} star {} with {} price. ".format(name, h["stars"], h["type"], h["pricerange"])
            message += "It is located in the {} area, at the {} {}.".format(h["area"], h["address"], h["postcode"])
            if extras[0][1] == "yes" and extras[0][1] == "yes":
                message += "They also have internet and parking avaiable."
            elif extras[0][1] == "yes" or extras[0][1] == "yes":
                extras = next(filter(lambda x: x[1] == "yes", extras))
                message = "They also have {}".format(extras[0])
            
            dispatcher.utter_message(text = message)
            dispatcher.utter_message(text = "Can I make you a booking?")
        else:
            prange = tracker.get_slot("hotel-pricerange")
            htype = tracker.get_slot("hotel-type")
            area = tracker.get_slot("hotel-area")
            stars = tracker.get_slot("hotel-stars")

            if prange != None and htype != None and area != None:
                f = open(db_dir+"hotel_db.json")
                hotels = json.load(f)
                f.close()

                hotels = filter(lambda x: x["pricerange"] == prange and x["type"] == htype and x["area"] == area, hotels)
                if stars != None:
                    stars = int(stars)
                    hotels = filter(lambda x: x["stars"] == stars, hotels)
                hotels = list(hotels)
                n_hotels = len(hotels)

                if n_hotels == 1:
                    hotel = hotels[0]
                    dispatcher.utter_message(text = "{} matches your criteria. Do you want to make a reservation?".format(name))
                    return [SlotSet("hotel-name"), hotel["name"]]
                elif n_hotels == 0:
                    dispatcher.utter_message(text = "I'm sorry, I can't find an hotel that fits your criteria. Are you interested in another area, price range or type?")
                else:
                    r = min(3, n_hotels)
                    message = hotels[0]["name"]
                    for i in range(1, r):
                        message += ", " + hotels[i]["name"]
                    dispatcher.utter_message(text = "{} match your criteria. Can you choose one of them?".format(message))
            else:
                details = filter(lambda x: x[1] is None, [("price range" ,prange),("type of lodging", htype), ("area", area)])
                message = "Could you please tell me what is the "
                for d in details:
                    message += d[0] + ", "
                message += "so we can narrow down the search for you?"
                dispatcher.utter_message(text = message)

        return []

class ActionFindTrain(Action):
    
    def name(self) -> Text:
        return "action_find_train"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        day = tracker.get_slot("train-day")
        departure = tracker.get_slot("train-departure")
        destination = tracker.get_destination("train-destination")

        time = [tracker.get_slot("train-leaveat"), tracker.get_slot("train-arriveby")]
        if time == [None, None]:
            dispatcher.utter_message(text = "Can you give me the time you want to leave at or arrive by?")
            return []
        else:
            
            (key, time) = ("train-leaveat", time[0]) if time[0] != None else ("train-arriveby", time[1])     

            f = open(db_dir+"train_db")
            trains = json.load(f)
            f.close()

            trains = filter(lambda x: (x["day"], x["destination"], x["departure"]) == (day, destination, departure), trains)
            trains = list(filter(lambda x: getDifference(time, x[key]) <= 10, trains))
            train = min(trains, key=lambda x, y: getDifference(time, x[key]) < getDifference(time, y[key]))

            if len(trains) == 0:
                dispatcher.utter_message(text = "I'm sorry. There are no avaiable trains for the hours you specified. Do you want to select another hour or day to travel?")
                return [SlotSet("train-leaveat", None), SlotSet("train-arriveby", None)]
            else:
                dispatcher.utter_message(text = "I found a train for you. It leaves at {} and arrives by {}.".format(train["departure"], train["destination"]))
                dispatcher.utter_message(text = "Do you want me do book it for you?")

        return []


class ActionFindAttraction(Action):
    
    def name(self) -> Text:
        return "action_find_attraction"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name = tracker.get_slot("attraction-name")

        if name != None:
            f = open(db_dir+"attraction_db.json")
            data = json.load(f)
            f.close()
            attraction = next(filter(lambda x: re.search(x["name"], name, re.IGNORECASE) is not None, data))

            message = "{} is a {} located at the {} {}".format(name, attraction["type"], attraction["address"], attraction["postcode"])
            message += " at the {}. Their phone number is {}".format(attraction["area"], attraction["phone"])
            if attraction["entrance fee"] != "?":
                if attraction["entrance fee"] == "free":
                    message += "The entrance is free."
                else:
                    message += " The entrance fee is {}.".format(attraction["entrance fee"])

            dispatcher.utter_message(text = message)
        else:
            specifics = [("area", tracker.get_slot("attraction-area")), ("type", tracker.get_slot("attraction-type"))]
            specifics = list(filter(lambda x: x[1] != None, specifics))
            if specifics == []:
                dispatcher.utter_message(text = "Can you give me the area or the type of attraction you are looking for?")
            else:
                f = open(db_dir+"attraction_db.json")
                attractions = json.load(f)
                f.close()

                for (s, v) in specifics:
                    attractions = list(filter(lambda x: x[s] == v, attractions))
                
                if attractions == []:
                    dispatcher.utter_message(text = "I'm sorry. I can't find an attraction with the area and type you specified. Do you wan't to search for another type?")

                    return [SlotSet("attraction-type", None)]
                else:
                    if len(attractions) in (1, 2) or len(specifics) == 2:
                        attraction = attractions[0]
                        
                        dispatcher.utter_message(text = "{} fits your criteria perfectly".format(attraction["name"]))
                        message = "It is a {} located at the {} {}".format(attraction["type"], attraction["address"], attraction["postcode"])
                        message += " at the {}. Their phone number is {}".format(attraction["area"], attraction["phone"])
                        if attraction["entrance fee"] != "?":
                                        if attraction["entrance fee"] == "free":
                                            message += "The entrance is free."
                                        else:
                                            message += " The entrance fee is {}.".format(attraction["entrance fee"])

                        dispatcher.utter_message(text = message)
                        dispatcher.utter_message(response ="utter_need_anything")
                    else:
                        slot_to_ask = "area" if specifics[0][0] == "type" else "type"
                        dispatcher.utter_message(text = "I have several options. Can you give me the {} you are looking for so we can narrow it down?".format(slot_to_ask))

        return []


class ActionFindTaxi(Action):

    def name(self) -> Text:
        return "action_find_taxi"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        times = [tracker.get_slot("taxi-leaveat"), tracker.get_slot("taxi-arriveby")]
        if times == [None, None]:
            dispatcher.utter_message(text = "Can you give the the time to pick you up?")
        else:
            f = open(db_dir+"taxi_db.json")
            taxis = json.load(f)
            f.close()

            color = random.choice(taxis["taxi_colors"])
            brand = random.choice(taxis["taxi_types"])
            numbers = random.choices(range(9), 11)
            number = "".join(str(numbers))

            dispatcher.utter_message(text = "A {} {} is going to pick you up. The driver's phone number is {}".format(color, brand, number))
            dispatcher.utter_message(response = "utter_need_anything")

        return []

class ActionFindHospital(Action):
    
    def name(self) -> Text:
        return "action_find_hospital"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text = "The nearest hospital is on Hills Rd, Cambridge CB20QQ")
        dispatcher.utter_message(response = "utter_need_anything")

        return []
            
        
