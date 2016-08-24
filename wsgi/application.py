#!/usr/bin/env python

import os, pymongo, json, hashlib, bson
from bson.json_util import dumps as mongo_dumps
from bottle import Bottle, request, response, HTTPResponse

from db import get_database_connection

from auth import auth_app, jwt_required, admin_required, authenticate

application = Bottle()
app = application
app.merge(auth_app)

user = None


# atender requisicoes do tipo get para /
@app.get('/')
def index():
    return "Boa sorte!"


@app.get('/mardonio')
def index():
    return "Boa sorte Mardonio!"


# atender requisicoes do tipo post para /api/v1/signin
# curl -H "Content-Type: application/json" -X POST -d '{"email":"scott@gmail.com", "password":"12345"}' http://localhost:8080/api/v1/signin
@app.post('/api/v1/signin')
def login():
    data = request.json
    encoded = authenticate(data['email'], data['password'])
    if encoded:
        return encoded
    else:
        return HTTPResponse(status=401, body="Nao autorizado.")


# atender requisicoes do tipo post para /api/v1/users/create
# curl -i -H "Content-Type: application/json" -X POST -d '{"name": "Eduardo", "email": "xyz@gmail", "password":"xyz"}' http://localhost:8080/api/v1/users/create
@app.post('/api/v1/users/create')
def create_user():
    response.content_type = 'application/json'
    data = request.json
    name = data["name"]  # obtem nome enviado por parametro postado.
    email = data["email"]  # obtem email enviado por parametro postado.
    password = hashlib.md5(data["password"].encode()).hexdigest()  # obtem hash md5 da senha enviada.
    db = get_database_connection()  # conecta com a base de dados e armazena a conexao em db.
    user = db.users.find_one({'email': email})  # find_one retorna um documento,
    # ou None se nao encontrar nenhum.
    if user:
        # usuario ja existe. retornar em formato JSON padrao com mensagem.
        # return mongo_dumps(user)
        return json.dumps({'success': True, 'msg': 'usuario ja existente.', "user": json.dump(user)})
    else:
        # usuario nao existe. inserir novo usuario.
        user = db.users.insert({'name': name, 'email': email, 'password': password})
        # retornar em formato JSON padrao com mensagem.
        return json.dumps({'success': True, 'msg': 'usuario cadastrado.'})


@app.post('/api/v1/admin/menu/sesions/create')
def create_session():
    response.content_type = 'application/json'
    data = request.json
    name = data["name"]
    db = get_database_connection()  # conecta com a base de dados e armazena a conexao em db.
    session = db.sessions.find_one({'name': name})
    if session:
        return json.dumps({'success': False, 'msg': 'Sessão já cadastrada.'})
    else:
        session = db.sessions.insert(data)
        return json.dumps({'success': True, 'msg': 'Sessão cadastrada com sucesso!'})


@app.post('/api/v1/admin/menu/items/create')
def create_item():
    response.content_type = 'application/json'
    data = request.json
    name = data["name"]
    preco = int(data["preco"])
    sessao = data["sessao"]
    db = get_database_connection()
    session = db.sessions.find_one({'name': sessao})
    if not session:
        return json.dumps({'success': False, 'msg': 'Não existe sessão com este nome cadastrada!'})

    if not name:
        return json.dumps({'success': False, 'msg': 'Nome do item não pode ser nulo!'})

    if preco == 0.0 or not preco or not isNumeber(preco):
        return json.dumps({'success': False, 'msg': 'Preço do item não pode ser nulo ou zerado!'})

    itens = db.itens.find_one({'name': name})
    if itens:
        return json.dumps({'success': False, 'msg': 'Item já cadastrado.'})
    else:
        itens = db.itens.insert(data)
        return json.dumps({'success': True, 'msg': 'Item cadastrado com sucesso!'})

