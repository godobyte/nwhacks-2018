"""
Alexa app herddit
@nwHacks2018
"""

from __future__ import print_function
import httplib, urllib, base64, json, sys


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------
# AMAZON.HelpIntent
def get_welcome_response():
    """ initialize the session
    """
    print("in handle_session_end_request")
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to herd it. " \
                    "Please pick a sub reddit " \
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please choose a subreddit by saying, " \
                    "for example UBC."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# AMAZON.HelpIntent - EndSession
def handle_session_end_request():
    print("in handle_session_end_request")
    card_title = "Session Ended"
    speech_output = "Thank you for using herd it. " \
                    "Now you have herd it! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def create_favorite_subreddit_attributes(favorite_subreddit):
    return {"favoriteSubreddit": favorite_subreddit}

# MySubredIntent
def set_subred_in_session(intent, session):
    """ Subreddit picked by user
    """
    print("in set_subred_in_session")
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'Subreddit' in intent['slots']:
        favorite_subreddit = intent['slots']['Subreddit']['value']
        session_attributes = create_favorite_subreddit_attributes(favorite_subreddit)
        speech_output = "The subreddit you picked is " + \
                        favorite_subreddit + \
                        ". You can ask me to read this subreddit by saying, " \
                        "read."
        reprompt_text = "You can ask me to read this subreddit by saying, " \
                        "read."
    else:
        speech_output = "I'm not sure what your chosen subreddit is. " \
                        "Please try again."
        reprompt_text = "Sorry, I'm not sure what your chosen subreddit is. " \
                        "You can pick a subreddit by saying, " \
                        "for example UBC."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# ReadSubredIntent
def get_subreddit_from_session(intent, session):
    print("in get_subreddit_from_session")
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favoriteSubreddit" in session.get('attributes', {}):
        favorite_subreddit = session['attributes']['favoriteSubreddit']

        # construct and read reddit
        speech_output = get_reddit_posts(favorite_subreddit) + ". If you want to switch to another sub reddit, please say switch with your chosen subreddit"
        should_end_session = False
    else:
        speech_output = "I'm not sure what your chosen subreddit is. " \
                        "You can pick a subreddit by saying, " \
                        "for example UBC."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# StopIntent, this is not working yet
def on_session_stopped(session_ended_request, session):
    print("in on_session_stopped")
    card_title = "Session Stopped"
    speech_output = "Thank you for using herd it. " \
                    "Now you have herd it! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# --------------- Functions helpers for reddit post reading ------------------
def get_reddit_posts(subreddit):
    numberofposts = 2
    url = "https://www.reddit.com/r/%s.json" % subreddit
    print(url)
    speech = "";
    data = {}

    # Keep Trying until data is received
    while 'data' not in data:
      data = json.loads(urllib.urlopen(url).read())
      print ("loading")

    read_posts = 0;
    index = 0;

    while read_posts < numberofposts:
      # Skip Stickied Posts
      if not data['data']['children'][index]['data']['stickied']:
        # Get Title
        print(data['data']['children'][index]['data']['title'])
        pos = " \\ Post number %s \\  " % str(index+1)
        speech += pos + str(data['data']['children'][index]['data']['title'])
        # Check if the post is a link or a text post
        if data['data']['children'][index]['data']['selftext_html'] is None:
          # Check if there is an image
          if 'preview' in data['data']['children'][index]['data']:
            # Image Handling
            image_url = data['data']['children'][index]['data']['preview']['images'][0]['source']['url']
            description = str(get_image_description(image_url))
            speech += " \\ The post contains an image of, \\ " + description
        else:
          #  Self Text added to speech
          print(data['data']['children'][index]['data']['selftext'])
          speech += " \\ Content, " + str(data['data']['children'][index]['data']['selftext'])

        read_posts = read_posts + 1
      index = index + 1

    print(speech)
    return speech

def get_image_description(url):
    print("querying Microsoft Vision API: " + url)

    subscription_key = '***********'
    uri_base = 'westcentralus.api.cognitive.microsoft.com'

    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    params = urllib.urlencode({
        'visualFeatures': 'Categories,Description,Color',
        'language': 'en',
    })

    body = "{'url':'%s'}" % url

    try:
        # Execute the REST API call and get the response.
        conn = httplib.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
        conn.request("POST", "/vision/v1.0/analyze?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()

        # 'data' contains the JSON data. The following formats the JSON data for display.
        parsed = json.loads(data)
        print("Response: " + parsed['description']['captions'][0]['text'])
        conn.close()
        return parsed['description']['captions'][0]['text']

    except Exception as e:
        print('Error in get_image_description:' + e)

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "MySubredIntent":
        return set_subred_in_session(intent, session)
    elif intent_name == "ReadSubredIntent":
        return get_subreddit_from_session(intent, session)
    elif intent_name == "StopIntent":
        return on_session_stopped(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
