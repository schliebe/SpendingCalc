# SpendingCalc
Telegram-Bot der Ausgaben speichern, anzeigen und zusammenrechnen kann.

## Installation
Um den SpendingCalc Telegram-Bot nutzen zu können sind ein paar Schritte notwendig.\
Zuerst muss sichergestellt sien, dass [Python3](https://www.python.org/downloads/ "Download Python")
auf dem System installiert ist. Der Code wurde auf der Version `3.7.7` entwickelt und getestet.

#### Virtual Environment erstellen
Zuerst muss ein [Virtual Environment](https://docs.python.org/3/tutorial/venv.html "Dokumentation zu Virtual Environments")
erstellt werden, in dem die benötigten Packages aus der `requirements.txt`
installiert werden. Hierzu muss folgendes im heruntergeladenen Verzeichnis in
der Kommandozeile eingegeben werden:\
*Virtual Environment mit Namen `venv` erstellen:*
```shell
$ python -m venv ./venv
```
*Virtual Environment aktivieren:*\
In Windows:
```shell
$ venv\Scripts\activate.bat
```
In Unix oder MacOS:
```shell
$ source venv/bin/activate
```
*Pakete aus `requirements.txt` installieren:*
```shell
$ python -m pip install -r requirements.txt
```

#### Bot Konfigurieren
Um den Bot nutzen zu können muss dieser zuerst registriert werden. Hierzu muss
der Telegram-Bot [@BotFather](https://t.me/botfather "@BotFather") genutzt werden
um einen neuen Bot zu erstellen über den der SpendingCalc Bot erreichbar sein soll.\
Der hierbei erhaltene Access Token muss in der `config.txt` bei `Telegram_Bot_Token`
anstelle von `TOKEN` eingefügt werden.

#### Bot starten
Wurden alle Pakete installiert und Konfigurationen eingestellt muss zunächst
[wie zuvor](#virtual-environment-erstellen) das Virtual Environment aktiviert werden.\
*Der Bot lässt sich nun in der Kommandozeile starten:*
```shell
$ python -m SpendingCalc
```
Eine Meldung bestätigt, dass der Bot gestartet ist. Über den bei der Registrierung
angegebenen Namen kann der Bot nun genutzt werden.\
Der Bot kann durch drücken von Strg+C gestoppt werden.
