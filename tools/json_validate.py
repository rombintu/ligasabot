import json

def validate_vict(data):
    valid = False
    try:
        print(data["ask"])
        print(data["vars"])
        print(data["ans"])
        valid = True
    except Exception as e:
        print(e)
    return valid

def validate_study(data):
    valid = False
    try:
        print(data["content"])
        print(data["url"])
        valid = True
    except Exception as e:
        print(e)
    return valid

def validate(json_content):
    data = {}
    vict = False
    study = False
    try:
        data = json.loads(json_content)
        if validate_vict(data):
            vict = True
        elif validate_study(data):
            study = True
    except Exception as e:
        print(e)
    return study, vict

def read_json_file(vict):
    if vict:
        with open("variants.json", "r") as jsf:
            return json.loads(jsf.read())
    else:
        with open("study.json", "r") as jsf:
            return json.loads(jsf.read())

def json_concat_vict(json_content):
    content = []
    old_js = []
    try:
        old_js = read_json_file(vict=True)
    except Exception as e:
        print(e)

    js_content = json.loads(json_content.decode("utf-8"))
    if type(js_content) == list:
        content = old_js + js_content
    elif type(js_content) == dict:
        content = old_js + [js_content] 
    with open("variants.json", "w") as new_js:
        new_js.write(json.dumps(content, indent=4))

def json_concat_study(json_content):
    content = []
    old_js = []
    try:
        old_js = read_json_file(vict=False)
    except Exception as e:
        print(e)

    js_content = json.loads(json_content.decode("utf-8"))
    if type(js_content) == list:
        content = old_js + js_content
    elif type(js_content) == dict:
        content = old_js + [js_content] 
    with open("study.json", "w") as new_js:
        new_js.write(json.dumps(content, indent=4))