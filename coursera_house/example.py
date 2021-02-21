import json
import requests
from django.conf import settings

HOT_WATER_TARGET_TEMPERATURE, BEDROOM_TARGET_TEMPERATURE = 24, 76

def handle_controllers(controllers):
    new_controllers = {}
    leak_error, cold_water_warn, smoke_error = False, False, False
    if controllers.get('leak_detector'):
        if controllers.get('cold_water'):
            new_controllers['cold_water'] = False
        if controllers.get('hot_water'):
            new_controllers['hot_water'] = False
        if controllers.get('boiler'):
            new_controllers['boiler'] = False
        if controllers.get('washing_machine') == 'on':
            new_controllers['washing_machine'] = 'off'
        leak_error = True
    if controllers.get('smoke_detector'):
        if controllers.get('air_conditioner'):
            new_controllers['air_conditioner'] = False
        if controllers.get('bedroom_light'):
            new_controllers['bedroom_light'] = False
        if controllers.get('bathroom_light'):
            new_controllers['bathroom_light'] = False
        if controllers.get('boiler'):
            new_controllers['boiler'] = False
        if controllers.get('washing_machine') == 'on':
            new_controllers['washing_machine'] = 'off'
        smoke_error = True
    if not controllers.get('cold_water'):
        if controllers.get('boiler'):
            new_controllers['boiler'] = False
        if controllers.get('washing_machine') == 'on':
            new_controllers['washing_machine'] = 'off'
        cold_water_warn = True
    if not (cold_water_warn or smoke_error or leak_error):
        if controllers.get('boiler_temperature') < 0.9 * HOT_WATER_TARGET_TEMPERATURE:
            if not (controllers.get('boiler')):
                new_controllers['boiler'] = True
        if controllers.get('boiler_temperature') > 1.1 * HOT_WATER_TARGET_TEMPERATURE:
            if controllers.get('boiler'):
                new_controllers['boiler'] = False
    if not (controllers.get('curtains') == 'slightly_open'):
        if (controllers.get('outdoor_light') < 50) and (not controllers.get('bedroom_light')):
            if not (controllers.get('curtains') == 'open'):
                new_controllers['curtains'] = 'open'
        if (controllers.get('outdoor_light') > 50) or (controllers.get('bedroom_light')):
            if not (controllers.get('curtains') == 'close'):
                new_controllers['curtains'] = 'close'
    if not smoke_error:
        if controllers.get('bedroom_temperature') > 1.1 * BEDROOM_TARGET_TEMPERATURE:
            if not (controllers.get('air_conditioner')):
                new_controllers['air_conditioner'] = True
        if controllers.get('bedroom_temperature') < 0.9 * BEDROOM_TARGET_TEMPERATURE:
            if controllers.get('air_conditioner'):
                new_controllers['air_conditioner'] = False
    return new_controllers

url = 'https://smarthome.webpython.graders.eldf.ru/api/user.controller'
token = 'd3c763687602b8916319c1ac5ca4d259bb7384aa488f9fa9ccbc2fcf93925e32'
headers = {
    'Authorization': 'Bearer ' + token,
}
resp_get = requests.get(url=url, headers=headers)
data_get = resp_get.json()['data']
controllers = {d['name']: d['value'] for d in data_get}
print(controllers)
new_controllers = handle_controllers(controllers)
if bool(new_controllers):
    new_list = [{'name': c[0], 'value': c[1]} for c in new_controllers.items()]
    dict_post = {}
    dict_post['controllers'] = new_list
    data_post = json.dumps(dict_post)
    response = requests.post(url=url, data=data_post, headers=headers)
    print(new_controllers)

