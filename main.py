import requests
from bs4 import BeautifulSoup
import json
import sqlite3
from datetime import datetime
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "TU_TOKEN_AQUI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "TU_CHAT_ID")

def init_db():
    conn = sqlite3.connect('precios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS productos
                 (id INTEGER PRIMARY KEY, nombre TEXT, url TEXT,
                  precio_actual REAL, precio_objetivo REAL, ultima_revision TEXT)''')
    conn.commit()
    conn.close()

def scrapear_mercadolibre(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser')
    try:
        precio = soup.find('span', {'class': 'andes-money-amount__fraction'}).text
        precio = float(precio.replace(',', ''))
        nombre = soup.find('h1', {'class': 'ui-pdp-title'}).text
        return nombre.strip(), precio
    except:
        return None, None

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def revisar_precios():
    with open('productos.json', 'r') as f:
        productos = json.load(f)
    conn = sqlite3.connect('precios.db')
    c = conn.cursor()
    for producto in productos:
        nombre, precio = scrapear_mercadolibre(producto['url'])
        if precio and precio <= producto['precio_objetivo']:
            mensaje = f"🔥 *OFERTA DETECTADA* 🔥\n\n*{nombre}*\n\n💰 Precio actual: ${precio:,.2f}\n🎯 Tu objetivo: ${producto['precio_objetivo']:,.2f}\n\n🔗 {producto['url']}"
            enviar_telegram(mensaje)
            print(f"Alerta enviada: {nombre}")
        c.execute("INSERT OR REPLACE INTO productos VALUES (?,?,?,?,?,?)",
                 (producto['id'], nombre, producto['url'], precio,
                  producto['precio_objetivo'], datetime.now()))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    revisar_precios()
    print("Revisión completada")
