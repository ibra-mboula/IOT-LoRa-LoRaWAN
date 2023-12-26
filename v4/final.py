from flask import Flask, jsonify
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import json
import threading
import datetime
import time
import pymongo


app = Flask(__name__)

def remove_duplicates(collection):
    unique_ids = set()
    duplicates = []

    for document in collection.find({}):
        unique_id = document['unique_id']
        if unique_id in unique_ids:
            duplicates.append(document['_id'])
        else:
            unique_ids.add(unique_id)

    for dup_id in duplicates:
        collection.delete_one({'_id': dup_id})
    print(f"Supprimé {len(duplicates)} doublons dans la collection.")



# Connexion à MongoDB
client_mongo = MongoClient('mongodb://localhost:27017/')
db = client_mongo['db']
collection_arduino = db['arduino']
collection_stm = db['stm']

# Nettoyez les doublons avant de créer l'index
remove_duplicates(collection_stm)
remove_duplicates(collection_arduino)


# Créez un index unique pour empêcher les insertions de doublons.
collection_arduino.create_index([("unique_id", pymongo.ASCENDING)], unique=True) #ASCENDING pour trier par ordre croissant , unique pour ne pas avoir de doublons
collection_stm.create_index([("unique_id", pymongo.ASCENDING)], unique=True)


# Identifiants MQTT pour TTN
app_id = "lora-app-747"
app_key = "NNSXS.34NDIYEZEBOVH6S6GHXKJUKSMDAVW4AAFIP4DOI.WZGFR2JLY3X4QHGINW7ZUXZ3NLYQ5QGXSG46W4PNEATCNYYNWDJA"

# Fonction callback pour la réception des messages MQTT
def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode("utf-8"))
    time_received = payload["received_at"]
    brand_id = payload["uplink_message"]["version_ids"]["brand_id"]
    decoded_payload = payload["uplink_message"]["decoded_payload"]

    time_obj = datetime.datetime.fromisoformat(time_received.rstrip('Z'))
    formatted_date = time_obj.strftime("%Y-%m-%d")
    formatted_time = time_obj.strftime("%H:%M:%S")

    unique_id = formatted_date + 'T' + formatted_time

    if brand_id == "stmicroelectronics":
        data = process_stm_payload(decoded_payload)
    elif brand_id == "arduino":
        data = process_arduino_payload(decoded_payload)
    else:
        print("Type de noeud inconnu")
        return

    data["unique_id"] = unique_id
    data["date"] = formatted_date
    data["time"] = formatted_time

    # Gestion des doublons : suppression du doublon existant
    try:
        if brand_id == "stmicroelectronics":
            collection_stm.delete_one({"unique_id": unique_id})
            collection_stm.insert_one(data)
        elif brand_id == "arduino":
            collection_arduino.delete_one({"unique_id": unique_id})
            collection_arduino.insert_one(data)
    except pymongo.errors.DuplicateKeyError:
        print(f"Erreur lors de l'insertion du document avec unique_id {unique_id}.")



# Configuration du client MQTT
client = mqtt.Client()
client.username_pw_set(app_id, app_key)
client.on_message = on_message # sert a appeler la fonction on_message
client.connect("eu1.cloud.thethings.network", 1883, 60)
client.subscribe("#")

mqtt_thread = threading.Thread(target=client.loop_start)
mqtt_thread.daemon = True
mqtt_thread.start()

#!=================================================================

#conversion de la résistance en humidité
def R_humidity(Resistor,Temperature):

    Humidity=0
    temp_range = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    Humidity_range = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90]
    new_values = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    
   
    Tinf=Temperature-(Temperature%5)
    Tsup=Temperature+(5-(Temperature%5))
    incInf=int(Tinf/5)
    incSup=int(Tsup/5)
   
    k=((Temperature%5)/5)
    
    RTH = [
        [0,    0,    12000, 5200,  2800,  720,  384,  200,  108,  64,   38,   23,   16,   10.2, 6.9],
        [0,    19800, 9800,  4700,  2000,  510,  271,  149,  82,   48,   29,   18,   12,   8.2,  5.4],
        [0,    16000, 7200,  3200,  1400,  386,  211,  118,  64,   38,   24,   15,   10.2, 6.9,  4.7],
        [21000, 10500, 5100,  2350,  1050,  287,  159,  91,   51,   31,   19,   12,   8.1,  5.5,  4.1],
        [13500, 6700,  3300,  1800,  840,   216,  123,  70,   40,   25,   16,   10,   7.2,  4.7,  3.2],
        [9800,  4803,  2500,  1300,  630,   166,  95,   55,   31,   20,   13,   8.5,  5.7,  4],
        [8000,  3900,  2000,  980,   470,   131,  77,   44,   25,   17,   10.5, 7.2,  5,    3.6,  2.5],
        [6300,  3100,  1500,  750,   385,   104,  63,   38,   21,   13,   9,    6.4,  4.4,  3.2],
        [4600,  2300,  1100,  575,   282,   80,   52,   32,   17,   11,   8.2,  5.8,  4,    2.9,  2.1],
        [3800,  1850,  900,   430,   210,   66,   45,   30,   14,   11,   7.1,  5,    3.3,  2.4,  1.8],
        [3200,  1550,  750,   350,   170,   51,   38,   24,   12,   9,    6,    4.1,  2.9,  2,    1.5]
    ]
   
    for i in range(len(new_values)-1):
        new_values[i]=RTH[incInf][i]-(k*abs(RTH[incSup][i]-RTH[incInf][i]))
   
    for i in reversed(range(len(new_values)-1)):
        if(Resistor<=new_values[i]):
            ecart = (Resistor-new_values[i+1])/abs(new_values[i]-new_values[i+1])
            Humidity=Humidity_range[i+1]-(5*ecart)
            break
        
    return Humidity
   


