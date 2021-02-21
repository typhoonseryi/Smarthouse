from __future__ import absolute_import, unicode_literals
import requests
import json
from celery import task
from django.conf import settings
from django.core.mail import send_mail
from .models import Setting


def handle_controllers(controllers):
    set1, _ = Setting.objects.get_or_create(
        controller_name='bedroom_target_temperature',
        defaults={
            'label': 'Желаемая температура в спальне',
            'value': 80
        }
    )
    BEDROOM_TARGET_TEMPERATURE = set1.value
    set2, _ = Setting.objects.get_or_create(
        controller_name='hot_water_target_temperature',
        defaults={
            'label': 'Желаемая температура горячей воды',
            'value': 21
        }
    )
    HOT_WATER_TARGET_TEMPERATURE = set2.value

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
        send_mail(
            'Leak_detector',
            'Leak error occured',
            settings.EMAIL_HOST,
            [settings.EMAIL_RECEPIENT],
        )
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


@task()
def smart_home_manager():
    url = settings.SMART_HOME_API_URL
    token = settings.SMART_HOME_ACCESS_TOKEN
    headers = {
        'Authorization': 'Bearer ' + token,
    }
    resp_get = requests.get(url=url, headers=headers)
    data_get = resp_get.json()['data']
    controllers = {d['name']: d['value'] for d in data_get}
    new_controllers = handle_controllers(controllers)
    if bool(new_controllers):
        new_list = [{'name': c[0], 'value': c[1]} for c in new_controllers.items()]
        dict_post = {}
        dict_post['controllers'] = new_list
        data_post = json.dumps(dict_post)
        response = requests.post(url=url, data=data_post, headers=headers)
        #print(response.json()['status'])
