from bottle import Bottle

import pymongo

mongodb_host = None
mongodb_db_name = None

try:
	dummy = os.environ['OPENSHIFT_HOMEDIR']
	mongodb_host = os.environ['OPENSHIFT_MONGODB_DB_URL']
	mongodb_db_name = os.environ['OPENSHIFT_APP_NAME']
except:    
	mongodb_host = 'mongodb://localhost:27017'
	mongodb_db_name = 'tonorango'


# retornar conexao de base de dados mongodb
def get_database_connection():
	conn = pymongo.MongoClient(mongodb_host)
	return conn[mongodb_db_name]
