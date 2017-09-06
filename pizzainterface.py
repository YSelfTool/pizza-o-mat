import regex as re
import json
from fuzzywuzzy import fuzz
import requests

DATA_START_MARKER = "__initialState__ = "
WORD_PATTERN = r"(?:mit)?(?<ingredient>[[:alnum:]\-\s,]+?)(?:(?<![0-9]),(?![0-9])|mit|und|$| - )"
WORD_REGEX = re.compile(WORD_PATTERN)

NOT_INCLUDED = "{} ist ohne {}."
INCLUDED = "{} ist mit {}."
INGREDIENT_DESCRIPTION = "Würdest du {} auf deiner Pizza mögen?"

RESTAURANTS_URL = "https://pizza.de/lieferservice/{}/{}/"
RESTAURANT_URL = "https://pizza.de/lieferservice/aachen/restaurant-{}/{}/"

def extract_data_content(content):
    data_start = content.index(DATA_START_MARKER) + len(DATA_START_MARKER)
    raw_data_str = content[data_start:]
    counter = 0
    result = []
    for char in raw_data_str:
        if char == "{":
            counter += 1
        elif char == "}":
            counter -= 1
        result.append(char)
        if counter == 0:
            break
    result_str = "".join(result)
    data = json.loads(result_str)
    return data

class Ingredient:
    def __init__(self, fullname):
        self.fullname = fullname
        self.name = self.extract_significant_word()

    def extract_significant_word(self):
        words = list(filter(None, map(str.strip, self.fullname.split(" "))))
        if len(words) < 0:
            raise Exception("Empty ingredient")
        elif len(words) == 1:
            return words[0]
        candidates = [word for word in words if word[0].isupper()]
        if len(candidates) == 0:
            return sorted(words, key=len)[-1] # längstes
        elif len(candidates) == 1:
            return candidates[0]
        else:
            return sorted(candidates, key=len)[-1]

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{} -> {}".format(self.fullname, self.name)

class Food:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.ingredients = self.split_description()

    def split_description(self):
        components = []
        for match in WORD_REGEX.finditer(self.description):
            ingredient_str = match.group("ingredient").strip()
            if len(ingredient_str) == 0:
                continue
            ingredient = Ingredient(ingredient_str)
            components.append(ingredient)
        return components

    def categorize(self, categories, ingredient_name_map):
        normalized_ingredients = {ingredient_name_map[ingredient.name]: ingredient.fullname for ingredient in self.ingredients}
        return { category:
            (True, INCLUDED.format(self.name, normalized_ingredients[category]))
            if category in normalized_ingredients
            else (False, NOT_INCLUDED.format(self.name, category))
            for category in categories
        }

    def jsonify(self):
        return {"shortName": self.name, "longName": "{} {}".format(self.name, self.description), "description": ""}

    @staticmethod
    def from_dict(item):
        return Food(item["name"], item["description"])

    def __str__(self):
        return " -> ".join([self.name, self.description, str(self.ingredients)])

    def __repr__(self):
        return str(self)

class Restaurant:
    def __init__(self, name, id, uri):
        self.name = name
        self.id = id
        self.uri = uri

    @staticmethod
    def from_dict(item):
        name = item["name"]
        id = item["id"]
        uri = RESTAURANT_URL.format(item["slug"], item["id"])
        return Restaurant(name, id, uri)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{} -> {}".format(self.name, self.uri)

def extract_pizza(data):
    menu = data["restaurant"]["info"]["menu"]
    known_names = set([])
    food_dict = {}
    for section in menu["sections"]:
        for item in section["items"]:
            name = item["name"]
            if "Pizza " in name:
                food = Food.from_dict(item)
                if name not in known_names or len(food.ingredients) > len(food_dict[name].ingredients):
                    known_names.add(name)
                    food_dict[name] = food
    return [food_dict[name] for name in sorted(known_names)]

def summarize_ingredients(ingredient_names):
    name_map = {}
    for name in ingredient_names:
        best_match = name
        for other in name_map:
            score = fuzz.partial_ratio(name, other)
            if score > 80: # arbitrarily choosen based on test-data
                best_match = other
        name_map[name] = best_match
    return name_map

def jsonify_data(pizzas, categories, ingredient_name_map):
    parties = [pizza.jsonify() for pizza in pizzas]
    answers = {pizza: pizza.categorize(categories, ingredient_name_map) for pizza in pizzas}
    questions = [
        {
            "title": category,
            "description": INGREDIENT_DESCRIPTION.format(category),
            "statements": {
                pizza.name: [
                    "+" if answers[pizza][category][0] else "-",
                    answers[pizza][category][1]
                ]
                for pizza in pizzas
            }
        }
        for category in categories
    ]
    return {
        "parties": parties,
        "questions": questions
    }

def generate_pizza_data(restaurant):
    page_content = requests.get(restaurant.uri).text
    data = extract_data_content(page_content)
    menu = data["restaurant"]["info"]["menu"]
    import pprint
    pp = pprint.PrettyPrinter(indent=2)
    pizzas = extract_pizza(data)
    known_ingredients = set([ingredient.name for pizza in pizzas for ingredient in pizza.ingredients])
    ingredient_name_map = summarize_ingredients(known_ingredients)
    categories = sorted(set(ingredient_name_map.values()))
    result = jsonify_data(pizzas, categories, ingredient_name_map)
    return json.dumps(result)

def extract_restaurants(town, plz):
    if not town.isalpha() or not plz.isnumeric() or len(plz) != 5:
        raise Exception("Invalid input values to get the URL")
    url = RESTAURANTS_URL.format(town.lower(), plz)
    content = requests.get(url).text
    data = extract_data_content(content)
    restaurants = []
    for restaurant_data in data["restaurants"]["list"]:
        if "pizza-pasta" not in restaurant_data["cuisines"] or restaurant_data["status"] != "open":
            continue
        restaurants.append(Restaurant.from_dict(restaurant_data))
    return restaurants

def validate_location(town, plz):
    plz = str(plz)
    if not town.isalpha() or not plz.isnumeric() or len(plz) > 5:
        return False
    url = RESTAURANTS_URL.format(town, str(plz))
    result = requests.get(url)
    return result.status_code == 200


if __name__ == "__main__":
    restaurants = extract_restaurants("aachen", "52062")
    print(generate_pizza_data(restaurants[0]))
