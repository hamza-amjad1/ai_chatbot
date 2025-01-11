import requests
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, SlotSet, FollowupAction
import re
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ActionAskLanguage(Action):
    def name(self) -> Text:
        return "action_ask_language"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        messages = [
            "What language would you like to use?",
            "You can choose from English, Japanese, or Chinese.",
            "Please type your preferred language."
        ]

        for message in messages:
            dispatcher.utter_message(text=message)

        return []


class ActionWelcome(Action):

    def name(self) -> Text:
        return "action_welcome"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        messages = [
            "Welcome to Easy Cinema!",
            "How may I assist you today?"
        ]

        for message in messages:
            dispatcher.utter_message(text=message)

        return []


class ActionSetLanguage(Action):
    def name(self):
        return "action_set_language"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        selected_language = tracker.latest_message['text'].lower()

        if "english" in selected_language or "eng" in selected_language:
            dispatcher.utter_message(response="utter_english_selected")
        elif "japanese" in selected_language or "jp" in selected_language:
            dispatcher.utter_message(response="utter_japanese_selected")
        elif "chinese" in selected_language or "cn" in selected_language or 'chi' in selected_language:
            dispatcher.utter_message(response="utter_chinese_selected")
        else:
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems like your message got cut off.")
            dispatcher.utter_message(
                text="Could you please provide more details or clarify what you meant?")
            dispatcher.utter_message(
                text="Could you please choose from English, Japanese, or Chinese?")
            dispatcher.utter_message(
                text="I'm here to help with any inquiries about our Athena bot service! 😊")
            return [UserUtteranceReverted()]

        return []


class ActionDetectBookingKeywords(Action):
    def name(self):
        return "action_detect_booking_keywords"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "").lower()

        # Define keywords to look for
        keywords = ["movie", "book", "ticket", "film", "show"]
        detected_keywords = [word for word in keywords if word in user_message]

        # Respond if keywords are found
        if detected_keywords:
            dispatcher.utter_message(
                text=f"I see you want to book a show. Let's proceed!"
            )
            # Trigger the movie booking flow
            return [FollowupAction("action_fetch_movies")]
        else:
            dispatcher.utter_message(
                text="Sorry, I couldn't understand your request. Could you clarify?"
            )
            # Revert the user's input if no relevant keywords are found
            return [UserUtteranceReverted()]


class ActionRecommendMovies(Action):
    def name(self):
        return "action_recommend_movies"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Get the user's preferred language
        user_language = tracker.get_slot("language")

        dispatcher.utter_message(text="Here are some popular English movies:\n1. The Shawshank Redemption\n2. The Dark Knight\n3. Inception")

        dispatcher.utter_message(text="The movies that are currently in cinemas are:")
        return [FollowupAction("action_fetch_movies")]

class ActionFetchMovies(Action):
    def name(self):
        return "action_fetch_movies"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        import requests

        api_key = os.getenv("TMDB_API_KEY")
        base_url = "https://api.themoviedb.org/3"

        # Define the movies to fetch
        movies_to_fetch = ["Zodiac", "Constantine"]

        # Custom poster URLs
        custom_posters = {
            "Zodiac": "https://i.pinimg.com/736x/08/8c/43/088c43d5a8e9d47d2ea03719062699cf.jpg",
            "Constantine": "https://media.posterlounge.com/img/products/760000/759054/759054_poster.jpg"
        }

        movie_details = []

        for movie in movies_to_fetch:
            search_url = f"{base_url}/search/movie?api_key={api_key}&query={movie}"
            response = requests.get(search_url)
            results = response.json().get('results', [])

            if results:
                movie_info = results[0]
                movie_title = movie_info['title']
                movie_description = movie_info['overview']

                # Use custom poster if available, otherwise fetch from TMDB
                movie_poster = custom_posters.get(
                    movie_title,
                    f"https://image.tmdb.org/t/p/w500{movie_info['poster_path']}" if movie_info.get('poster_path') else None
                )

                movie_details.append(
                    (movie_title, movie_description, movie_poster))

        if movie_details:
            # Send details for each movie
            for index, (title, description, poster) in enumerate(movie_details, start=1):
                # Group title and description together
                movie_message = f"{index}. {title}\nDescription: {description}"
                dispatcher.utter_message(text=movie_message)

                # Send poster image
                if poster:
                    dispatcher.utter_message(image=poster)

            # Send a final prompt for user choice
            dispatcher.utter_message(
                text="Please reply with the number of your choice (e.g., 1 for Zodiac, 2 for Constantine)."
            )
        else:
            dispatcher.utter_message(
                text="Sorry, I couldn't fetch the movie details."
            )

        return []