# cria um novo pedido.
@app.get('/user/<userId>/orders/create')
def create_order_user(userId):
    response.content_type = 'application/json'
    itens = request.json
    db = get_database_connection()  # conecta com a base de dados e armazena a conexao em db.
    user = db.users.find_one({'_id': userId})  # find_one retorna um documento,

    valorPedido = 0

    if user:
        """
        fazer uma iteração no objeto "itens" que contém a lista dos itens do pedido
        para fazer o cálculo do valor total do pedido
        OBS: VERIFICAR A SINTAXE
        """
        for item in itens:
            session = db.sessions.find_one({'name': item['sessao']})
            if not session:
                return json.dumps({'success': False, 'msg': 'Existem itens com sessão ainda não cadastrada.'})

            itemDb = db.itens.find_one({'name': item['nome']})
            if not itemDb:
                return json.dumps({'success': False, 'msg': 'Existem itens ainda não cadastrados.'})

            valorPedido += float(item['preco'])

        db.orders.insert({'usuarioId': userId, 'data': datetime.now(), 'valorTotal': valorPedido, 'itens': itens})

        return json.dumps({'success': True, 'msg': 'Pedido cadastrado.'})
    else:
        return json.dumps({'success': False, 'msg': 'Usuário não cadastrado.'})

# retorna lista de pedidos de usuário. Para cada pedido, informar apenas data e valor total.
@app.get('/user/<userId>/orders')
def list_orders_user(userId):
    response.content_type = 'application/json'
    db = get_database_connection()  # conecta com a base de dados e armazena a conexao em db.
    orders = db.orders.find({'usuarioId': userId},
                            {'data': True, 'valorTotal': True, 'usuarioId': False, 'itens': False, '_id': False})

    if orders:
        return mongo_dumps(orders)
    else:
        return json.dumps({'success': False, 'msg': 'Não existem pedidos para o usuário informado.'})

# retorna todos os items do pedido
@app.get('/user/<userId>/orders/<orderId>')
def list_details_order_user(userId, orderId):
    response.content_type = 'application/json'
    db = get_database_connection()  # conecta com a base de dados e armazena a conexao em db.

    user = db.users.find_one({'_id': userId})  # find_one retorna um documento,

    if user:
        itens = db.orders.find_one({'$and': [{'_id': orderId, 'usuarioId': userId}]},
                                   {'data': False, 'valorTotal': False, 'usuarioId': False, 'itens': True,
                                    '_id': False})

        if itens:
            return mongo_dumps(itens)
        else:
            return json.dumps({'success': False, 'msg': 'Não existe pedido realizado.'})
    else:
        return json.dumps(
            {'success': False, 'msg': 'Usuário não cadastrado.'})  # atender requisicoes do tipo get para /api/v1/users


# curl -i -H "Content-Type: application/json" -X GET  http://localhost:8080/api/v1/users
@app.get('/api/v1/users')
@jwt_required
def list_user(user):
    response.content_type = 'application/json'
    db = get_database_connection()  # conecta com a base de dados e armazena a conexao em db.
    users = db.users.find()
    return mongo_dumps(users)


@app.get('/api/v1/admin/menu/items')
def get_list_itens():
    response.content_type = 'application/json'
    db = get_database_connection()  # conecta com a base de dados e armazena a conexao em db.
    sessions = db.sessions.find()

    """lista_itens = "{}"""""
    lista_sessoes = "{}"

    for session in sessions:

        itens = db.itens.find({'sessao': session['name']})

        """for item in itens:
            lista_itens += ',{"nome":"' + item['name'] + '","preco":' + float(item['preco']) + '}'"""

        lista_sessoes += ',{"nome":"' + session['name'] + '","itens":[' + itens + ']}'

    if lista_sessoes != "{}":
        return json.dumps('{"sessoes":[' + lista_sessoes[1:] + ']}')
    else:
        return json.dumps({'success': False, 'msg': 'Não existe sessão cadastrada.'})


def isNumeber(value):
    try:
        float(value)
        return True
    except:
        return False


# atender requisicoes do tipo get para /api/v1/admin/users
# curl -i -H "Content-Type: application/json" -X GET  http://localhost:8080/api/v1/admin/users
@app.get('/api/v1/admin/users')
@admin_required
def list_user_from_admin(user):
    response.content_type = 'application/json'
    db = get_database_connection()  # conecta com a base de dados e armazena a conexao em db.
    users = db.users.find()
    return mongo_dumps(users)
