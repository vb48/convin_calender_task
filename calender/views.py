from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.discovery import build

# to avoid https invalid error add this line
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# path to client credentials for OAuth2.0
OAuth_Client_Creds = os.path.abspath(os.getcwd()) + "\calender\client_credentials.json"
 
# the scopes which we want to use, in this case google calender
scopes = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']

# handle redirects from this url
REDIRECT_URL = 'http://127.0.0.1:8000/rest/v1/calendar/redirect/'

# Create your views here.
@api_view(['GET'])
def init(request):
    # persn = {'name':'Vaibhav'}
    # return Response(persn)

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            OAuth_Client_Creds, scopes=scopes)
    
    flow.redirect_uri = REDIRECT_URL

    # helps refresh an access token without asking the user for permission again
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    
    # the 'state' here stores the auth state once granted persmission
    request.session['state'] = state

    # return the auth url to the user to allow auth on their account
    return Response({"authorization_url": authorization_url})
    

@api_view(['GET'])
def redirect(request):
    # persn = {'name':'Vaibhav'}
    # return Response(persn)
    
    state = request.session['state']
    
    # print(state)

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        OAuth_Client_Creds, scopes=scopes, state=state)
    flow.redirect_uri = REDIRECT_URL

    authorization_response = request.get_full_path()
    flow.fetch_token(authorization_response=authorization_response)


    # Save credentials back to session in case access token was refreshed.
    credentials = flow.credentials

    # create a dict from creds
    credentials_dict = {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}
    
    # print(credentials_dict)
    
    # pass the creds dict to session to indicate that these are the creds for this particular session 
    request.session['credentials'] = credentials_dict


    # if creds are not in the session then redirect the user
    if 'credentials' not in request.session:
        return redirect('v1/calendar/init')

    # Else load creds from the session
    credentials = google.oauth2.credentials.Credentials(
        **request.session['credentials']) # unpack the **kwargs
    
    # Now we can get the events from the calenders
    service = googleapiclient.discovery.build(
        'calendar', 'v3', credentials=credentials)

    # Returns the calendars on the user's calendar list
    calendar_list = service.calendarList().list().execute()

    # Getting user ID i.e., email address
    calendar_id = calendar_list['items'][0]['id']

    # Getting all events associated with a user ID (email address)
    events  = service.events().list(calendarId=calendar_id).execute()

    events_list_append = [] 
    if not events['items']:
        print('No data found.')
        return Response({"message": "No data found or user credentials invalid."})
    else:
        for events_list in events['items']:
            events_list_append.append(events_list)
            return Response({"events": events_list_append})
    return Response({"error": "calendar event aren't here"})