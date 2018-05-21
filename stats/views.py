from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .models import User #Choice, Question,

import requests, json
from dateutil.parser import parse

# class IndexView(generic.ListView):
#     template_name = 'stats/index.html'
#     context_object_name = 'latest_question_list'

#     def get_queryset(self):
#         """Return the last five published questions."""
#         return Question.objects.order_by('-pub_date')[:5]

# class DetailView(generic.DetailView):
#     model = Question
#     template_name = 'stats/detail.html'

# class ResultsView(generic.DetailView):
#     model = Question
#     template_name = 'stats/results.html'

# def vote(request, question_id):
#     question = get_object_or_404(Question, pk=question_id)
#     try:
#         selected_choice = question.choice_set.get(pk=request.POST['choice'])
#     except (KeyError, Choice.DoesNotExist):
#         # Redisplay the question voting form.
#         return render(request, 'stats/detail.html', {
#             'question': question,
#             'error_message': "You didn't select a choice.",
#         })
#     else:
#         selected_choice.votes += 1
#         selected_choice.save()
#         # Always return an HttpResponseRedirect after successfully dealing
#         # with POST data. This prevents data from being posted twice if a
#         # user hits the Back button.
#         return HttpResponseRedirect(reverse('stats:results', args=(question.id,)))

def get_time(ms):
    dur = ms/1000
    sec = dur%60
    dur = dur/60
    dur = '%d:%02d'%(dur, sec)
    return dur


def home(request):
    cid = 'e6f5f053a682454ca4eb1781064d3881'
    cs = 'e4294f2365ec45c0be87671b0da16596'
    uri = 'https://demo8.orkash.com/spotify'
    scope = 'user-top-read%20user-follow-read%20user-library-read%20user-read-recently-played%20user-read-email%20streaming'

    url = "https://accounts.spotify.com/authorize/?client_id=" + cid + "&response_type=code&redirect_uri=" + uri + "&scope=" + scope
    return render(request, 'stats/home.html', {'url':url})

def refresh(request):
    f = User.objects.all()
    users = []

    for user in f:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": user.refresh_token,
            "client_id": 'e6f5f053a682454ca4eb1781064d3881',
            "client_secret": "e4294f2365ec45c0be87671b0da16596"
        }
        res = requests.post("https://accounts.spotify.com/api/token", data=data)
        print (res)
        js = res.json()
        user.token = js['access_token']

        # res = requests.get("https://api.spotify.com/v1/me?access_token=" + user.token)
        # print (res)
        # user.name = res.json()['display_name'] if res.json()['display_name'] else ''
        # user.email = res.json()['email'] #if res.json()['email'] else ''
        user.save()
        users.append((user.username, user.email, user.username.split(':')[-1]))

    return render(request, 'stats/users.html', {'users': users })

def users(request):
    f = User.objects.all()

    users = []
    for user in f:
        users.append((user.username, user.email, user.username.split(':')[-1]))

    return render(request, 'stats/users.html', {'users': users })


def details(request, username):
    user=User.objects.get(username=username)

    url = "https://api.spotify.com/v1/me?access_token=" + user.token
    res = requests.get(url)
    js = res.json()
    if js['display_name']:
        name = js['display_name']
        idd = js['id']
    else:
        name = js['id']
        idd=''
    
    email = js['email']
    foll =js['followers']['total']

    if js['images']:
        img = js['images'][0]['url']
    else:
        img = ''

    return render(request, 'stats/details.html', {'name':name, 'id':idd, 'email':email, 'foll':foll, 'img':img, 'username':js['id']})


def top(request, username):
    user=User.objects.get(username=username)
    ttype = request.GET['type']
    time = request.GET['time']
    url = "https://api.spotify.com/v1/top/artists?access_token=" + user.token
    # url = "https://api.spotify.com/v1/me/top/" + ttype + "?time_range=" + time + "&limit=50&access_token=" + user.token
    print (url)
    res = requests.get(url)
    js = res.json()
    print (js)
    top = []
    for item in js['items']:
        dur = get_time(item['duration_ms'])
        top.append((item['name'], item['artists'][0]['name'], item['album']['name'], dur))

    return render(request, 'stats/top.html', {'tops':top})