def process_stm_payload(payload):
    print("++++++ Traitement Payload STM ++++++")
    resistor = payload["humidity"]["value"]/10  # Obtenir la valeur de résistance
    print("Résistance STM:", resistor)
    temperature_value = payload["temperature"]["value"]  # Obtenir la valeur de la température
    print("Température STM:", temperature_value)

    # Calcul de l'humidité à partir de la résistance et de la température
    calculated_humidity = R_humidity(resistor, temperature_value)
    print("Humidité Calculée STM:", calculated_humidity)

    return {
        "humidity": calculated_humidity,  # Utilisation de l'humidité calculée
        "light": payload["lightMich"]["value"],
        "temperature": temperature_value
    }
    
def process_arduino_payload(payload):
    print("------ Traitement Payload Arduino ------")
    resistor = payload["humidity"]/10
    print("Résistance Arduino:", resistor)
    temperature_value = payload["temperature"]
    print("Température Arduino:", temperature_value)

    # Calcul de l'humidité à partir de la résistance et de la température
    calculated_humidity = R_humidity(resistor, temperature_value)
    print("Humidité Calculée Arduino:", calculated_humidity)

    return {
        "humidity": calculated_humidity,  # Utilisation de l'humidité calculée
        "light": payload["light"],
        "temperature": temperature_value
    }




# Fonction qui mAJ la db toutes les 10 secondes
def update_db_every_10_seconds():
    while True:
        print("Mise à jour de la base de données toutes les 10 secondes")
        time.sleep(10)

db_update_thread = threading.Thread(target=update_db_every_10_seconds)
db_update_thread.daemon = True
db_update_thread.start()

#!==============================ROUTE====================================

@app.route('/data')
def data():
    arduino_data = list(collection_arduino.find({}, {'_id': 0}))
    stm_data = list(collection_stm.find({}, {'_id': 0}))
    combined_data = {'arduino': arduino_data, 'stm': stm_data}
    
    return jsonify(combined_data)

@app.route('/data/stm/last/<int:count>')
def last_stm_measures(count):
    stm_data = list(collection_stm.find({}, {'_id': 0}).sort('_id', -1).limit(count))
    return jsonify(stm_data)

@app.route('/data/arduino/last/<int:count>')
def last_arduino_measures(count):
    try:
        arduino_data = list(collection_arduino.find({}, {'_id': 0}).sort('_id', -1).limit(count))
        return jsonify(arduino_data)
    except Exception as e:
        print(f"Error retrieving last {count} Arduino measures: {e}")
        return jsonify({"error": "Error retrieving data"}), 500

@app.route('/data/arduino/date/<date>')
def data_for_arduino_date(date):
    try:
        # Convertir la chaîne de date en objet datetime
        start = datetime.datetime.strptime(date, '%Y-%m-%d')
        end = start + datetime.timedelta(days=1)
        
        # Trouver les données entre le début et la fin de la date sélectionnée
        arduino_data = list(collection_arduino.find({
            "date": {
                "$gte": start.strftime('%Y-%m-%d'),
                "$lt": end.strftime('%Y-%m-%d')
            }
        }, {'_id': 0}).sort([('time', pymongo.ASCENDING)]))
        
        return jsonify(arduino_data)
    except Exception as e:
        print(f"Error retrieving data for date {date}: {e}")
        return jsonify({"error": "Error retrieving data"}), 500


@app.route('/data/stm/date/<date>')
def data_for_date(date):
    try:
        # Convertir la chaîne de date en objet datetime
        start = datetime.datetime.strptime(date, '%Y-%m-%d')
        end = start + datetime.timedelta(days=1)
        
        # Trouver les données entre le début et la fin de la date sélectionnée
        stm_data = list(collection_stm.find({
            "date": {
                "$gte": start.strftime('%Y-%m-%d'),
                "$lt": end.strftime('%Y-%m-%d')
            }
        }, {'_id': 0}).sort([('time', pymongo.ASCENDING)]))
        
        return jsonify(stm_data)
    except Exception as e:
        print(f"Error retrieving data for date {date}: {e}")
        return jsonify({"error": "Error retrieving data"}), 500


@app.route('/humidity')
def humidity_page():
    return app.send_static_file('humidity.html')


@app.route('/humidity/data/stm/last/<int:count>')
def last_stm_humidity_measures(count):
    stm_data = list(collection_stm.find({}, {'_id': 0}).sort('_id', -1).limit(count))
    return jsonify(stm_data)

@app.route('/light')
def light_page():
    return app.send_static_file('light.html')

@app.route('/light/data/stm/last/<int:count>')
def last_stm_light_measures(count):
    stm_data = list(collection_stm.find({}, {'_id': 0}).sort('_id', -1).limit(count))
    return jsonify(stm_data)

@app.route('/data/light/combined')
def combined_light_data():
    arduino_data = list(collection_arduino.find({}, {'_id': 0, 'light': 1, 'timestamp': 1}))
    stm_data = list(collection_stm.find({}, {'_id': 0, 'light': 1, 'timestamp': 1}))
    combined_data = {'arduino': arduino_data, 'stm': stm_data}
    return jsonify(combined_data)


@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)
