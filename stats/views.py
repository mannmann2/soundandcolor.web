from django.shortcuts import render #, get_object_or_404
from django.contrib.auth import authenticate
from .forms import LoginForm
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings

# from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
# from django.urls import reverse
# from django.views import generic
import json
import spotipy
import requests
from random import random
from elasticsearch import Elasticsearch
# import plotly.plotly as py
# import plotly.graph_objs as go
# import plotly
from colorthief import ColorThief

# plotly.tools.set_credentials_file(username='armanmann2', api_key='UQYdm8ikKKAL7pLJ7wzp')
import networkx as nx
from dateutil.parser import parse
from django.contrib.auth import logout, login
from urllib.request import urlopen
import io

from .models import CustomUser as User

# scope = 'user-top-read%20user-follow-read%20user-library-read%20user-read-recently-played%20user-read-email%20streaming'
# url = "https://accounts.spotify.com/authorize/?client_id=" + cid + "&response_type=code&redirect_uri=" + uri + "&scope=" + scope

esOn = True
es = Elasticsearch(['localhost:9200'])

def save():
    with open('spotify.txt', 'r') as f:
        data = f.read()

    data = json.loads('[' + data[:-1] + ']')

    for js in data:
        data2 = {
        "grant_type": "refresh_token",
        "refresh_token": js['refresh_token'],
        "client_id": 'e6f5f053a682454ca4eb1781064d3881',
        "client_secret": "e4294f2365ec45c0be87671b0da16596"
        }

        res = requests.post("https://accounts.spotify.com/api/token", data=data2)

        res = requests.get("https://api.spotify.com/v1/me?access_token=" + res.json()['access_token'])
        js1 = res.json()
        print(js1)
        x = User.objects.filter(username=js1['id'])
        if not x:
            print (js1['id'])
            user = User(username=js1['id'], email=js1['email'], uri=js1['uri'], name=js1['display_name'], access_token=js['access_token'], refresh_token=js['refresh_token'], scope=js['scope'])
            user.set_password('password')
            user.save()

def num_format(num):
    return "{:,}".format(num)

def get_time(ms):
    dur = ms/1000
    sec = dur%60
    dur = dur/60
    dur = '%d:%02d'%(dur, sec)
    return dur

# def signup(request):
    # if request.method == 'POST':
    #     form = UserCreationForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         username = form.cleaned_data.get('username')
    #         raw_password = form.cleaned_data.get('password1')
    #         user = authenticate(username=username, password=raw_password)
    #         if user is not None:
    #             login(request, user)

            # return HttpResponseRedirect('/friends')
    # else:
    #     form = UserCreationForm()
    # return render(request, 'auth/signup.html', {'form': form})
# def login_page(request):
    # form=LoginForm(request.POST)
    # return render(request, 'auth/login.html', {'form':form})
# def login_view(request):
    # username = request.POST['username']
    # password = request.POST['password']
    # user = authenticate(username=username, password=password)
    
    # if user is not None:
    #     login(request, user)
    # return HttpResponseRedirect('/') 

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')

def auth(request):
    code = request.GET['code']
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://www.localhost:8000/auth",
        # "redirect_uri": "http://www.soundandcolor.life/auth",
        "client_id": 'e6f5f053a682454ca4eb1781064d3881',
        "client_secret" : "e4294f2365ec45c0be87671b0da16596"
        }

    res = requests.post("https://accounts.spotify.com/api/token", data=data)
    js = res.json()
    res = requests.get("https://api.spotify.com/v1/me?access_token=" + js['access_token'])
    js1 = res.json()
    print(js1)
    user = User.objects.filter(username=js1['id'])
    if not user:
        user = User(username=js1['id'], email=js1['email'], uri=js1['uri'], name=js1['display_name'], access_token=js['access_token'], refresh_token=js['refresh_token'], scope=js['scope'])
        user.set_password("password")
        user.token = js['access_token']
        #make call to following
        user.save()
    else: ######
        user[0].scope = js['scope']
        user[0].save()

    user = authenticate(username=js1['id'], password="password")    
    login(request, user)
    return HttpResponseRedirect('/friends')

