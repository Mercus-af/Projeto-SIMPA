"""Entrada do servidor. Execute na raiz: python app.py."""
import os
from simpa.app import app,criar_app

if __name__=='__main__':
    app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=False)
