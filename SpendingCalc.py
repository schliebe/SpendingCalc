from telegram.ext import Updater, Filters
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from DB import DB
import datetime

# Konstanten für Zustände festlegen
MAIN = 0
ENTER = 10
ENTER_VALUE = 11
ENTER_TAG = 12
ENTER_COMMENT = 13
ANALYSIS = 20
ANALYSIS_TIME = 21

# Verbindung zur Datenbank
db = None

# Zwischenspeicher für Daten
data = {}


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


def register_handlers(dispatcher):
    """Register all handlers for messages send to the bot

    :param dispatcher: The bots dispatcher
    """
    # ConversationHandler hinzufügen
    main_menu_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN: [MessageHandler(Filters.regex('^(Eintragen)$'), enter_menu),
                   MessageHandler(Filters.regex('^(Analyse)$'), analysis_menu)],
            ENTER: [MessageHandler(Filters.regex(r'^-?\d+((\.|,)\d{1,2})?€?$'),
                                   enter_value),
                    MessageHandler(Filters.text, invalid)],
            ENTER_VALUE: [MessageHandler(Filters.text, enter_tag)],
            ENTER_TAG: [MessageHandler(Filters.regex('^(Nein & Speichern)$'),
                                       enter_save),
                        MessageHandler(Filters.regex('^(Ja)$'), enter_comment),
                        MessageHandler(Filters.text, invalid)],
            ENTER_COMMENT: [MessageHandler(Filters.text, enter_save)],
            ANALYSIS: [MessageHandler(Filters.regex('^(Zurück)$'), back),
                       MessageHandler(Filters.regex(
                           '^(7 Tage|30 Tage|Diesen Monat|Dieses Jahr|Alle)$'),
                           analysis_time),
                       MessageHandler(Filters.text, invalid)],
            ANALYSIS_TIME: [MessageHandler(Filters.text, analysis_tag)]
        },
        fallbacks=[],
    )

    dispatcher.add_handler(main_menu_handler)


def start(update, context):
    """Handling after using the /start command

    :param update: Update of the sent message
    :param context: Context of the sent message
    """
    update.message.reply_text(
        'Willkommen beim SpendingCalc Bot!'
    )
    return main_menu(update, context)