def refresh(user):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": user.refresh_token,
        "client_id": 'e6f5f053a682454ca4eb1781064d3881',
        "client_secret": "e4294f2365ec45c0be87671b0da16596"
        }

    res = requests.post("https://accounts.spotify.com/api/token", data=data)
    print(res)
    user.token = res.json()['access_token']
    user.save()

def refresh_all(request):
    f = User.objects.all()
    users = []

    for user in f:
        refresh(user)
        users.append((user.username, user.email, user.username.split(':')[-1]))

    return HttpResponseRedirect('/friends')

def add_friend(request):
    current_user = request.user
    username = request.GET['query']

    # Add as friend in both users after a notification
    # for user1 in User.objects.all():
    #     x += user1.username
    if username and User.objects.filter(username=username) and username not in current_user.friends.split(',')[:-1]:
        current_user.friends += username + ','
        current_user.save()
        message = 'Added ' + username + '.'
        # message = 'Notification sent.'
    elif not username:
        message = ''
    elif not User.objects.filter(username=username):
        message = "User does not exist. Make sure they've signed up."        
    else:
        message = 'You are already friends.'
    return render(request, 'users.html', {'users': get_friends(current_user), 'message':message})
    # return HttpResponseRedirect('/friends')

def get_friends(current_user):
    users = []
    f = User.objects.all()
    if current_user is None:
        fx = [user.username for user in f]
    else:
        fx = current_user.friends.split(',')[:-1]
    for user in f:
        if user != current_user and user.username in fx:
            name = user.name or user.username
            # try:
            #     url = "https://api.spotify.com/v1/me/player/currently-playing?access_token=" + user.token
            #     js = requests.get(url).json()
            #     print (js)
            #     tName = js['item']['name']
            #     tArtist = js['item']['artists'][0]['name']
            #     tUrl = js['item']['href']
            # except:
            #     tName =''
            #     tArtist = ''
            #     tUrl = ''
            users.append((user.username, user.email, name))
    return users

def users(request):
    current_user = request.user
    friends = get_friends(current_user)
    genres = {}
    for friend in friends:
        try:
            js = es.get('following', doc_type='_doc', id=friend[0])['_source']['ids']
        except:
            continue
        for fid in js:
            js2 = es.get('artist', doc_type='_doc', id=fid)['_source']['genres']
            for genre in js2:
                if genre in genres:
                    genres[genre] += 1
                else:
                    genres[genre] = 1
    genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:30]
    return render(request, 'users.html', {'users': friends, 'genres':genres})

def home(request):
    # current_user = request.user
    cols = []
    for ch in "Sound & Color":
        cols.append([ch, 20+100*random(), 140+100*random(), 155+100*random()])
    # save()
    return render(request, 'home.html', {'users': get_friends(None), 'cols':cols})




# def ref(request):
#     cols = []
#     for ch in "Sound & Color":
#         cols.append([ch, 60+100*random(), 140+100*random(), 155+100*random()])
#     return render(request, 'dom.html', {'cols':cols})
#     # return HttpResponse(cols)

# def ff(request):
#     test_file = open('config.json', 'rb')
#     response = HttpResponse(content=test_file)
#     response['Content-Type'] = 'application/pdf'
#     response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % 'whatever'
#     return response




def details(request, username):
    user = User.objects.get(username=username)
    url = "https://api.spotify.com/v1/me?access_token=" + user.token
    res = requests.get(url)
    js = res.json()
    if 'display_name' not in js:
        refresh(user)
        url = "https://api.spotify.com/v1/me?access_token=" + user.token
        res = requests.get(url)
        js = res.json()

    name = user.name or username
    idd = '' if name == username else username 
    email = user.email
    uri = user.uri

    if js['images']:
        img = js['images'][0]['url']
    else:
        img = ''

    genres = {}
    try:
        js1 = es.get('following', doc_type='_doc', id=username)['_source']['ids']
        for fid in js1:
            js2 = es.get('artist', doc_type='_doc', id=fid)['_source']['genres']
            for genre in js2:
                if genre in genres:
                    genres[genre] += 1
                else:
                    genres[genre] = 1
        genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:10]
    except:
        pass
    context = {'name':name, 'id':idd,
               'email':email, 'img':img, 'username':js['id'],
               'users':get_friends(user), 'uri':uri, 'genres':genres}
    return render(request, 'details.html', context)


