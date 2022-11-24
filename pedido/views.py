from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import Pedido, ItemPedido, CupomDesconto
from produtos.models import Produto, Categoria
import json
import math
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.contrib.messages import constants



@csrf_exempt
def finalizar_pedido(request):
    if request.method == "GET":
        categorias = Categoria.objects.all()
        
        if len(request.session['carrinho']) == 0:
            messages.add_message(request, constants.WARNING, 'Escolha no mínimo 1 item para finalizar um pedido.')
            return redirect('home')
        total = sum([float(i['preco']) for i in request.session['carrinho']])
        return render(request, 'finalizar_pedido.html', {'carrinho': len(request.session['carrinho']),
                                                        'categorias': categorias,
                                                        'total': total,
                                                        })
    else:
        if len(request.session['carrinho']) > 0:
            x = request.POST
            total = sum([float(i['preco']) for i in request.session['carrinho']])
            cupom = CupomDesconto.objects.filter(codigo=x['cupom'])
            cupom_salvar = None
            if len(cupom) > 0 and cupom[0].ativo:
                total = total - ((total*cupom[0].desconto)/100)
                cupom[0].usos += 1
                cupom[0].save()
                cupom_salvar = cupom[0]

            carrinho = request.session.get('carrinho')
            
            listaCarrinho = []
            for i in carrinho:
                listaCarrinho.append({
                    'produto': Produto.objects.filter(id = i['id_produto'])[0],
                    'observacoes': i['observacoes'],
                    'preco': i['preco'],
                    'adicionais': i['adicionais'],
                    'quantidade': i['quantidade'],
                })
            
            

            lambda_func_troco = lambda x: int(x['troco_para'])-total if not x['troco_para'] == '' else ""
            lambda_func_pagamento = lambda x: 'Cartão' if x['meio_pagamento'] == '2' else 'Dinheiro'
            pedido = Pedido(usuario=x['nome'],
                            total = total,
                            troco = lambda_func_troco(x),
                            cupom = cupom_salvar,
                            pagamento = lambda_func_pagamento(x),
                            ponto_referencia = x['pt_referencia'],
                            cep = x['cep'],
                            rua = x['rua'],
                            numero = x['numero'],
                            bairro = x['bairro'],
                            telefone = x['telefone'],
                            )
            pedido.save()
            
            ItemPedido.objects.bulk_create(
                ItemPedido(
                    pedido = pedido,
                    produto = v['produto'],
                    quantidade = v['quantidade'],
                    preco = v['preco'],
                    adicionais = str(v['adicionais'])
                ) for v in listaCarrinho


            )
        
            request.session['carrinho'].clear()
            request.session.save()
            return render(request, 'pedido_realizado.html')
        else:
            return redirect('http://127.0.0.1:8000/?erro=1')

def validaCupom(request):
    cupom = request.POST.get('cupom')
  
    cupom = CupomDesconto.objects.filter(codigo = cupom)
    if len(cupom) > 0 and cupom[0].ativo:
        desconto = cupom[0].desconto
        total = sum([float(i['preco']) for i in request.session['carrinho']])
        total_com_desconto = float( math.floor( total - ((total*desconto)/100)))
        data_json = json.dumps({'status': 0,
                                'desconto': desconto,
                                'total_com_desconto': str(total_com_desconto).replace('.', ',')

                                })
        return HttpResponse(data_json)
    else:
        return HttpResponse(json.dumps({'status': 1}))



stripe.api_key = settings.STRIPE_SECRET_KEY
@csrf_exempt
def create_payment_intent(request):

    stripe.api_key = settings.STRIPE_SECRET_KEY
    email = json.loads(request.body)['email']
    print(email)
    total = sum([int(i['preco']) for i in request.session['carrinho']])
    intent = stripe.PaymentIntent.create(
        amount= total,
        currency='BRL',

    )

    
    return JsonResponse({
        'clientSecret': intent['client_secret']
    })




def sucesso(request):
    return render(request, 'pedido_realizado.html')


def form_payment(request):

    STRIPE_PUBLIC_KEY = settings.STRIPE_PUBLIC_KEY

    categorias = Categoria.objects.all()

    total = sum([int(i['preco']) for i in request.session['carrinho']])

    carrinho = [i for i in request.session['carrinho']]
    
    quantidade = []
    nome_produto = []
    for i in carrinho:

        produto = Produto.objects.get(id=i['id_produto'])

        nome_produto.append(produto.nome_produto)

        quantidade.append(i['quantidade'])

     

    var = {
        
    }

    
    return render(request, 'form-payment.html', {'STRIPE_PUBLIC_KEY':STRIPE_PUBLIC_KEY, 
                                                'categorias':categorias,
                                                 'total':total, 'carrinho': len(carrinho),
                                                  'nome_produto': nome_produto,
                                                  })

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
        payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)


    if event['type'] == 'charge.succeeded':
        session = event['data']['object']
     

        return HttpResponse(status=200)

@csrf_exempt
def clear_carrinho(request):
    request.session['carrinho'].clear()
    request.session.save()
    return JsonResponse({'status': 'apagado'}) 