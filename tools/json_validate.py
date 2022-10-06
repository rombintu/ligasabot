import json

def validate(json_content):
    data = json.loads(json_content)
    content = []
    if type(data) != list:
        content = [data]
    else:
        content = data
    for ct in content:
        keys = ct.keys()
        vict = "ask" and "vars" and "ans" in keys
        study = "content" and "url" and "title" in keys 
    return study, vict