def viz(request):
    x = request.GET['username']
    y = request.GET['genre']
    art = []
    js1 = es.get('following', doc_type='_doc', id=x)['_source']['ids']
    for fid in js1:
        js2 = es.get('artist', doc_type='_doc', id=fid)['_source']
        if y in js2['genres']:
            art.append((js2['id'], js2['name'], js2['images'][-2]['url']))
    return render(request, 'viz.html', {'genre':y, 'art':art, 'token':request.user.token})


def search(request):
    # form = SearchForm(request.POST or None)
    user = User.objects.get(username='mannmann2')
    query = request.GET['query']
    url = "https://api.spotify.com/v1/search?q=*" + query + "*&type=album,artist,track&limit=20&access_token=" + user.token
    res = requests.get(url)
    js = res.json()

    albs = []
    for item in js['albums']['items']:
        # if not es.exists('simple-album', doc_type='_doc', id=item['id']):
        es.index('simple-album', doc_type='_doc', id=item['id'], body=item)

        if item['images']:
            img3 = item['images'][-1]['url']
        else:
            img3 = ''
        albs.append((item['name'], item['id'], item['release_date'][:4], item['album_type'], img3))

    arts = []
    for item in js['artists']['items']:
        # if not es.exists('artist', doc_type='_doc', id=item['id']):
        es.index('artist', doc_type='_doc', id=item['id'], body=item)

        # if '/' in item['name']:
        #     item['name'] = item['name'].replace('/', ' ')
        if item['images']:
            img = item['images'][-1]['url']
        else:
            img = ''
        arts.append((item['name'], item['id'], img, item['popularity']))

    trks = []
    for item in js['tracks']['items']:
        # if not es.exists('track', doc_type='_doc', id=item['id']):
        es.index('track', doc_type='_doc', id=item['id'], body=item)

        dur = get_time(item['duration_ms'])
        trks.append((item['name'], dur, item['external_urls']['spotify']))

    return render(request, 'search.html', {'token':user.token, 'albums':albs, 'artists':arts, 'tracks':trks})


def new(request):
    user = request.user
    url = 'https://api.spotify.com/v1/browse/new-releases?limit=50&access_token=' + user.token
    res = requests.get(url)
    js = res.json()
    albs = []

    # while True:
    for item in js['albums']['items']:
        if item['images']:
            img3 = item['images'][-2]['url']
        else:
            img3 = ''

        albs.append((item['name'], item['id'], parse(item['release_date']).strftime("%d %B"), item['album_type'], item['artists'][0]['name'], item['artists'][0]['id'], img3))

        es.index('simple-album', doc_type='_doc', id=item['id'], body=item)        

        # if js['albums']['next']:
        #     res = requests.get(js['albums']['next']+"&access_token=" + token)
        #     js = res.json()
        # else:
        #     break

    return render(request, 'new.html', {'new':albs, 'token':user.token})


def following(request, username):
    user = User.objects.get(username=username)
    foll = []
    url = "https://api.spotify.com/v1/me/following?type=artist&limit=50&access_token=" + user.token
    res = requests.get(url)
    js = res.json()['artists']

    ids = []
    while True:
        for item in js['items']:
            # if not es.exists('artist', doc_type='_doc', id=item['id']):
            es.index('artist', doc_type='_doc', id=item['id'], body=item)
            ids.append(item['id'])
            # if '/' in item['name']:
            #     item['name'] = item['name'].replace('/', ' ')
            if item['images']:
                img = item['images'][-1]['url']
            else:
                img = ''
            foll.append((item['name'], item['id'], img, item['popularity']))

        if js['next']:
            print('.', end='')
            res = requests.get(js['next']+"&access_token=" + user.token)
            js = res.json()['artists']
        else:
            break
    es.index('following', doc_type='_doc', id=username, body={'ids':ids})
    return render(request, 'following.html', {'following':foll, 'token':user.token, 'count':len(ids)})


