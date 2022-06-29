from django.shortcuts import render


def index(request):
    print("ahhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
    return render(request,'index.html')
    #return HttpResponse()