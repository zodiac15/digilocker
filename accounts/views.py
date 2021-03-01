from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .forms import CustomUserCreationForm
import base64
import requests
from .cypher import encrypt, decrypt
from .models import UserBlock
import hashlib


# Create your views here
@login_required
def index(request):
    param = {}
    file_type_dict = {'doc': 'fa fa-file-word-o fa-3x',
                      'docx': 'fa fa-file-word-o fa-3x',
                      'pdf': 'fa fa-file-pdf-o fa-3x',
                      'ppt': 'fa fa-file-powerpoint-o fa-3x',
                      'pptx': 'fa fa-file-powerpoint-o fa-3x',
                      'xls': 'fa fa-file-excel-o fa-3x',
                      'xlsx': 'fa fa-file-excel-o fa-3x',
                      'txt': 'fa fa-file-text-o fa-3x',
                      'jpg': 'fa fa-file-image-o fa-3x',
                      'jpeg': 'fa fa-file-image-o fa-3x',
                      'png': 'fa fa-file-image-o fa-3x ',
                      'default': 'fa fa-file-text fa-3x'
                      }
    icon_colour = {'doc': 'blue',
                   'docx': 'blue',
                   'pdf': 'red',
                   'ppt': 'gold',
                   'pptx': 'gold',
                   'xls': 'green',
                   'xlsx': 'green',
                   'txt': 'gray',
                   'jpg': 'orangered',
                   'jpeg': 'orangered',
                   'png': 'orangered'}
    application_type = {'doc': 'application/msword',
                        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'pdf': 'application/pdf',
                        'ppt': 'application/vnd.ms-powerpoint',
                        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                        'xls': 'application/vnd.ms-excel',
                        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'txt': 'text/plain',
                        'jpg': 'image/jpeg',
                        'jpeg': 'image/jpeg',
                        'png': 'image/png'}

    if request.method == 'POST' and 'upload' in request.POST and request.FILES['upfile']:
        file = request.FILES['upfile']
        name = request.POST['file-name']
        password = hashlib.sha1(request.POST['password'].encode('utf-8')).hexdigest()
        file_type = name.split('.')[-1]
        test = encrypt(base64.b64encode(file.read()).decode('ascii'), password)
        file_hash = test['cipher_text']
        tag = test['tag']
        nonce = test['nonce']
        salt = test['salt']
        file_size = str(file.size)

        data = {'file_name': name,
                'file_type': file_type,
                'file_size': file_size,
                'file_hash': file_hash,
                'tag': tag,
                'nonce': nonce,
                'salt': salt,
                'creator': request.user.username,
                'type': "create"
                }

        response = requests.post('https://digilocker-blockchain.herokuapp.com/api/addblock', data=data).json()
        if 'status' in response and response['status']:
            print(response)
            mb = UserBlock(index=response['index'], user=request.user.username)
            mb.save()
            status = True
        else:
            status = False

        param['uploaded'] = status

    if request.method == 'POST' and 'download' in request.POST:
        indx = request.POST['index']
        password = hashlib.sha1(request.POST['password'].encode('utf-8')).hexdigest()
        response = requests.post('https://digilocker-blockchain.herokuapp.com/api/fetch', data={'index': indx}).json()
        name = response['data']['name']
        f_type = response['data']['file_type']
        nonce = response['data']['nonce']
        salt = response['data']['salt']
        f_hash = response['data']['file_hash']
        tag = response['data']['tag']

        encrypted = {'cipher_text': f_hash, 'salt': salt, 'nonce': nonce, 'tag': tag}
        decrypted = decrypt(encrypted, password)

        with open(name, "wb") as fh:
            fh.write(base64.decodebytes(decrypted))
        with open(name, "rb") as fh:
            httpresponse = HttpResponse(fh.read(), content_type='application/force-download')
            httpresponse['Content-Disposition'] = 'inline; filename=' + name
            return httpresponse

    list_of_index = list(UserBlock.objects.values_list('index', flat=True).filter(user=request.user.username))
    blocks = []
    for i in list_of_index:
        response = requests.post('https://digilocker-blockchain.herokuapp.com/api/fetch', data={'index': i}).json()
        name = response['data']['name']
        file_type = response['data']['file_type']
        if file_type in file_type_dict:
            file_icon = file_type_dict[file_type]
            file_icon_color = icon_colour[file_type]
        else:
            file_icon = file_type_dict['default']
        index = i
        temp = {'name': name,
                'file_type': file_type,
                'file_icon': file_icon,
                'file_icon_color': file_icon_color,
                'index': index}
        blocks.append(temp)

    return render(request, 'accounts/index.html', {'blocks': blocks})


def sign_up(request):
    context = {}
    form = CustomUserCreationForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return render(request, 'accounts/index.html')
    context['form'] = form
    return render(request, 'registration/sign_up.html', context)


'''
def download(request, path):
    file_path = 
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            
    raise Http404
'''