def recent(request, username):
    user = User.objects.get(username=username)

    url = "https://api.spotify.com/v1/me/player/recently-played?limit=50&access_token=" + user.token
    res = requests.get(url)
    js = res.json()

    recents = []

    for item in js['items']:
        dur = get_time(item['track']['duration_ms'])
        recents.append((item['track']['name'], item['track']['external_urls']['spotify'],
                        item['track']['album']['artists'][0]['name'], item['track']['album']['artists'][0]['id'],
                        item['track']['album']['name'], item['track']['album']['id'], dur,
                        parse(item['played_at'])))
                        # (datetime.strptime(item['played_at'],'%Y-%m-%dT%H:%M:%S.%fZ').timestamp()+19800).strftime('%B %d, %-I:%M %p')))

        es.index('simple-track', doc_type='_doc', id=item['track']['id'], body=item['track'])
    return render(request, 'recent.html', {'recent':recents, 'token':user.token})


def top(request, username):
    user = User.objects.get(username=username)
    ttype = request.GET['type']
    time = request.GET['time']
    # url = "https://api.spotify.com/v1/me/top/" + ttype + "?time_range=" + time + "&limit=50&access_token=" + user.token
    # print (url)
    # res = requests.get(url)
    # js = res.json()
    # print (js)
    top = []

    sp = spotipy.Spotify(auth=user.token)
    sp.trace = False
    if ttype == 'tracks':
        js = sp.current_user_top_tracks(time_range=time, limit=50)
        for item in js['items']:
            dur = get_time(item['duration_ms'])
            top.append((item['name'], item['external_urls']['spotify'],
                        item['album']['artists'][0]['name'], item['album']['artists'][0]['id'],
                        item['album']['name'], item['album']['id'], dur))

            es.index('track', doc_type='_doc', id=item['id'], body=item)
        return render(request, 'topTracks.html', {'tops':top, 'token':user.token})

    else:
        js = sp.current_user_top_artists(time_range=time, limit=50)
        for item in js['items']:
            if item['images']:
                img = item['images'][2]['url']
            else:
                img = ''
            top.append((item['name'], item['id'], img, item['popularity']))

            es.index('artist', doc_type='_doc', id=item['id'], body=item)
        return render(request, 'topArtists.html', {'tops':top, 'token':user.token})


def saved(request, username):
    user = User.objects.get(username=username)
    ttype = request.GET['type']
    url = "https://api.spotify.com/v1/me/" + ttype + "?limit=50&access_token=" + user.token
    res = requests.get(url)
    js = res.json()

    count = 0
    saved = []
    while True:
        if ttype == 'tracks':
            for item in js['items']:
                dur = get_time(item['track']['duration_ms'])
                saved.append((item['track']['name'], item['track']['external_urls']['spotify'],
                              item['track']['album']['artists'][0]['name'], item['track']['album']['artists'][0]['id'],
                              item['track']['album']['name'], item['track']['album']['id'], dur))
                count += 1
                es.index('track', doc_type='_doc', id=item['track']['id'], body=item['track'])

        else:
            for item in js['items']:
                saved.append((item['album']['name'], item['album']['id'],
                              item['album']['release_date'][:4], item['album']['artists'][0]['name'],
                              item['album']['artists'][0]['id'], item['album']['images'][-1]['url']))

                count += 1
                es.index('album', doc_type='_doc', id=item['album']['id'], body=item['album'])

        if js['next']:
            print('.')
            res = requests.get(js['next']+"&access_token=" + user.token)
            js = res.json()
        else:
            break

    context = {'saved':saved, 'token':user.token, 'count':count}
    if ttype == 'tracks':
        return render(request, 'savedTracks.html', context)
    else:
        return render(request, 'savedAlbums.html', context)


