# Visualisation des Données

Ce projet met en œuvre une chaîne complète de collecte et visualisation de données environnementales telles que la température, l'humidité et la luminosité, qui sont recueillies par des capteurs. Elles sont ensuite transmises à The Things Network (TTN), extraites via un broker MQTT, traitées et stockées dans une base de données MongoDB. Enfin, elles sont présentées à travers une interface web dynamique qui évolue en temps réel. 

## Architecture du Système

![diag drawio](https://github.com/ibra-mboula/IOT-LoRa-LoRaWAN/assets/78673312/f0572552-5ee2-4983-9ea4-94acb3555d19)

Le diagramme ci-dessus décrit le flux de données à travers les différents composants du système.

## Flux de Données

1. **Collecte de Données**: Les capteurs recueillent les données environnementales et les envoient à la passerelle TTN via LoRaWAN.
2. **Passerelle TTN**: La passerelle reçoit les données et les transmet au cloud TTN.
3. **Cloud TTN**: Les données sont accessibles via le cloud TTN.
4. **Broker MQTT**: Un client MQTT est configuré pour s'abonner à tous les topics concernés pour récupérer les données.
5. **Traitement des Données**: Les données récupérées sont traitées et formatées selon les besoins.
6. **Stockage MongoDB**: Les données traitées sont injectées dans une base de données MongoDB pour le stockage.
7. **Visualisation Web**: Une application web Flask récupère les données de MongoDB et les visualise sous forme de graphiques interactifs.

## Technologies Utilisées

- Capteurs: Arduino MKRWAN1300, STM32 WL55JC1
- Communication: LoRaWAN, MQTT via The Things Network
- Backend: Flask
- Base de données: MongoDB
- Visualisation: Bibliothèques JavaScript pour les graphiques ---> chart.js
  
  ![viz-30-20](https://github.com/ibra-mboula/IOT-LoRa-LoRaWAN/assets/78673312/6d3c70f1-a6d3-4c86-9f62-6f71820e7f0f)

  ![viz-arduino-20](https://github.com/ibra-mboula/IOT-LoRa-LoRaWAN/assets/78673312/b1c18b9f-ef73-4fd8-9687-b9af80d04e30)
