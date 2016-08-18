#!/usr/bin/env python
import imp
import os
import sys

PYCART_DIR = ''.join(['python-', '.'.join(map(str, sys.version_info[:2]))])

LOCAL_ENV = 'local'
OPENSHIFT_ENV = 'openshift'

environ = OPENSHIFT_ENV

try:
   zvirtenv = os.path.join(os.environ['OPENSHIFT_HOMEDIR'], PYCART_DIR,
                           'virtenv', 'bin', 'activate_this.py')
   exec(compile(open(zvirtenv).read(), zvirtenv, 'exec'),
        dict(__file__ = zvirtenv) )
   environ = OPENSHIFT_ENV
except IOError:
   pass
except KeyError:
   environ = LOCAL_ENV
   pass


def run_simple_httpd_server(app, ip, port=8080):
   from wsgiref.simple_server import make_server
   make_server(ip, port, app).serve_forever()


#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
# 


#
#  main():
#
if __name__ == '__main__':   
   zapp = imp.load_source('application', 'wsgi/application.py')

   if environ == OPENSHIFT_ENV:
      ip = os.environ['OPENSHIFT_PYTHON_IP']
   else:
      ip = '127.0.0.1'
   
   port = 8080

   print('Starting WSGIServer on %s:%d ... ' % (ip, port))
   run_simple_httpd_server(zapp.application, ip, port)