from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Produto, Categoria, Opcoes, Adicional
from django.http import JsonResponse
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404


def home(request):
    if not request.session.get('carrinho'):
        request.session['carrinho'] = []
        request.session.save()
    
    if request.method != 'GET':
        return Http404()
    

    produtos = Produto.objects.all()
  
    categorias = Categoria.objects.all()
    return render(request, 'home.html', {'produtos': produtos,
                                        'carrinho': len(request.session['carrinho']),
                                        'categorias': categorias,
                                     
                                        })


def categorias(request, id):
    if not request.session.get('carrinho'):
        request.session['carrinho'] = []
        request.session.save()
    produtos = Produto.objects.filter(categoria__id=id)
    categorias = Categoria.objects.all()
    carrinho = request.session['carrinho']
    return render(request, 'home.html', {'produtos':produtos,
                                         'categorias': categorias,
                                         'carrinho': len(carrinho)})
    





def produto(request, id):
    if not request.session.get('carrinho'):
        request.session['carrinho'] = []
        request.session.save()
    erro = request.GET.get('erro')
    produto = Produto.objects.filter(id=id)[0]
    categorias = Categoria.objects.all()
    return render(request, 'produto.html', {'produto': produto, 
                                            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
                                            'carrinho': len(request.session['carrinho']),
                                            'categorias': categorias,
                                            'erro': erro})






def add_carrinho(request):
    if not request.session.get('carrinho'):
        request.session['carrinho'] = []
        request.session.save()

    x = dict(request.POST)

    def removeLixo():
        adicionais = x.copy()
        adicionais.pop('id')
        adicionais.pop('csrfmiddlewaretoken')
        adicionais.pop('observacoes')
        adicionais.pop('quantidade')
        adicionais = list(adicionais.items())

        return adicionais
        
    adicionais = removeLixo()    

    id = int(x['id'][0])
    preco_total = Produto.objects.filter(id=id)[0].preco


    for i, j in adicionais:
        for k in j:
            preco_total += Opcoes.objects.filter(id=int(k))[0].acrecimo



    
    def troca_id_por_nome_adicional():
        adicionais_com_nome = []
        for i in adicionais:
            opcoes = []
            for j in i[1]:
                op = Opcoes.objects.filter(id = int(j))[0].nome
                opcoes.append(op) 
                print(op)
            adicionais_com_nome.append((i[0], opcoes))
        return adicionais_com_nome
    
    adicionais = troca_id_por_nome_adicional()
    
    preco_total *= int(x['quantidade'][0])

    data = {'id_produto': int(x['id'][0]),
            'observacoes': x['observacoes'][0],
            'preco': preco_total,
            'adicionais': adicionais,
            'quantidade': x['quantidade'][0]}

    request.session['carrinho'].append(data)
    request.session.save()
  
    
  
    return redirect('ver_carrinho')

def ver_carrinho(request):
  
    categorias = Categoria.objects.all()
    dados_motrar = []
    for i in request.session['carrinho']:
        prod = Produto.objects.filter(id=i['id_produto'])
        dados_motrar.append(
            {'imagem': prod[0].img.url,
             'nome': prod[0].nome_produto,
             'quantidade': i['quantidade'],
             'preco': i['preco'],
             'id': i['id_produto']
             }
        )
    total = sum([float(i['preco']) for i in request.session['carrinho']])

    return render(request, 'carrinho.html', {'dados': dados_motrar,
                                             'total': total,
                                             'carrinho': len(request.session['carrinho']),
                                             'categorias': categorias,
             

                                             })




def remover_carrinho(request, id):
    request.session['carrinho'].pop(id)
    request.session.save()
    return redirect('ver_carrinho')



stripe.api_key = settings.STRIPE_SECRET_KEY
@csrf_exempt
def create_payment_intent(request):

    stripe.api_key = settings.STRIPE_SECRET_KEY


    produtos = request.session['carrinho']
    intent = stripe.PaymentIntent.create(
  
        currency='BRL',
        

    )

    
    return JsonResponse({
        'clientSecret': intent['client_secret']
    })





def sucesso(request):
    return render(request, 'pedido_realizado.html')



