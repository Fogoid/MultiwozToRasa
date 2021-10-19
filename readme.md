The files presented in this repository are in the context of the Master Thesis *Making Chatbots for Customer Support: Fast and Serious*. In this files, we present the process we used to create a Rasa agent using the MultiWOZ dataset. If you want details on the implementation check **Chapter 4**. 

To recreate the Rasa model we used for testing, perform the following steps:
1. Clone this repository
2. Create a Resources folder, and put inside the MultiWOZ dataset, in a folder called multiwoz (In this work, we used MultiWOZ 2.2 available in https://github.com/budzianowski/multiwoz/tree/master/data/MultiWOZ_2.2)
3. Create a folder called Model, and inside, use `rasa init` to create a basic agent.
5. (Optional) If you want to create a single domain model instead of multi domain, comment line 152 of `main.py` file, and uncomment line 153
6. (Optional) If you want any other domain besides the Restaurant model, go to the function `ValidDialog` and change any references to `restaurant` to the other domain you pretend 
7. Run `main.py`

In case you want to run the model:
1. Go inside the `Model` folder
3. Edit the `config.yml` file to have configuration as we present below.
4. Change the text of the responses in the `domain.yml` file (We present our responses section of the domain below for the restaurant domain).
5. Download the `db` folder available in https://github.com/budzianowski/multiwoz
6. Implement the actions in the file `/actions/actions.py` (We present the logic used below for the Restaurant domain and for the Hotel domain).
8. Use `rasa train`.
10. You can now start the action server using `rasa run actions` and interact with the model by using `rasa shell`.

### Model Configuration

```YAML
pipeline:
  - name: WhitespaceTokenizer
    "intent_tokenization_flag": True
    "intent_split_symbol": "+"
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: char_wb
    min_ngram: 1
    max_ngram: 4
  - name: DIETClassifier
    epochs: 80
    constrain_similarities: true
  - name: EntitySynonymMapper
  - name: ResponseSelector
    epochs: 80
    constrain_similarities: true
  - name: FallbackClassifier
    threshold: 0.3
    ambiguity_threshold: 0.1
```

### Responses

```YAML
responses:
  utter_say_goodbye:
  - text: Thank you! Goodbye
  utter_ask_restaurant_name:
  - text: Can you tell me the name of the restaurant, please?
  utter_ask_restaurant_bookpeople_restaurant_booktime_restaurant_name:
  - text: Please tell me the restaurant name, the number of people, and the time of the booking.
  utter_ask_restaurant_bookday:
  - text: For what day is the reservation?
  utter_ask_restaurant_booktime_restaurant_name:
  - text: Tell me the name and the time of the reservation, please.
  utter_ask_restaurant_booktime:
  - text: Can you tell me the time of the booking?
  utter_ask_restaurant_bookpeople_restaurant_booktime:
  - text: Tell me the day and the number of people for the booking, please.
  utter_ask_restaurant_bookpeople_restaurant_name:
  - text: Can you tell me the name of the restaurant and the number of people?
  utter_ask_restaurant_bookday_restaurant_booktime:
  - text: What is the day and time of the booking?
  utter_ask_restaurant_bookday_restaurant_booktime_restaurant_name:
  - text: Please tell me the name of the restaurant, and the day and time of the reservation.
  utter_ask_restaurant_bookpeople:
  - text: How many people is the booking for?
  utter_ask_restaurant_bookday_restaurant_name:
  - text: What is the name of the restaurant, and the day of the booking?
```

### Logic for implementing restaurant and hotel domain actions

For the restaurant domain, we define the actions **action_find_restaurant** and **action_book_restaurant**, whereas for the hotel domain we define **action\_find\_hotel** and **action_book_hotel**. Note that since both models' actions have the same functionality, the logic implemented is similar

#### Action_find_restaurant and Action_find_hotel}

To find a restaurant or a place to stay, we split the functionality in two parts:

- If the user gives the name of the restaurant/place, then search for the restaurant and give information about the same.
- If the user intents to find a restaurant/place, use the criteria to find a suitable one.

That said, there are some details for each of the parts. For the first part, even if the user has given the name of the restaurant/place, if there is new criteria such as the price range, then we proceed to the second part instead of giving information about the restaurant/place given. This property prevents the user from being stuck in the interaction if it has given the name of the restaurant previously and wants to find another one.

Furthermore, when displaying the information about the restaurant/place the user referenced, the agent also displays a message asking if the user wants to make a booking, as shown below:

*If you wish to make a reservation, please state the number of people, the time of booking/days of your stay or the day of the week/check-in.*

We decided to structure the sentence this way instead of a sentence like "Do you want to make a booking?" to guide better the user during the conversation and avoid errors. This is because our models do not recognize the meaning of yes/no which represent an affirmation or a negation.

Moving now to the second part of the functionality, there are several details we consider. If no criteria has been given during the conversation, then the action responds with the following sentence:

*Could you please tell me the price range, type of food/lodging or area of town of the restaurant/place to stay?*

Then, after checking the existence of criteria, we proceed to find any restaurants/places whose properties match with the given criteria. In here, there are 3 possibilities:

- If there is only one restaurant/place, we use the same logic as we would when given the name of the restaurant/place by the user
- If there are two or three places, we show the user the eligible restaurants/places and ask him/her to select one.
- If there are four or more restaurants/places, we select randomly three restaurants/places, and show the user for him/her to select one 

Given these 3 possibilities, one example sentence given by the agent is the following:

*the missing sock, yu garden, backstreet bistro match your criteria. Can you please select one?*

For last, there is a final property. If the user has not given all possible criteria (for example, give price range and type of restaurant/lodging but not the area of town), the agent also displays a message that the user can give more criteria. An example message can be:

*Optionally, you can give the city area so we can narrow down the search.*

#### Action_book_restaurant and Action_book_hotel

For the booking, we start by verifying the value of all slots required. For example, for the restaurant, we start by checking if the restaurant name has been given by the user, and also check if it exists. In case any of these properties fail, then a message is sent for the user to tell the restaurant name it is trying to make a booking, just as shown below:

*I can not find the restaurant/place you told me. Can you please tell me the name of the restaurant/place again?*

After the check on the restaurant name, we proceed to verify if all the slots required are set, such as the day of booking, time of booking and the number of people for the restaurant. In case any of these slots, the agent ask the agent for the missing slots:

*Please tell me the number of nights in order to complete the booking.*

After checking all the slots, we then proceed to make the booking. There are two possibilities. First, if no booking was done during the conversation with the user, then a booking is done. However, if a booking was already done, then we proceed to change the properties of the booking. This way, we are able to extend the functionalities of the agent, allowing the user to modify its booking in case of a mistake by either the user or the agent. In either case, the user is reported of the situation with a sentence specifying the details of the reservation. The message given by the agent to the user is, for example:

*Your booking for autumn house for 3 days starting monday for 2 people has been done successfully. Can I help you with anything else?*