class ActionSendMovieTemplate(Action):
    def name(self):
        return "action_send_movie_template"

    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        dispatcher.utter_message(
            json_message={
                "type": "template",
                "template_name": "moviechoice",
                "language": "en",
                "parameters": []
            }
        )
        return []


class ActionSetMovie(Action):
    def name(self):
        return "action_set_movie"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Movie mapping
        movie_mapping = {
            "1": "Zodiac",
            "2": "Constantine"
        }

        # Get user input
        user_input = tracker.latest_message.get("text", "").lower()

        # Try to match a number first
        import re
        match = re.search(r"\b(1|2)\b", user_input)  # Matches "1" or "2"

        if match:
            movie_number = match.group(1)  # Extract the matched number
            selected_movie = movie_mapping.get(movie_number)

            if selected_movie:
                # If valid movie, confirm and set the slot
                dispatcher.utter_message(
                    text=f"You have selected {selected_movie}."
                )
                dispatcher.utter_message(
                    text="Please select the desired time for the show."
                )
                return [SlotSet("movie", selected_movie), FollowupAction("action_fetch_showtimes")]
            else:
                dispatcher.utter_message(
                    text="Sorry, I couldn't find a movie for that choice. Please try again."
                )
                return [UserUtteranceReverted()]
        else:
            # If no number is matched, search for the movie name
            for movie_number, movie_name in movie_mapping.items():
                if movie_name.lower() in user_input:
                    dispatcher.utter_message(
                        text=f"You have selected {movie_name}."
                    )
                    dispatcher.utter_message(
                        text="Please select the desired time for the show."
                    )
                    return [SlotSet("movie", movie_name), FollowupAction("action_fetch_showtimes")]

            # If neither number nor movie name is found
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems like your message got cut off."
            )
            dispatcher.utter_message(
                text="Could you please provide more details or clarify what you meant?"
            )
            dispatcher.utter_message(
                text="Please reply with the number or name of the movie you'd like to select (e.g., 1 for Zodiac, 2 for Constantine)."
            )
            dispatcher.utter_message(
                text="I'm here to help with any inquiries about our Athena bot service! 😊"
            )
            return [UserUtteranceReverted()]


class ActionFetchShowtimes(Action):
    def name(self):
        return "action_fetch_showtimes"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Sample showtimes for demonstration purposes
        showtime_mappings = {
            "Zodiac": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM"],
            "Constantine": ["11:00 AM", "02:00 PM", "05:00 PM", "08:00 PM"],
        }

        selected_movie = tracker.get_slot("movie")

        if not selected_movie or selected_movie not in showtime_mappings:
            dispatcher.utter_message(
                text="I couldn't find showtimes for the selected movie. Could you please confirm the movie first?"
            )
            return []

        # Fetch showtimes for the selected movie
        showtimes = showtime_mappings[selected_movie]
        showtimes_list = "\n".join(
            [f"{i+1}: {time}" for i, time in enumerate(showtimes)])

        # Send showtimes to the user
        dispatcher.utter_message(
            text=f"Here are the available showtimes for {selected_movie}:\n{showtimes_list}\nPlease reply with the number corresponding to your preferred showtime."
        )

        return []


