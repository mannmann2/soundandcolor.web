from django.shortcuts import render #, get_object_or_404
from django.contrib.auth import authenticate
from .forms import LoginForm
from django.contrib.auth.forms import UserCreationForm

# from django.http import Http404
# from django.http import HttpResponse, HttpResponseRedirect
# from django.urls import reverse
# from django.views import generic

import spotipy
import requests
from elasticsearch import Elasticsearch

from dateutil.parser import parse
from django.contrib.auth import logout, login

from .models import User #Choice, Question,
# from .forms import SearchForm

esOn = True
es = Elasticsearch(['localhost:9200'])

def login_page(request):
    form=LoginForm(request.POST)
    return render(request, 'auth/login.html', {'form':form})        

def login_view(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    
    if user is not None:
        login(request, user)
        users = get_friends()

    return render(request, 'users.html', {'users':users})    

def logout_view(request):
    logout(request)
    return render(request, 'auth/logout.html', {})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                users = get_friends()

            return render(request, 'users.html', {'users':users})
    else:
        form = UserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})

def num_format(num):
    return "{:,}".format(num)

def get_time(ms):
    dur = ms/1000
    sec = dur%60
    dur = dur/60
    dur = '%d:%02d'%(dur, sec)
    return dur

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

        # res = requests.get("https://api.spotify.com/v1/me?access_token=" + user.token)
        # print (res)
        # user.name = res.json()['display_name'] if res.json()['display_name'] else ''
        # user.email = res.json()['email'] #if res.json()['email'] else ''
        users.append((user.username, user.email, user.username.split(':')[-1]))

    return render(request, 'users.html', {'users': users})

def get_friends():
    users = []
    f = User.objects.all()
    for user in f:
        uid = user.username.split(':')[-1]
        users.append((user.username, user.email, uid))
    return users
    
def users(request):
    users = get_friends()
    return render(request, 'users.html', {'users': users})


def home(request):
    cid = 'e6f5f053a682454ca4eb1781064d3881'
    # cs = 'e4294f2365ec45c0be87671b0da16596'
    uri = 'http://soundandcolor.life/auth'
    scope = 'user-top-read%20user-follow-read%20user-library-read%20user-read-recently-played%20user-read-email%20streaming'

    url = "https://accounts.spotify.com/authorize/?client_id=" + cid + "&response_type=code&redirect_uri=" + uri + "&scope=" + scope
    return render(request, 'home.html', {'url':url})

def auth(request):
    code = request.GET['code']
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://soundandcolor.life/auth",
        "client_id": 'e6f5f053a682454ca4eb1781064d3881',
        "client_secret" : "e4294f2365ec45c0be87671b0da16596"
        }

    res = requests.post("https://accounts.spotify.com/api/token", data=data)
    js = res.json()

    res = requests.get("https://api.spotify.com/v1/me?access_token=" + js['access_token'])
    js1 = res.json()

    x = User.objects.filter(username=js1['id'])
    if x:
        msg = "Thanks, but no thanks."
    else:
        user = User(username=js1['id'], email=js1['email'], name=js1['display_name'], access_token=js['access_token'], refresh_token=js['refresh_token'])
        user.save()
        msg = "Thank you for the data. :P"

    return render(request, 'auth.html', {"msg": msg})


def search(request):
    # form = SearchForm(request.POST or None)
    user = User.objects.get(username='mannmann2')
    query = request.GET['query']
    url = "https://api.spotify.com/v1/search?q=*" + query + "*&type=album,artist,track&limit=20&access_token=" + user.token
    res = requests.get(url)
    js = res.json()

    albs = []
    for item in js['albums']['items']:
        if not es.exists('simple-album', doc_type='_doc', id=item['id']):
            es.index('simple-album', doc_type='_doc', id=item['id'], body=item)

        if item['images']:
            img3 = item['images'][-1]['url']
        else:
            img3 = ''
        albs.append((item['name'], item['id'], item['release_date'][:4], item['album_type'], img3))

    arts = []
    for item in js['artists']['items']:
        if not es.exists('artist', doc_type='_doc', id=item['id']):
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
        if not es.exists('track', doc_type='_doc', id=item['id']):
            es.index('track', doc_type='_doc', id=item['id'], body=item)
        dur = get_time(item['duration_ms'])
        trks.append((item['name'], dur, item['external_urls']['spotify']))

    return render(request, 'search.html', {'albums':albs, 'artists':arts, 'tracks':trks})


