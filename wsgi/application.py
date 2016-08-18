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
	response.content_type='application/json'
	data = request.json	
	name = data["name"] # obtem nome enviado por parametro postado.
	email = data["email"] # obtem email enviado por parametro postado.
	password = hashlib.md5(data["password"].encode()).hexdigest() # obtem hash md5 da senha enviada.
	db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
	user = db.users.find_one({'email': email}) # find_one retorna um documento, 												
											   # ou None se nao encontrar nenhum.
	if user:
		# usuario ja existe. retornar em formato JSON padrao com mensagem.
		return json.dumps({'success': True, 'msg': 'usuario ja existente.'})
	else:
		# usuario nao existe. inserir novo usuario.
		user = db.users.insert({'name': name, 'email': email, 'password': password})
		# retornar em formato JSON padrao com mensagem.
		return json.dumps({'success': True, 'msg': 'usuario cadastrado.'})

@app.post('/api/v1/admin/menu/sesions/create')
def create_session():
	response.content_type='application/json'
	data = request.json
	name = data["name"]
	db = get_database_connection()  # conecta com a base de dados e armazena a conexao em db.
	session = db.sessions.find_one({'name':name})
	if session:
		return json.dumps({'success': False, 'msg': 'Sessão já cadastrada.'})
	else:
		session = db.sessions.insert(data)
		return json.dumps({'success':True, 'msg':'Sessão cadastrada com sucesso!'})

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


	if preco == 0.0 or not preco or not isNumeber(preco) :
		return json.dumps({'success': False, 'msg': 'Preço do item não pode ser nulo ou zerado!'})


	itens = db.itens.find_one({'name' : name})
	if itens:
		return json.dumps({'success': False, 'msg': 'Item já cadastrado.'})
	else:
		itens = db.itens.insert(data)
		return json.dumps({'success': True, 'msg': 'Item cadastrado com sucesso!'})


# atender requisicoes do tipo get para /api/v1/users
# curl -i -H "Content-Type: application/json" -X GET  http://localhost:8080/api/v1/users
@app.get('/api/v1/users')
@jwt_required
def list_user(user):
	response.content_type='application/json'
	db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
	users = db.users.find()		
	return mongo_dumps(users)

@app.get('/api/v1/admin/menu/items')
def get_list_itens():
	response.content_type='application/json'
	db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
	itens = db.itens.find()
	return mongo_dumps(itens)

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
	response.content_type='application/json'
	db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
	users = db.users.find()		
	return mongo_dumps(users)