def get_related_artists(artist, token):
    url = "https://api.spotify.com/v1/artists/" + artist + "/related-artists?access_token=" + token
    # print (url)
    res = requests.get(url)
    js = res.json()
    es.index('related-artists', doc_type='_doc', id=artist, body=js)
    return js

def artist(request, artist):
    token = request.GET['token']

    # if es.exists('artist', doc_type='_doc', id=artist):
    #     js1 = es.get('artist', doc_type='_doc', id=artist)['_source']
    # else:
    url = 'https://api.spotify.com/v1/artists/' + artist + '?access_token=' + token
    res = requests.get(url)
    js1 = res.json()
    es.index('artist', doc_type='_doc', id=artist, body=js1)

    name = js1.pop('name')
    genres = ', '.join(js1.pop('genres'))
    pop = js1.pop('popularity')
    img = js1.pop('images')[1]['url']
    uri = js1.pop('uri')

    # if es.exists('top-tracks', doc_type='_doc', id=artist):
    #     js2 = es.get('top-tracks', doc_type='_doc', id=artist)['_source']
    # else:
    url = "https://api.spotify.com/v1/artists/" + artist + "/top-tracks?country=US&access_token=" + token #
    res = requests.get(url)
    js2 = res.json()
    es.index('top-tracks', doc_type='_doc', id=artist, body=js2)

    trks = []
    for item in js2['tracks']:
        # if not es.exists('track', doc_type='_doc', id=item['id']):
        es.index('track', doc_type='_doc', id=item['id'], body=item)

        dur = get_time(item['duration_ms'])
        trks.append((item['name'], dur, item['external_urls']['spotify']))


    # if es.exists('related-artists', doc_type='_doc', id=artist):
    #     js3 = es.get('related-artists', doc_type='_doc', id=artist)['_source']
    # else:
    js3 = get_related_artists(artist, token)

    related = []
    for item in js3['artists']:
        # if not es.exists('artist', doc_type='_doc', id=item['id']):
        es.index('artist', doc_type='_doc', id=item['id'], body=item)

        # if '/' in item['name']:
        #     item['name'] = item['name'].replace('/', ' ')
        # if item['images']:
        #     img2 = item['images'][-1]['url']
        # else:
        img2 = ''
        related.append((item['name'], item['id'], img2, item['popularity']))

    # if es.exists('artist-albums', doc_type='_doc', id=artist):
    #     js = es.get('artist-albums', doc_type='_doc', id=artist)['_source']
    # else:
    url = 'https://api.spotify.com/v1/artists/' + artist + '/albums?limit=50&access_token=' + token
    res = requests.get(url)
    js = res.json()
    es.index('artist-albums', doc_type='_doc', id=artist, body=js)

    albs = []
    while True:
        for item in js['items']:
            # if not es.exists('simple-album', doc_type='_doc', id=item['id']):
            es.index('simple-album', doc_type='_doc', id=item['id'], body=item)

            if item['images']:
                img3 = item['images'][-1]['url']
            else:
                img3 = ''
            albs.append((item['name'], item['id'], item['release_date'][:4], item['album_type'], img3))

        if js['next']:
            res = requests.get(js['next']+"&access_token=" + token)
            js = res.json()
        else:
            break
    context = {'img':img, 'name':name, 'pop':pop, 'genres':genres,
               'tops':trks, 'albums':albs, 'related': related, 'token':token, 'uri':uri}
    return render(request, 'artist.html', context)