class ActionSetShowtime(Action):
    def name(self) -> Text:
        return "action_set_showtime"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        import re
        from datetime import datetime

        # Sample showtimes for demonstration purposes
        showtime_mappings = {
            "Zodiac": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM"],
            "Constantine": ["11:00 AM", "02:00 PM", "05:00 PM", "08:00 PM"],
        }

        selected_movie = tracker.get_slot("movie")
        user_input = tracker.latest_message.get("text", "").strip()

        if not selected_movie or selected_movie not in showtime_mappings:
            dispatcher.utter_message(
                text="I couldn't find the movie you selected. Could you confirm the movie first?"
            )
            return [SlotSet("showtime", None)]

        showtimes = showtime_mappings[selected_movie]

        # Normalize available showtimes for consistent comparison
        normalized_showtimes = [
            datetime.strptime(st, "%I:%M %p").strftime("%I:%M %p") for st in showtimes
        ]

        # Regex pattern to match times, including "AM/PM" variations
        time_pattern = r"\b(\d{1,2}(:\d{2})?\s?(?:AM|PM|A\.M\.|P\.M\.|A\.M|P\.M))\b"

        # Check for time-based input first (explicit "AM/PM" or its variations)
        match_time = re.search(time_pattern, user_input, re.IGNORECASE)
        if match_time:
            input_time = match_time.group(1).strip().upper().replace(".", "")  # Normalize to "AM"/"PM"

            try:
                # Normalize the user input time
                parsed_time = (
                    datetime.strptime(input_time, "%I:%M %p")
                    if ":" in input_time
                    else datetime.strptime(input_time, "%I %p")
                )
                normalized_input_time = parsed_time.strftime("%I:%M %p")

                # Compare against normalized showtimes
                if normalized_input_time in normalized_showtimes:
                    dispatcher.utter_message(
                        text=f"You have selected {normalized_input_time} for {selected_movie}."
                    )
                    dispatcher.utter_message(
                        text="Please select the location to watch the movie."
                    )
                    dispatcher.utter_message(response="utter_ask_location")
                    return [SlotSet("showtime", normalized_input_time)]

            except ValueError:
                pass  # Continue if time parsing fails

        # If no valid time-based input, fall back to numeric choice
        match_numeric = re.search(r"\b(\d+)\b", user_input)
        if match_numeric:
            choice = int(match_numeric.group(1)) - 1  # Convert to zero-based index
            if 0 <= choice < len(normalized_showtimes):
                selected_showtime = normalized_showtimes[choice]
                dispatcher.utter_message(
                    text=f"You have selected {selected_showtime} for {selected_movie}."
                )
                dispatcher.utter_message(
                    text="Please select the location to watch the movie."
                )
                dispatcher.utter_message(response="utter_ask_location")
                return [SlotSet("showtime", selected_showtime)]

        # If no valid input is found, prompt the user again
        dispatcher.utter_message(
            text=f"I didn't understand your choice. Please select a valid number or showtime from the list: {', '.join(showtimes)}."
        )
        return [SlotSet("showtime", None)]

class ActionSetLocation(Action):
    def name(self):
        return "action_set_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Extract the latest user input
        user_input = tracker.latest_message.get("text", "").lower()
        
        # List of possible locations
        locations = ["hong kong", "singapore", "malaysia"]
        
        # Acronym mappings
        acronym_mappings = {
            "hk": "hong kong",
            "sg": "singapore",
            "my": "malaysia"
        }
        
        # Normalize user input using acronyms if present
        for acronym, full_name in acronym_mappings.items():
            if acronym in user_input:
                location = full_name
                break
        else:
            # Search for any location in the user input
            location = next((loc for loc in locations if loc in user_input), None)
        
        if location:
            dispatcher.utter_message(
                text=f"You have selected {location.title()} as the location to watch the movie."
            )
            # Save the location in the slot
            return [SlotSet("location", location)]
        else:
            dispatcher.utter_message(
                text="I couldn't determine the location. Please specify Hong Kong, Singapore, or Malaysia."
            )
            return [SlotSet("location", None)]



class ActionFetchCinemas(Action):
    def name(self):
        return "action_fetch_cinemas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # user_location = next(
            # tracker.get_latest_entity_values("location"), None)
        user_location = tracker.get_slot("location")

        # Cinema mappings
        cinema_mappings = {
            "hong kong": {
                "a": "Golden Harvest G Ocean (Ocean Centre)",
                "b": "The Sky (Olympian City)",
                "c": "StagE (Tuen Mun Town Plaza Phase 1)"
            },
            "singapore": {
                "a": "Golden Mile Tower",
                "b": "Orchard Cinema (Cathay Cineleisure Orchard)"
            },
            "malaysia": {
                "a": "GSC Mid Valley",
                "b": "GSC Pavilion KL",
                "c": "GSC Paradigm Mall"
            }
        }

        # Acronym mappings
        acronym_mappings = {
            "hk": "hong kong",
            "sg": "singapore",
            "my": "malaysia"
        }

        # Check if location is provided
        if not user_location:
            dispatcher.utter_message(
                text="I couldn't detect your location. Could you please tell me where you are?")
            return []

        # Normalize the location input
        location = user_location.lower()
        # Map acronyms to full names
        location = acronym_mappings.get(location, location)

        if location not in cinema_mappings:
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems you tried to say something else.")
            dispatcher.utter_message(
                text="Could you please provide more details or clarify what you meant?")
            dispatcher.utter_message(
                text="I'm here to help with any inquiries about our Athena bot service! 😊")

            return []

        # Fetch cinemas for the user's location
        cinemas = cinema_mappings[location]
        cinema_list = "\n".join(
            [f"{key}: {name}" for key, name in cinemas.items()])

        dispatcher.utter_message(
            text=f"Here are the cinemas available in {location.title()}:\n{cinema_list}\nPlease reply with the letter corresponding to your choice."
        )

        # Save location in the slot
        return [SlotSet("location", location)]


