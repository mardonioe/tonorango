#!/usr/bin/env python

import os, pymongo, json, hashlib, bson
from bson.json_util import dumps as mongo_dumps
from bottle import Bottle, request, response, HTTPResponse

from functools import wraps

from datetime import datetime, timedelta

import jwt
from jwt.exceptions import DecodeError, ExpiredSignature

from db import get_database_connection

application = Bottle()
auth_app = application

token_timeout = 15 # minutes
jwt_algorithm = 'HS256'

user = None 

try:
	# you may not commit secret_key.txt
	auth_app.config['SECRET_KEY'] = open('secret_key.txt', 'rb').read()
except IOError:
	import random
	auth_app.config['SECRET_KEY'] = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
	secret = open('secret_key.txt', 'w')
	secret.write(auth_app.config['SECRET_KEY'])
	secret.close()



# decorator that makes an endpoint require a valid jwt token
def jwt_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not request.headers.get('Authorization'):
			return HTTPResponse(status=401, body="Token nao enviado.")
		try:
			payload = parse_token(request)
		except DecodeError:
			return HTTPResponse(status=401, body="Token invalido.")
		except ExpiredSignature:
			return HTTPResponse(status=401, body="Token expirado.")
		return f(user, *args, **kwargs)
	return decorated_function

# decorator that makes an endpoint require a valid jwt token and user be admin
def admin_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not request.headers.get('Authorization'):
			return HTTPResponse(status=401, body="Token nao enviado.")
		try:
			payload = parse_token(request)
			user = payload['sub']			
			if not user['is_admin']:
				return HTTPResponse(status=401, body="Usuario nao e admin.")
		except DecodeError:
			return HTTPResponse(status=401, body="Token invalido.")
		except ExpiredSignature:
			return HTTPResponse(status=401, body="Token expirado.")
		return f(user, *args, **kwargs)
	return decorated_function


# validate user and password agains users 'database'
def authenticate(email, pwd):
	db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
	user = db.users.find_one({'email': email}) # find_one retorna um documento, ou None
	if user:
		if user['password'] == hashlib.md5(pwd.encode()).hexdigest():
			return create_token(user)
	return False


# creates a jwt token loaded with user data
def create_token(user):
	payload = {
		# subject
		'sub': {'email': user['email'], 'is_admin': user.get('is_admin', False)},
		# issued at
		'iat': datetime.utcnow(),
		# expiry
		'exp': datetime.utcnow() + timedelta(minutes=token_timeout)
	}
	token = jwt.encode(payload, auth_app.config['SECRET_KEY'], algorithm=jwt_algorithm)
	return token.decode('unicode_escape')


def parse_token(req):
	token = req.headers.get('Authorization').split()[1]
	return jwt.decode(token, auth_app.config['SECRET_KEY'], algorithms=jwt_algorithm)
