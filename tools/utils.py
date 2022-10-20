from fileinput import filename
import json

file_name = "utils.json"


def write_day(day):
    with open(file_name, "w") as jsf:
        json.dump({"day": day}, jsf)

def read_day(default):
    try:
        with open(file_name, "r") as jsf:
            return json.loads(jsf.read())["day"]
    except:
        return default