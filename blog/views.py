from django.shortcuts import render
# this file is created by - yogesh
from django.http import HttpResponse
from .models import Blogpost

def index(request):
    myposts = Blogpost.objects.all()
    return render(request,'blog/index.html',{"myposts":myposts})

def blogpost(request, id):
    post = Blogpost.objects.filter(post_id = id)[0]
    return render(request,'blog/blogpost.html',{'post':post})