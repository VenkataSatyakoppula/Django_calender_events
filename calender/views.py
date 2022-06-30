from django import views
from django.forms import ValidationError
from dotenv import load_dotenv
from django.shortcuts import render
from rest_framework import status, serializers
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import redirect
import requests
import google_auth_oauthlib.flow
import os

load_dotenv()

#Endpoints to make API requests
GOOGLE_ACCESS_TOKEN_OBTAIN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_CALENDER_API_ENDPOINT = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'


#Code to get the access token from google
def google_get_access_token(*, code: str, redirect_uri: str) -> str:
    # Reference: https://developers.google.com/identity/protocols/oauth2/web-server#obtainingaccesstokens
    data = {
        'code': code,
        'client_id': os.getenv('DJANGO_GOOGLE_OAUTH2_CLIENT_ID'),
        'client_secret': os.getenv('DJANGO_GOOGLE_OAUTH2_CLIENT_SECRET'),
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    print(data)
    response = requests.post(GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)

    if not response.ok:
        raise ValidationError('Failed to obtain access token from Google.')

    access_token = response.json()['access_token']

    return access_token

#prompt user for his/her credentials
class  GoogleCalendarInitView(views.View):
    def get(self,request,*args,**kwargs):
        #Refernece: https://developers.google.com/identity/protocols/oauth2/web-server
        
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        settings.BASE_DIR/'client_secret.json',
        scopes=['https://www.googleapis.com/auth/calendar'])

        #googleAuthurl = 'https://accounts.google.com/o/oauth2/v2/auth'
        flow.redirect_uri  = 'http://localhost:8000/rest/v1/calendar/redirect/'
        authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
        return redirect(authorization_url)

#Get's the code and get access token using the code and get list of calender events
class GoogleCalendarRedirectView(APIView):
    class InputSerializer(serializers.Serializer):
        #serilizers for code and errors
        code = serializers.CharField(required=False)
        error = serializers.CharField(required=False)
    def get(self, request, *args, **kwargs):
        input_serializer = self.InputSerializer(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        code = validated_data.get('code')
        error = validated_data.get('error')

        domain = 'http://localhost:8000'
        api_uri = '/rest/v1/calendar/redirect/'
        redirect_uri = f'{domain}{api_uri}'

        try:
            #get access token from the session
            access_token = request.session['token']
        except KeyError:
            access_token = google_get_access_token(code=code, redirect_uri=redirect_uri)
            request.session['token'] = access_token

        response = requests.get(
        GOOGLE_CALENDER_API_ENDPOINT,
        params={'access_token': access_token}
        )
        #if token expires it raises an error
        if not response.ok:
            raise ValidationError('Failed to obtain calender info from Google.')
        #Calender events data
        data = response.json()    
        return render(request,'calender_view.html',{'data':data})

class index(views.View):
    def get(self, request, *args, **kwargs):
        return render(request,'index.html')

#Revokes the token access
class revoke(views.View):
    def get(self,request,*args,**kwargs):
        print(request.session['token'])
        requests.post('https://oauth2.googleapis.com/revoke',
        params={'token': request.session['token']},
        headers = {'content-type': 'application/x-www-form-urlencoded'})
        del request.session['token']
        return render(request,'revoke.html')