class ActionSetCinema(Action):
    def name(self):
        return "action_set_cinema"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        import re
        # Extract the user input
        user_input = tracker.latest_message.get("text", "").lower().strip()
        user_location = tracker.get_slot("location")

        # Cinema mappings updated to use `a`, `b`, `c`
        cinema_mappings = {
            "hong kong": {
                "a": "Golden Harvest G Ocean (Ocean Centre)",
                "b": "The Sky (Olympian City)",
                "c": "StagE (Tuen Mun Town Plaza Phase 1)"
            },
            "singapore": {
                "a": "Golden Mile Tower",
                "b": "Orchard Cinema (Cathay Cineleisure Orchard)"
            },
            "malaysia": {
                "a": "GSC Mid Valley",
                "b": "GSC Pavilion KL",
                "c": "GSC Paradigm Mall"
            }
        }

        # Validate the user's location
        if not user_location or user_location.lower() not in cinema_mappings:
            dispatcher.utter_message(
                text="I couldn't determine your location. Please provide a valid location."
            )
            return [SlotSet("cinema", None)]

        # Fetch cinemas for the user's location
        location_cinemas = cinema_mappings[user_location.lower()]

        # Match user input to cinema options (a, b, c)
        if user_input in location_cinemas:
            selected_cinema = location_cinemas[user_input]
            dispatcher.utter_message(
                text=f"You have selected {selected_cinema} in {user_location.title()}. Enjoy your time at the cinema!"
            )
            return [SlotSet("cinema", selected_cinema), FollowupAction("action_ask_seats_type")]

        # Search for a cinema name
        for cinema_letter, cinema_name in location_cinemas.items():
            simplified_name = re.sub(r"\s*\(.*?\)", "", cinema_name).strip().lower()  # Remove parentheses and lowercase
            if simplified_name in user_input:
                dispatcher.utter_message(
                    text=f"You have selected {cinema_name} in {user_location.title()}. Enjoy your time at the cinema!"
                )
                return [SlotSet("cinema", cinema_name), FollowupAction("action_ask_seats_type")]

        # If neither a letter nor a cinema name matches
        cinema_list = "\n".join(
            [f"{key.upper()}: {name}" for key, name in location_cinemas.items()]
        )
        dispatcher.utter_message(
            text=f"Sorry, I couldn't understand that. Please reply with the letter corresponding to your choice:\n{cinema_list}"
        )
        return [SlotSet("cinema", None)]


class ActionAskSeatsType(Action):
    def name(self):
        return "action_ask_seats_type"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Retrieve user's location
        user_location = tracker.get_slot("location")

        # Location-based seat pricing with currencies
        seat_prices_by_location = {
            "malaysia": {
                "prices": {"VIP": 50, "Standard": 30, "Couple": 80},
                "currency": "MYR"
            },
            "hong kong": {
                "prices": {"VIP": 150, "Standard": 100, "Couple": 250},
                "currency": "HKD"
            },
            "singapore": {
                "prices": {"VIP": 100, "Standard": 70, "Couple": 200},
                "currency": "SGD"
            }
        }

        # Validate user location
        if not user_location or user_location.lower() not in seat_prices_by_location:
            dispatcher.utter_message(
                text="I couldn't determine your location for pricing. Please confirm your location first."
            )
            return []

        # Get seat prices and currency for the user's location
        location_data = seat_prices_by_location[user_location.lower()]
        location_seat_prices = location_data["prices"]
        currency = location_data["currency"]

        # Constructing the message with prices
        seat_options_with_prices = "\n".join(
            [f"- {seat_type}: {price} {currency}" for seat_type, price in location_seat_prices.items()]
        )

        dispatcher.utter_message(
            text="What type of seats would you like to book? Here are the options:"
        )
        dispatcher.utter_message(text=seat_options_with_prices)

        return []