def main_menu(update, context):
    """Handling the main menu

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for main menu
    """
    keyboard = [['Eintragen'],
                ['Analyse']]

    update.message.reply_text(
        'Was möchtest du machen?',
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    return MAIN


def enter_menu(update, context):
    """Handling the enter menu

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for enter menu
    """
    update.message.reply_text(
        'Welchen Betrag möchtest du eintragen?',
        reply_markup=ReplyKeyboardRemove()
    )
    return ENTER


def enter_value(update, context):
    """Handling the entered value

    The entered value is in the correct form becuase of the regex in the
    ConversationHandler.

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for value entry
    """
    chat_id = update.effective_chat.id
    message = update.message.text

    # Eingegebenen Wert zu Zahl konvertieren
    value = float(message.strip().replace(',', '.').replace('€', ''))
    data[chat_id] = {'value': value,
                     'comment': None}

    # Tags laden und als Keyboard anzeigen
    tags = db.get_tags(chat_id)
    data[chat_id]['tags'] = tags
    keyboard = []
    for tag in tags:
        keyboard.append([tag])

    # Keyboard nur anzeigen, wenn Tags vorhanden sind
    if tags:
        keyboard = ReplyKeyboardMarkup(keyboard)
    else:
        keyboard = ReplyKeyboardRemove()

    update.message.reply_text(
        ('Betrag: {:.2f}€\nUnter welcher Kategorie möchtest du den Betrag '
         'abspeichern?\nFür eine neue Kategorie einfach den Namen eingeben!')
        .format(value),
        reply_markup=keyboard
    )
    return ENTER_VALUE


def enter_tag(update, context):
    """Handling the entered tag

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for tag entry
    """
    chat_id = update.effective_chat.id
    message = update.message.text

    tag = message.strip()
    data[chat_id]['tag'] = tag

    # Überprüfen, ob Tag erst angelegt werden muss
    if tag not in data[chat_id]['tags']:
        # Der Tag 'Alle' ist ungültig (und macht auch keinen Sinn)
        if tag == 'Alle':
            return invalid(update, context)
        db.add_tag(chat_id, tag)

    keyboard = [['Ja'], ['Nein & Speichern']]

    update.message.reply_text(
        'Betrag: {:.2f}€\nTag: {}\n\nSoll ein Kommentar hinzugefügt werden?'
        .format(data[chat_id]['value'], tag),
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    return ENTER_TAG


def enter_comment(update, context):
    """Promt for user to enter a comment

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for comment entry
    """
    chat_id = update.effective_chat.id

    # Angabe, dass ein Kommentar eingegeben wird
    data[chat_id]['comment'] = True

    update.message.reply_text(
        'Welcher Kommentar soll hinzugefügt werden?',
        reply_markup=ReplyKeyboardRemove()
    )
    return ENTER_COMMENT


def enter_save(update, context):
    """Saves the entered data to the database

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for main menu
    """
    chat_id = update.effective_chat.id
    message = update.message.text

    value = data[chat_id]['value']
    tag = data[chat_id]['tag']
    date = datetime.date.today()
    comment = data[chat_id]['comment']

    # Kommentar hinzufügen, wenn dieser nicht übersprungen wurde
    if comment:
        comment = message.strip()

    # Eintrag in Datenbank schreiben
    db.add_entry(chat_id, tag, value, date, comment)

    # Zwischengespeicherte Daten löschen
    data.pop(chat_id, None)

    update.message.reply_text('Erfolgreich eingetragen!')
    return main_menu(update, context)


def analysis_menu(update, context):
    """Handling the analysis menu

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for analysis menu
    """
    keyboard = [['7 Tage', '30 Tage'],
                ['Diesen Monat', 'Dieses Jahr'],
                ['Alle'],
                ['Zurück']]

    update.message.reply_text(
        'Welchen Zeitraum möchtest du betrachten?',
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    return ANALYSIS


def analysis_time(update, context):
    """Handling the selected time period

    The possible time periods:  Saved as:
    The last 7 days             7day
    The last 30 days            30day
    This month                  month
    This year                   year
    All time                    all

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for time period selection
    """
    chat_id = update.effective_chat.id
    message = update.message.text

    data[chat_id] = {}

    # Zeitfenster anhand der gewählten Antwort auswählen
    # Weitere Nachrichten sind wegen Regex nicht möglich -> Kein else nötig
    if message == '7 Tage':
        data[chat_id]['period'] = '7day'
    elif message == '30 Tage':
        data[chat_id]['period'] = '30day'
    elif message == 'Diesen Monat':
        data[chat_id]['period'] = 'month'
    elif message == 'Dieses Jahr':
        data[chat_id]['period'] = 'year'
    elif message == 'Alle':
        data[chat_id]['period'] = 'all'

    # Tags laden und als Keyboard anzeigen
    tags = db.get_tags(chat_id)
    data[chat_id]['tags'] = tags
    keyboard = [['Alle']]
    for tag in tags:
        keyboard.append([tag])

    update.message.reply_text(
        'Welche Kategorie möchtest du betrachten?',
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    return ANALYSIS_TIME


def analysis_tag(update, context):
    """Handling the selected tag

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for tag selection
    """
    chat_id = update.effective_chat.id
    message = update.message.text

    tag = message.strip()
    time_period = data[chat_id]['period']

    # Überprüfen, ob ausgewählter Tag existiert, oder 'Alle' ist
    if tag == 'Alle':
        result = db.get_entry_sum(chat_id, time_period=time_period)
    elif tag in data[chat_id]['tags']:
        result = db.get_entry_sum(chat_id, tag=tag, time_period=time_period)
    else:
        return invalid(update, context)

    answer = ''
    for tag in result:
        answer += '{}: {:.2f}€\n'.format(tag[0], tag[1])

    update.message.reply_text(answer)

    return main_menu(update, context)


def back(update, context):
    """Returns the user back to the main menu

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for main menu
    """
    return main_menu(update, context)


def invalid(update, context):
    """Tells the user that an invalid input was made

    :param update: Update of the sent message
    :param context: Context of the sent message
    """
    update.message.reply_text(
        'Ungültige Eingabe, bitte nochmal versuchen!')


def main():
    # Daten aus Config-Datei laden
    config = load_config()

    # Bot erstellen und Token festlegen
    updater = Updater(token=config['Telegram_Bot_Token'])
    dispatcher = updater.dispatcher

    # Verbindung zur Datenbank herstellen
    global db
    db = DB('SpendingCalcData.db')

    # Handler für Eingaben registrieren
    register_handlers(dispatcher)

    # Bot starten
    updater.start_polling()
    print('Bot started!')
    updater.idle()


if __name__ == '__main__':
    main()
