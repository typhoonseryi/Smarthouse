import json
import requests
from django.conf import settings
from django.forms import ModelForm
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import FormView
from .models import Setting
from .form import ControllerForm
from requests import exceptions as exc


class ControllerView(FormView):
    form_class = ControllerForm
    template_name = 'core/control.html'
    success_url = reverse_lazy('form')

    url = settings.SMART_HOME_API_URL
    token = settings.SMART_HOME_ACCESS_TOKEN
    headers = {
        'Authorization': 'Bearer ' + token,
    }

    def get_controllers(self):
        try:
            resp_get = requests.get(url=self.url, headers=self.headers)
            data_get = resp_get.json()['data']
            controllers = {d['name']: d['value'] for d in data_get}
            return controllers
        except (json.decoder.JSONDecodeError, exc.ConnectionError, exc.HTTPError, exc.Timeout):
            return {}

    def post_controllers(self, **kwargs):
        new_list = [{'name': key, 'value': value} for key, value in kwargs.items()]
        dict_post = {}
        dict_post['controllers'] = new_list
        data_post = json.dumps(dict_post)
        try:
            requests.post(url=self.url, data=data_post, headers=self.headers)
        except (exc.ConnectionError, exc.HTTPError, exc.Timeout):
            return '502'

    def __init__(self, **kwargs):
        super(ControllerView, self).__init__(**kwargs)
        self.controllers = self.get_controllers()

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        if not bool(self.controllers):
            return HttpResponse('Bad Gateway', status=502)
        else:
            return super(ControllerView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ControllerView, self).get_context_data()
        context['data'] = self.controllers
        return context

    def get_initial(self):
        set1, _ = Setting.objects.get_or_create(
            controller_name='bedroom_target_temperature',
            defaults={
                'label': 'Желаемая температура в спальне',
                'value': 80
            }
        )
        set2, _ = Setting.objects.get_or_create(
            controller_name='hot_water_target_temperature',
            defaults={
                'label': 'Желаемая температура горячей воды',
                'value': 21
            }
        )
        return {
            'bedroom_target_temperature': set1.value,
            'hot_water_target_temperature': set2.value,
            'bedroom_light': self.controllers.get('bedroom_light'),
            'bathroom_light': self.controllers.get('bathroom_light'),
        }

    def form_valid(self, form):
        Setting.objects.update_or_create(
            controller_name='bedroom_target_temperature',
            label='Желаемая температура в спальне',
            defaults={
                'value': form.cleaned_data['bedroom_target_temperature'],
            }
        )
        Setting.objects.update_or_create(
            controller_name='hot_water_target_temperature',
            label='Желаемая температура горячей воды',
            defaults={
                'value': form.cleaned_data['hot_water_target_temperature'],
            }
        )
        resp = self.post_controllers(
            bedroom_light=form.cleaned_data['bedroom_light'],
            bathroom_light=form.cleaned_data['bathroom_light'],
        )
        if resp == '502':
            return HttpResponse('Bad Gateway', status=502)
        return super(ControllerView, self).form_valid(form)