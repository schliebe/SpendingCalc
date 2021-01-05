from telegram.ext import Updater
from DB import DB


def load_config():
    """Load data out of the config file and return as a dict.

    :return: dict with keys and values in the config file
    """
    config = {'Telegram_Bot_Token': None}
    with open('config.txt') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            config[key] = value
    return config


def main():
    # Daten aus Config-Datei laden
    config = load_config()

    # Bot erstellen und Token festlegen
    updater = Updater(token=config['Telegram_Bot_Token'])
    dispatcher = updater.dispatcher

    # Verbindung zur Datenbank herstellen
    db = DB('SpendingCalcData.db')

    # Bot starten
    updater.start_polling()
    print('Bot started!')
    updater.idle()


if __name__ == '__main__':
    main()