class ActionSetSeatsType(Action):
    def name(self):
        return "action_set_seats_type"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Get user input
        user_input = tracker.latest_message.get("text", "").lower()
        
        # Match for seat types in the text
        selected_seats_type = None
        if "vip" in user_input:
            selected_seats_type = "vip"
        elif "standard" in user_input:
            selected_seats_type = "standard" 
        elif "couple" in user_input:
            selected_seats_type = "couple"
        
        # Retrieve user's location
        user_location = tracker.get_slot("location")

        # Location-based seat pricing with currencies
        seat_prices_by_location = {
            "malaysia": {
                "prices": {"vip": 50, "standard": 30, "couple": 80},
                "currency": "MYR"
            },
            "hong kong": {
                "prices": {"vip": 150, "standard": 100, "couple": 250},
                "currency": "HKD"
            },
            "singapore": {
                "prices": {"vip": 100, "standard": 70, "couple": 200},
                "currency": "SGD"
            }
        }

        # Validate user location
        if not user_location or user_location.lower() not in seat_prices_by_location:
            dispatcher.utter_message(
                text="I couldn't determine your location for pricing. Please confirm your location first."
            )
            return [SlotSet("seat_type", None)]

        # Get seat prices and currency for the user's location
        location_data = seat_prices_by_location[user_location.lower()]
        location_seat_prices = location_data["prices"]
        currency = location_data["currency"]

        valid_seat_types = location_seat_prices.keys()

        # Validate seat type
        if selected_seats_type and selected_seats_type.lower() in valid_seat_types:
            price = location_seat_prices[selected_seats_type.lower()]
            dispatcher.utter_message(
                text=f"You have selected the {selected_seats_type.capitalize()} section in {user_location.title()}. The price per seat is {price} {currency}."
            )
            return [SlotSet("seat_type", selected_seats_type), FollowupAction("action_ask_number_of_seats")]
        else:
            # Handle invalid or unrecognized seat type
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems you tried to say something else.")
            dispatcher.utter_message(
                text="Please specify the type of seats you want (VIP, Standard, Couple).")
            return [UserUtteranceReverted()]

        return []


class ActionAskNumberOfSeats(Action):
    def name(self):
        return "action_ask_number_of_seats"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="How many seats would you like to reserve?")
        return []


class ActionSetNumberOfSeats(Action):
    def name(self):
        return "action_set_number_of_seats"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Fetch the latest user message
        user_message = tracker.latest_message.get("text", "")
        
        # Search for a number in the text
        match = re.search(r'\b\d+\b', user_message)
        number_of_seats = int(match.group()) if match else None

        if number_of_seats and 1 <= number_of_seats <= 10:  # Assuming a max of 10 seats can be reserved.
            if number_of_seats == 1:
                dispatcher.utter_message(
                    text=f"You have selected {number_of_seats} seat. Please select the seat number."
                )
            else:
                dispatcher.utter_message(
                    text=f"You have selected {number_of_seats} seats. Please select the seat numbers."
                )
            
            # Seating plan image URL
            image_url = "https://www.edrawsoft.com/templates/images/cinema-seating-plan.png"
            dispatcher.utter_message(image=image_url)
            
            return [SlotSet("number_of_seats", number_of_seats), FollowupAction("action_ask_seat_numbers")]
        elif number_of_seats:  # Number is outside valid range
            dispatcher.utter_message(text="Please specify a valid number of seats (1-10).")
            return [UserUtteranceReverted()]
        else:  # No valid number found
            dispatcher.utter_message(text="I didn't understand that. Could you please specify the number of seats?")
            return [UserUtteranceReverted()]


class ActionAskSeatNumbers(Action):
    def name(self):
        return "action_ask_seat_numbers"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        number_of_seats = tracker.get_slot("number_of_seats")

        if number_of_seats:
            if number_of_seats == 1:
                dispatcher.utter_message(
                    text=f"Please provide the seat number for the seat you want to reserve. eg A1 or D12")
            else:
                dispatcher.utter_message(
                    text=f"Please provide the seat numbers for the {number_of_seats} seats you want to reserve. eg A1, B2, C3")
        else:
            dispatcher.utter_message(text="Please specify the number of seats first.")

        return []


