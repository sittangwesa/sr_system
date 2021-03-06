from multiprocessing import context
from unicodedata import name
from django.http import HttpResponse
from pydoc_data.topics import topics
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .models import College, Repository
from .form import UploadFileForm
from django.views.generic.edit import FormView
from .form import FileFieldForm
# from somewhere import handle_uploaded_file
from .form import RepositoryForm,UserForm
from django.core.mail import send_mail,EmailMessage,EmailMultiAlternatives
import imaplib
import datetime
import email
import getpass
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper
import mimetypes
import os
from django.utils.datastructures import MultiValueDictKeyError

# Create your views here.


def loginPage(request):
    page='login'
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username= request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist!')  
            
        user= authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')    
        else:
             messages.error(request, 'User or Password does not exist!')  
            
              
    context ={'page' : page}
    return render(request, 'srbase/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('login')

def registerPage(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form= UserCreationForm(request.POST)
        if form.is_valid():
            user= form.save(commit=False)
            user.username= user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occured during registration')
    return render(request, 'srbase/login_register.html', {'form' : form})

def userProfile(request,pk):
    user = User.objects.get(id=pk)
    repositories = user.repository_set.all()
    colleges = College.objects.all()
    
    context = {'user': user, 'repositories':repositories, 'colleges':colleges }
    return render(request, 'srbase/profile.html', context)

def collegePage(request):
    q= request.GET.get('q') if request.GET.get('q') != None else ''
    colleges = College.objects.filter(name__icontains=q)
    context={'colleges' : colleges}
    return render(request, 'srbase/community.html', context)

def collegePage(request):
    q= request.GET.get('q') if request.GET.get('q') != None else ''
    colleges = College.objects.filter(name__icontains=q)
    context={'colleges' : colleges}
    return render(request, 'srbase/communities.html', context)

# def download(request):
#     base_dir= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     filename='docfile'
#     filepath= base_dir + '/download/' + filename
#     thefile=filepath
#     filename= os.path.basename(thefile)
#     chunk_size=8192
#     reponse=StreamingHttpResponse(FileWrapper(open(thefile, 'rb'),chunk_size),
#     content_type=mimetypes.guess_type(thefile)[0])
#     response['Content-Length']=os.path.getsize(thefile)
#     response['Content-Disposition']="Attachment;filename=%s" % filename
#     return response

    

def home(request):
    q= request.GET.get('q') if request.GET.get('q') != None else ''
    

    repositories = Repository.objects.filter(
        Q(college__name__icontains=q) |
        Q(title__icontains=q) |
        Q(description__icontains=q)
    )
    
    colleges= College.objects.all()
    repository_count= repositories.count()
    college_repositories = College.objects.all()
    
    
    context ={'repositories': repositories, 'colleges':colleges,  ' college_repositories':  college_repositories, 'repository_count': repository_count}
    return render(request, 'srbase/home.html', context)

def repository(request,pk):
    repository= Repository.objects.get(id=pk)
    context = {'repository': repository}
    return render(request, "srbase/repository.html", context)


    

# def title(request):
#     q= request.GET.get('q') if request.GET.get('q') != None else ''
#     titles = Title.objects.filter(name__icontains=q)
#     context={'titles' : titles}
#     return render(request,'srbase/titles.html', context)

def authorsPage(request, pk):
     
    authors = User.objects.get(id=pk)
    context = {'authors' : authors}

    
    return render(request,'srbase/authors.html', context)
    
@login_required(login_url='login')
def createRepository(request):
    form = RepositoryForm()
    # if request.method == 'POST':
    #     form = RepositoryForm(request.POST or None)
    #     if form.is_valid():
    #         form.save()
    #         return redirect('home')
    
    colleges= College.objects.all()
    
    if request.method == 'POST':
        college_name=request.POST.get('college')
        college, created= College.objects.get_or_create(name= college_name)
        form = RepositoryForm()
        uploaded_file = request.FILES['file']
        print(uploaded_file.name)
        print(uploaded_file.size)
        
        if form.is_valid():

            repository=form.save(commit=False)
            repository.host=request.user
            repository.save()
        Repository.objects.create(
            author = request.user,
            college = college,
            title= request.POST.get('title'),
            description= request.POST.get('description'),
        )
        
        return redirect('home')
        
    
  
    context = {'form': form}
    return render(request, 'srbase/repository_form.html', context)

@login_required(login_url='login')
def updateRepository(request, pk):
    repository = Repository.objects.get(id =pk)
    form = RepositoryForm(instance=repository)
    colleges= College.objects.all()
    if request.user != repository.author:
        return HttpResponse('Your are not Allowed here...!!')
        
    if request.method == 'POST':
        college_name=request.POST.get('college')
        college, created = College.objects.get_or_create(name= college_name)
        repository.title=request.POST.get('title')
        repository.college=college
        repository.description=request.POST.get('description')
        repository.save()
        
        return redirect('home')
    
    context = {'form' : form, 'colleges':colleges}
    return render(request, 'srbase/repository_form.html', context)

@login_required(login_url='login')
def deleteRepository(request, pk):
    repository= Repository.objects.get(id =pk)
    
    if request.user != repository.author:
        return HttpResponse('Your are not Allowed here...!!')
    
    if request.method == 'POST':
        repository.delete()
        return redirect('home')
    return render(request, 'srbase/delete.html', {'obj':repository})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form= UserForm(instance =user)
    if request.method == 'POST':
        form= UserForm(request.POST,  instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    
    context= {'form' : form}
    return render(request, 'srbase/update-user.html', context)

def submitPage(request):
    message = request.POST.get('message','')
    subject = request.POST.get('subject','')
    mail_id = request.POST.get('email','')
    email = EmailMultiAlternatives(subject,message,'sitangwesa6@gmail.com', [mail_id])
    email.content_subtype = 'html'

    file = request.FILES.get('file')   
    # email.attach(file.name,file.read()

    email.send()
    return redirect('home')


def submit(request):
    return render(request,'srbase/submit.html')


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'])
            return redirect(request, 'srbase/create-repository.html')
    else:
        form = UploadFileForm()
    return render(request, 'srbase/upload.html', {'form': form})

class FileFieldFormView(FormView):
    form_class = FileFieldForm
    template_name = 'srbase/upload.html'  # Replace with your template.
    success_url = 'create-repository'  # Replace with your URL or reverse().

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            for f in files:
                ...  # Do something with each file.
            return self.form_valid(form)
        else:
            return self.form_invalid(form)