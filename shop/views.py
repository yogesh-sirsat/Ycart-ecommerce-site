from django.shortcuts import render, redirect, HttpResponse
# this file is created by - yogesh
from django.http import HttpResponse
from .models import Product, Contact, Orders, OrderUpdate
from math import ceil
from django.contrib import messages
import json
from django.views.decorators.csrf import csrf_exempt
from PayTm import Checksum
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
MERCHANT_KEY = 'Ix!KhL#IMW!2jdzl'

def index(request):
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
        
    params = {'allProds':allProds}
    return render(request, 'shop/index.html', params)

def about(request):
    return render(request, 'shop/about.html')

def contact(request):
    thank = False
    if request.method=="POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        thank = True
    if thank:
        messages.success(request, 'Thanks For Contacting Us...')
    return render(request, 'shop/contact.html',{'thank': thank})

def tracker(request):
    if request.method=="POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps({"status" : "success", "updates" : updates, "itemJson" : order[0].items_json}, default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status" : "noitem"}')
        except Exception as e:
            return HttpResponse('{"status" : "error"}')

    return render(request, 'shop/tracker.html')

def searchMatch(query, item):
    if query.lower() in item.product_name.lower() or query.lower() in item.desc.lower() or query.lower() in item.category.lower():
        return True
    else:
        return False
def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])
        
    params = {'allProds':allProds}
    if len(allProds) == 0 or len(query)<4:
        params = {'msg': "Please make sure to enter relevant search query"}
    
    return render(request, 'shop/search.html', params)

def productView(request, myid):
    # Fetch the product using the id
    product = Product.objects.filter(id=myid)


    return render(request, 'shop/prodView.html', {'product':product[0]})

def checkout(request):
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        amount = request.POST.get('amount','')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json, name=name, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone,amount=amount)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank = True
        id = order.order_id
        param_dict = {

                'MID': 'iUVRxp12822049217524',
                'ORDER_ID': str(order.order_id),
                'TXN_AMOUNT': str(amount),
                'CUST_ID': email,
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'WEBSTAGING',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',

        }
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
        return render(request, 'shop/paytm.html', {'param_dict': param_dict})
    return render(request, 'shop/checkout.html')

@csrf_exempt
def handlerequest(request):
    # paytm will send you post request here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]

    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print('order successful')
        else:
            print('order was not successful because' + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})

def handlesignup(request):
    if request.method == 'POST':
        # get the post parameters
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        liemail = request.POST['liemail']
        password = request.POST['password']
        cpassword = request.POST['cpassword']
        # logic
        if password != cpassword:
            messages.warning(request, 'Your confirm password not matched with password')
            return redirect('ShopHome')
        # create the user
        myuser = User.objects.create_user(username, liemail, password)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.save()
        messages.success(request, 'Your account has been created successfully')
        return redirect('ShopHome')
    else:
        return HttpResponse('404 - page not found')

def handlelogin(request):
    if request.method == 'POST':
        # get the post parameters
        loginusername = request.POST['loginusername']
        loginpassword = request.POST['loginpassword']

        user = authenticate(username=loginusername, password=loginpassword)
        if user is not None:
            login(request, user)
            messages.success(request, 'You successfully logged in')
            return redirect('ShopHome')
        else:
            messages.warning(request," You did't entered correct credentials ")
            return redirect('ShopHome')
    return HttpResponse('404 - page not found')

def handlelogout(request):
    logout(request)
    messages.success(request, 'You successfully logged out')
    return redirect('ShopHome')