class ActionSetSeatNumbers(Action):
    def name(self):
        return "action_set_seat_numbers"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Extract the latest user message
        user_message = tracker.latest_message.get("text", "")
        number_of_seats = tracker.get_slot("number_of_seats")

        # Try extracting seat numbers in the format (e.g., A1, B2, C10)
        seat_numbers = re.findall(r"[A-Z]\d+", user_message)

        # If no seat format is found, fallback to extracting plain numbers
        if not seat_numbers:
            seat_numbers = re.findall(r"\d+", user_message)

        if seat_numbers:
            # Check if the number of seats matches the slot value
            if number_of_seats and len(seat_numbers) == int(number_of_seats):
                if len(seat_numbers) == 1:
                    dispatcher.utter_message(
                        text=f"You have selected the seat: {seat_numbers[0]}. Confirming your reservation now!"
                    )
                else:
                    dispatcher.utter_message(
                        text=f"You have selected the following seats: {', '.join(seat_numbers)}. Confirming your reservation now!"
                    )
                return [SlotSet("seat_numbers", seat_numbers)]
            else:
                dispatcher.utter_message(
                    text=f"You mentioned {number_of_seats} seats but provided {len(seat_numbers)} seat numbers. Please try again."
                )
                return [UserUtteranceReverted()]
        else:
            dispatcher.utter_message(text="I didn't catch the seat numbers. Could you please repeat?")
            return [UserUtteranceReverted()]




class ActionAskConfirmation(Action):
    def name(self):
        return "action_ask_confirmation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        messages = [
            "Please confirm your booking by replying with 'Confirm' or 'Cancel'.",
            "Are you sure you want to proceed with the booking?",
            "Please confirm your booking details."
        ]

        for message in messages:
            dispatcher.utter_message(text=message)

        return []
    
class ActionSetConfirmation(Action):
    def name(self):
        return "action_set_confirmation"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        confirmation = tracker.latest_message.get("text", "").lower()

        if "confirm" in confirmation:
            dispatcher.utter_message(text="Your booking is confirmed!")
            return [SlotSet("decide", "confirm"), FollowupAction("action_ask_payment_option")]
        elif "cancel" in confirmation:
            dispatcher.utter_message(text="Your booking has been canceled. Feel free to ask if you need anything else!")
        else:
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(text="Please confirm your booking by replying with 'Confirm' or 'Cancel'.")

        return []


class ActionConfirmBooking(Action):
    def name(self):
        return "action_confirm_booking"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Fetching all the slots
        selected_cinema = tracker.get_slot("cinema")
        selected_movie = tracker.get_slot("movie")
        selected_seats = tracker.get_slot("seat_number")
        selected_seats_type = tracker.get_slot("seat_type")

        confirmation = tracker.latest_message.get("text", "").lower()

        # If all required slots are filled, ask for confirmation
        if selected_movie and selected_cinema and selected_seats and selected_seats_type:
            if "confirm" in confirmation:
                # If user confirmed the booking, proceed with confirmation message
                dispatcher.utter_message(
                    text=f"Your booking is confirmed!\nMovie: {selected_movie}\nCinema: {selected_cinema}\nSeats: {selected_seats} ({selected_seats_type})."
                )
                return [FollowupAction("action_ask_payment_option")]
            elif "cancel" in confirmation:
                # If user canceled, provide a cancellation message
                dispatcher.utter_message(
                    text="Your booking has been canceled. Feel free to ask if you need anything else!")
            else:
                # If user's confirmation intent is unclear, ask for confirmation again
                dispatcher.utter_message(
                    text="Sorry, I didn't understand that.")
                dispatcher.utter_message(
                    text="Please confirm your booking by replying with 'Confirm' or 'Cancel'.")
        else:
            # If booking details are incomplete, ask user to retry
            dispatcher.utter_message(
                text="Sorry, some booking details are missing. Please try again.")

        return []


class DetectPaymentOption(Action):
    def name(self):
        return "action_detect_payment_option"
    
    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message.get("text", "").lower()
        if "credit" in text or "card" in text or "online" in text:
            return [FollowupAction("tell_online_payment")]
        elif "cash" in text or "offline" in text:
            return [FollowupAction("tell_offline_payment")]
        else:
            dispatcher.utter_message("Sorry, I didn't understand that.")
            dispatcher.utter_message("Please select a valid payment option.")
            return [UserUtteranceReverted()]
        
class TellOnlinePayment(Action):
    def name(self):
        return "action_tell_online_payment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        messages = [
            "These are the different options of online payment.",
            "Master, Visa, Paypal.",
            "We also have debit or credit card payment options."
        ]
        return []
    