def new(request):
    # username = request.GET['user']
    user = User.objects.get(username='mannmann2')
    url = 'https://api.spotify.com/v1/browse/new-releases?limit=50&access_token=' + user.token
    res = requests.get(url)
    js = res.json()
    albs = []

    # while True:
    for item in js['albums']['items']:
        if item['images']:
            img3 = item['images'][-1]['url']
        else:
            img3 = ''

        albs.append((item['name'], item['id'], parse(item['release_date']).strftime("%d %B"), item['album_type'],
                     item['artists'][0]['name'], item['artists'][0]['id'], img3))

        # if js['albums']['next']:
        #     res = requests.get(js['albums']['next']+"&access_token=" + token)
        #     js = res.json()
        # else:
        #     break

    return render(request, 'new.html', {'new':albs, 'token':user.token})


def details(request, username):
    user = User.objects.get(username=username)
    url = "https://api.spotify.com/v1/me?access_token=" + user.token
    res = requests.get(url)
    js = res.json()

    if not 'display_name' in js:
        refresh(user)
        url = "https://api.spotify.com/v1/me?access_token=" + user.token
        res = requests.get(url)
        js = res.json()

    if js['display_name']:
        name = js['display_name']
        idd = js['id']
    else:
        name = js['id']
        idd = ''

    email = js['email']
    foll = js['followers']['total']

    if js['images']:
        img = js['images'][0]['url']
    else:
        img = ''

    context = {'name':name, 'id':idd,
               'email':email, 'foll':foll,
               'img':img, 'username':js['id']}
    return render(request, 'details.html', context)


def following(request, username):
    user = User.objects.get(username=username)
    foll = []
    url = "https://api.spotify.com/v1/me/following?type=artist&limit=50&access_token=" + user.token
    res = requests.get(url)
    js = res.json()['artists']

    while True:
        for item in js['items']:
            if not es.exists('artist', doc_type='_doc', id=item['id']):
                es.index('artist', doc_type='_doc', id=item['id'], body=item)

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

    return render(request, 'following.html', {'following':foll, 'token':user.token})


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

        return render(request, 'topTracks.html', {'tops':top, 'token':user.token})

    else:
        js = sp.current_user_top_artists(time_range=time, limit=50)
        for item in js['items']:
            if item['images']:
                img = item['images'][2]['url']
            else:
                img = ''
            top.append((item['name'], item['id'], img, item['popularity']))

        return render(request, 'topArtists.html', {'tops':top, 'token':user.token})


def saved(request, username):
    user = User.objects.get(username=username)
    ttype = request.GET['type']
    url = "https://api.spotify.com/v1/me/" + ttype + "?limit=50&access_token=" + user.token
    res = requests.get(url)
    js = res.json()

    saved = []
    while True:
        for item in js['items']:
            if ttype == 'tracks':
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

    if ttype == 'tracks':
        return render(request, 'savedTracks.html', {'saved':saved, 'token':user.token})
    else:
        return render(request, 'savedAlbums.html', {'saved':saved, 'token':user.token})