def album(request, album):
    token = request.GET['token']
    # play = request.GET['play']
    # if play:
    #     uris = {"uris":[play[1:]]}
    #     url = "https://api.spotify.com/v1/me/player/play?access_token=" + token
    #     # url = url.replace(' ', '')
    #     res = requests.put(url, data = uris)
    #     print (res.text)
    # if es.exists('album', doc_type='_doc', id=album):
    #     js = es.get('album', doc_type='_doc', id=album)['_source']
    # else:
    url = "https://api.spotify.com/v1/albums/" + album + "?limit=50&access_token=" + token
    res = requests.get(url)
    js = res.json()
    es.index('album', doc_type='_doc', id=album, body=js)

    img = js['images'][0]['url']
    artist = js.pop('artists')
    artist_name = artist[0]['name']
    artist_id = artist[0]['id']
    album_type = js.pop('album_type')
    genres = ', '.join(js.pop('genres'))
    name = js.pop('name')
    date = parse(js.pop('release_date'))
    date = date.strftime("%B %d, %Y")
    label = js.pop('label')
    pop = js.pop('popularity')
    uri = js.pop('uri')

    img_url = urlopen(img)
    img_file = io.BytesIO(img_url.read())
    color_thief = ColorThief(img_file)
    dom = color_thief.get_color(quality=50)

    # if es.exists('album-tracks', doc_type='_doc', id=album):
    #     js1 = es.get('album-tracks', doc_type='_doc', id=album)['_source']
    # else:
    url = "https://api.spotify.com/v1/albums/" + album + "/tracks?limit=50&access_token=" + token
    res = requests.get(url)
    js1 = res.json()
    es.index('album-tracks', doc_type='_doc', id=album, body=js1)

    trks = []
    while True:
        for item in js1['items']:
            # if not es.exists('simple-track', doc_type='_doc', id=item['id']):
            es.index('simple-track', doc_type='_doc', id=item['id'], body=item)

            dur = get_time(item['duration_ms'])
            trks.append((item['name'], dur, item['external_urls']['spotify']))

        if js1['next']:
            res = requests.get(js1['next']+"&access_token=" + token)
            js = res.json()
        else:
            break

    context = {'img':img, 'name':name, 'pop':pop, 'artist':artist_name, 'id':artist_id, 'type':album_type, "dom":dom, 'genres':genres, 'label':label, 'date':date, 'tracks':trks, 'token':token, 'uri':uri}
    return render(request, 'album.html', context)


def genres(request, username):
    user = User.objects.get(username=username)
    pass



def graphs(request):
    # ti = request.user.token
    # graph = nx.DiGraph()
    # i = 0
    # p = []
    # id1 = '1O10apSOoAPjOu6UhUNmeI'
    # a1 = 'Unknown Mortal Orchestra'
    # print (a1)
    # p.append(a1)
    # graph.add_node(a1, ntype = 'level' + str(i))
    # i+=1
    # js = get_related_artists(id1, ti)
    # def finc(a, js, i):
    #     rel = []
    #     for artist in js['artists']:
    #         if not graph.has_node(artist['name']):
    #             graph.add_node(artist['name'], ntype = 'level' + str(i))
    #         if not graph.has_edge(a, artist['name']):
    #             graph.add_edge(a, artist['name'])
                
    #         rel.append((artist['name'], artist['id']))
    #         nx.write_gexf(graph, "related.gexf")    
    #     i+=1
    #     if i<10:    
    #         for (a, reli) in rel:
    #             if a not in p:
    #                 print (a)
    #                 p.append(a)
    #                 js = get_related_artists(reli, ti)
    #                 if 'artists' not in js:                  
    #                     res = requests.post("https://accounts.spotify.com/api/token", data=data)
    #                     js = json.loads(res.text)
    #                     token = js['access_token']
    #                     js = get_related_artists(reli, ti)
    #                     if 'artists' in js:
    #                         print ("OK")
    #                     else:
    #                         print ("nOK")
    #                 finc(a, js, i)
    # finc(a1, js, i)
    # nx.write_gexf(graph, "related.gexf")
    return render(request, "graphs3.html", {})


# class IndexView(generic.ListView):
#     template_name = 'stats/index.html'
#     context_object_name = 'latest_question_list'

#     def get_queryset(self):
#         """Return the last five published questions."""
#         return Question.objects.order_by('-pub_date')[:5]

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