class TellOfflinePayment(Action):
    def name(self):
        return "action_tell_offline_payment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        messages = [
            "These are the different options of offline payment.",
            "Cash"
        ]
        return []


class ActionAskPaymentOptions(Action):
    def name(self):
        return "action_ask_payment_option"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        messages = [
            "Now that you have confirmed your ticket.",
            "Let us get started on the payment process.",
            "Please decide between the different options of payment.",
            "The payment options we provide are:",
            "Master, Visa, Paypal.",
            "We also have debit or credit card payment options."
        ]
        for message in messages:
            dispatcher.utter_message(text=message)

        return []

class ActionSetPaymentOption(Action):
    def name(self) -> Text:
        return "action_set_payment_option"

    def __init__(self):
        self.payment_options_map = {
            "credit card": ["credit", "credit card", "creditcard"],
            "debit card": ["debit", "debit card", "debitcard"],
            "paypal": ["paypal", "pay pal", "pp"],
            "apple pay": ["apple", "apple pay", "applepay"],
            "mastercard": ["master", "mastercard", "master card"],
            "visa": ["visa", "visa card"],
            "cash": ["cash", "offline", "in person", "physical"]
        }
        # Pre-compute flattened keyword mapping for efficiency
        self.keyword_mapping = {
            keyword.strip(): option 
            for option, keywords in self.payment_options_map.items() 
            for keyword in keywords
        }

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        try:
            # Get and clean user input
            user_input = (tracker.latest_message.get("text", "") or "").lower()
            
            if not user_input:
                return self._handle_empty_input(dispatcher)

            # Find matching payment option
            payment_option = self._match_payment_option(user_input)

            if payment_option:
                return self._handle_valid_payment(dispatcher, payment_option)
            else:
                return self._handle_invalid_payment(dispatcher)

        except Exception as e:
            # Log the error in your preferred way
            print(f"Error processing payment option: {str(e)}")
            return self._handle_error(dispatcher)

    def _match_payment_option(self, user_input: Text) -> Text:
        """Match user input against valid payment options."""
        # Split user input into words
        input_words = user_input.split()
        
        # Try exact match with complete input first
        if user_input in self.keyword_mapping:
            return self.keyword_mapping[user_input]
        
        # Try matching individual words
        for word in input_words:
            if word in self.keyword_mapping:
                return self.keyword_mapping[word]
                
        # Try partial matches as a last resort
        for keyword, option in self.keyword_mapping.items():
            if keyword in user_input or any(word in keyword for word in input_words):
                return option
        
        return None

    def _handle_valid_payment(
        self,
        dispatcher: CollectingDispatcher,
        payment_option: Text
    ) -> List[Dict[Text, Any]]:
        """Handle successful payment option selection."""
        dispatcher.utter_message(
            text=f"Perfect! You've selected {payment_option.capitalize()} as your payment option."
        )
        dispatcher.utter_message(response="utter_payment_link")
        
        return [
            SlotSet("payment_option", payment_option),
            FollowupAction("action_booking_confirmed")
        ]

    def _handle_invalid_payment(
        self,
        dispatcher: CollectingDispatcher
    ) -> List[Dict[Text, Any]]:
        """Handle unrecognized payment options."""
        valid_options = ", ".join(sorted(set(self.payment_options_map.keys())))
        dispatcher.utter_message(
            text="I couldn't recognize the payment option you mentioned."
        )
        dispatcher.utter_message(
            text=f"Please select from these available options: {valid_options}."
        )
        return [UserUtteranceReverted()]

    def _handle_empty_input(
        self,
        dispatcher: CollectingDispatcher
    ) -> List[Dict[Text, Any]]:
        """Handle empty or invalid user input."""
        dispatcher.utter_message(
            text="I didn't receive any payment option selection. Please specify how you'd like to pay."
        )
        return [UserUtteranceReverted()]

    def _handle_error(
        self,
        dispatcher: CollectingDispatcher
    ) -> List[Dict[Text, Any]]:
        """Handle unexpected errors during processing."""
        dispatcher.utter_message(
            text="I encountered an issue while processing your payment option. Please try again."
        )
        return [UserUtteranceReverted()]
    
    
class ActionBookingConfirmed(Action):
    def name(self):
        return "action_booking_confirmed"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        dispatcher.utter_message(
            text="Your booking has been confirmed. Enjoy the movie!")
        return []