def artist(request, artist):
    token = request.GET['token']

    if es.exists('artist', doc_type='_doc', id=artist):
        js1 = es.get('artist', doc_type='_doc', id=artist)['_source']
    else:
        url = 'https://api.spotify.com/v1/artists/' + artist + '?access_token=' + token
        res = requests.get(url)
        js1 = res.json()
        es.index('artist', doc_type='_doc', id=artist, body=js1)

    name = js1.pop('name')
    genres = ', '.join(js1.pop('genres'))
    pop = js1.pop('popularity')
    followers = num_format(js1.pop('followers')['total'])
    img = js1.pop('images')[1]['url']


    if es.exists('top-tracks', doc_type='_doc', id=artist):
        js2 = es.get('top-tracks', doc_type='_doc', id=artist)['_source']
    else:
        url = "https://api.spotify.com/v1/artists/" + artist + "/top-tracks?country=US&access_token=" + token #
        res = requests.get(url)
        js2 = res.json()
        es.index('top-tracks', doc_type='_doc', id=artist, body=js2)

    trks = []
    for item in js2['tracks']:
        if not es.exists('track', doc_type='_doc', id=item['id']):
            es.index('track', doc_type='_doc', id=item['id'], body=item)
        dur = get_time(item['duration_ms'])
        trks.append((item['name'], dur, item['external_urls']['spotify']))


    if es.exists('related-artists', doc_type='_doc', id=artist):
        js3 = es.get('related-artists', doc_type='_doc', id=artist)['_source']
    else:
        url = "https://api.spotify.com/v1/artists/" + artist + "/related-artists?access_token=" + token
        res = requests.get(url)
        js3 = res.json()
        es.index('related-artists', doc_type='_doc', id=artist, body=js3)

    related = []
    for item in js3['artists']:
        if not es.exists('artist', doc_type='_doc', id=item['id']):
            es.index('artist', doc_type='_doc', id=item['id'], body=item)

        # if '/' in item['name']:
        #     item['name'] = item['name'].replace('/', ' ')
        # if item['images']:
        #     img2 = item['images'][-1]['url']
        # else:
        img2 = ''
        related.append((item['name'], item['id'], img2, item['popularity']))

    if es.exists('artist-albums', doc_type='_doc', id=artist):
        js = es.get('artist-albums', doc_type='_doc', id=artist)['_source']
    else:
        url = 'https://api.spotify.com/v1/artists/' + artist + '/albums?limit=50&access_token=' + token
        res = requests.get(url)
        js = res.json()
        es.index('artist-albums', doc_type='_doc', id=artist, body=js)

    albs = []
    while True:
        for item in js['items']:
            if not es.exists('simple-album', doc_type='_doc', id=item['id']):
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
    context = {'img':img, 'name':name, 'pop':pop, 'foll':followers, 'genres':genres,
               'tops':trks, 'albums':albs, 'related': related, 'token':token}
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
    if es.exists('album', doc_type='_doc', id=album):
        js = es.get('album', doc_type='_doc', id=album)['_source']
    else:
        url = "https://api.spotify.com/v1/albums/" + album + "?limit=50&access_token=" + token
        res = requests.get(url)
        js = res.json()
        es.index('album', doc_type='_doc', id=album, body=js)

    img = js['images'][1]['url']
    artist_name = js.pop('artists')[0]['name']
    album_type = js.pop('album_type')
    genres = ', '.join(js.pop('genres'))
    name = js.pop('name')
    date = parse(js.pop('release_date'))
    date = date.strftime("%B %d, %Y")
    label = js.pop('label')
    pop = js.pop('popularity')

    if es.exists('album-tracks', doc_type='_doc', id=album):
        js1 = es.get('album-tracks', doc_type='_doc', id=album)['_source']
    else:
        url = "https://api.spotify.com/v1/albums/" + album + "/tracks?limit=50&access_token=" + token
        res = requests.get(url)
        js1 = res.json()
        es.index('album-tracks', doc_type='_doc', id=album, body=js1)

    trks = []
    while True:
        for item in js1['items']:
            if not es.exists('simple-track', doc_type='_doc', id=item['id']):
                es.index('simple-track', doc_type='_doc', id=item['id'], body=item)

            dur = get_time(item['duration_ms'])
            trks.append((item['name'], dur, item['external_urls']['spotify']))

        if js1['next']:
            res = requests.get(js1['next']+"&access_token=" + token)
            js = res.json()
        else:
            break

    context = {'img':img, 'name':name, 'pop':pop, 'artist':artist_name, 'type':album_type,
               'genres':genres, 'label':label, 'date':date, 'tracks':trks, 'token':token}
    return render(request, 'album.html', context)


def genres(request, username):
    user = User.objects.get(username=username)
    pass


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