def following(request, username):
    user=User.objects.get(username=username)
    foll = []
    url = "https://api.spotify.com/v1/me/following?type=artist&limit=50&access_token=" + user.token
    res = requests.get(url)
    js = res.json()['artists']

    while True:
        for item in js['items']:
            if '/' in item['name']:
                item['name'] = item['name'].replace('/', ' ')
            if item['images']:
                img = item['images'][-1]['url']
            else:
                img = ''
            foll.append((item['name'], item['id'], img, item['popularity']))

        if js['next']:
            print ('.', end='')
            res = requests.get(js['next']+"&access_token=" + user.token)
            js = res.json()['artists']
        else:
            break

    return render(request, 'stats/following.html', {'following':foll, 'token':user.token})

def saved(request, username):
    user = User.objects.get(username = username)
    ttype = request.GET['type']
    url = "https://api.spotify.com/v1/me/" + ttype + "?limit=50&access_token=" + user.token
    res = requests.get(url)
    js = res.json()

    saved = []
    while True:
        for item in js['items']:
            if ttype=='tracks':
                dur = get_time(item['track']['duration_ms'])
                saved.append((item['track']['name'], item['track']['external_urls']['spotify'], 
                            item['track']['album']['artists'][0]['name'], item['track']['album']['artists'][0]['id'],
                            item['track']['album']['name'], item['track']['album']['id'], dur))
            else:
                saved.append((item['album']['name'], item['album']['id'], 
                        item['album']['release_date'][:4], item['album']['artists'][0]['name'], 
                        item['album']['artists'][0]['id'], item['album']['images'][-1]['url']))
        
        if js['next']:
            res = requests.get(js['next']+"&access_token=" + user.token)
            js = res.json()
        else:
            break

    if ttype=='tracks':
        return render(request, 'stats/savedTracks.html', {'saved':saved, 'token':user.token})
    else:
        return render(request, 'stats/savedAlbums.html', {'saved':saved, 'token':user.token})


def genres(request, username):
    user = User.objects.get(username = username)
    pass


def artist(request, artist):
    token = request.GET['token']

    url = 'https://api.spotify.com/v1/artists/' + artist + '?access_token=' + token
    res = requests.get(url)
    js1 = res.json()
    name = js1.pop('name')
    genres = ', '.join(js1.pop('genres'))
    pop = js1.pop('popularity')
    followers = js1.pop('followers')['total']
    img = js1.pop('images')[1]['url']

    url = "https://api.spotify.com/v1/artists/" + artist + "/top-tracks?country=US&access_token=" + token
    res = requests.get(url)
    js2 = res.json()
    trks = []
    for track in js2['tracks']:
        dur = get_time(track['duration_ms'])
        trks.append((track['name'], dur, track['external_urls']['spotify']))

    albs = []
    url = 'https://api.spotify.com/v1/artists/' + artist + '/albums?limit=50&access_token=' + token
    res = requests.get(url)
    js = res.json()

    while True:
        for item in js['items']:
            albs.append((item['name'], item['id'], item['release_date'][:4], item['album_type'], item['images'][-1]['url']))

        if js['next']:
            res = requests.get(js['next']+"&access_token=" + token)
            js = res.json()
        else:
            break

    return render(request, 'stats/artist.html', {'img':img, 'name':name, 'pop':pop, 'foll':followers, 'genres':genres, 'tops':trks, 'albums':albs, 'token':token})


def album(request, album):
    token = request.GET['token']
    # play = request.GET['play']
    # if play:
    #     uris = {"uris":[play[1:]]}
    #     url = "https://api.spotify.com/v1/me/player/play?access_token=" + token
    #     # url = url.replace(' ', '')
    #     res = requests.put(url, data = uris)
    #     print (res.text)

    url = "https://api.spotify.com/v1/albums/" + album + "?limit=50&access_token=" + token
    res = requests.get(url)
    js = res.json()

    img = js['images'][1]['url']
    artist_name = js.pop('artists')[0]['name']
    album_type = js.pop('album_type')
    genres = ', '.join(js.pop('genres'))
    name = js.pop('name')
    date = parse(js.pop('release_date'))
    date = date.strftime("%B %d, %Y")
    label = js.pop('label')
    pop = js.pop('popularity')

    trks = []
    url = "https://api.spotify.com/v1/albums/" + album + "/tracks?limit=50&access_token=" + token
    res = requests.get(url)
    js1 = res.json()

    while True:
        for track in js1['items']:
            dur = get_time(track['duration_ms'])
            trks.append((track['name'], dur, track['external_urls']['spotify']))

        if js1['next']:
            res = requests.get(js1['next']+"&access_token=" + token)
            js = res.json()
        else:
            break    

    return render(request, 'stats/album.html', {'img':img, 'name':name, 'pop':pop, 'artist':artist_name, 'type':album_type, 'genres':genres, 'label':label, 'date':date, 'tracks':trks, 'token':token})


