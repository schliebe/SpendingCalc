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
ENTER_DATE = 13
ENTER_COMMENT = 14
ANALYSIS = 20
ANALYSIS_TIME = 21
ANALYSIS_TAG = 22
ANALYSIS_SHOW = 23
ANALYSIS_SELECT = 24
ANALYSIS_EDIT = 25
EDIT_VALUE = 251
EDIT_DATE = 252
EDIT_COMMENT = 253
EDIT_SAVE = 254
EDIT_REMOVE = 255

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
            ENTER_TAG: [MessageHandler(Filters.text, enter_date)],
            ENTER_DATE: [MessageHandler(Filters.regex('^(Nein & Speichern)$'),
                                        enter_save),
                         MessageHandler(Filters.regex('^(Ja)$'), enter_comment),
                         MessageHandler(Filters.text, invalid)],
            ENTER_COMMENT: [MessageHandler(Filters.text, enter_save)],
            ANALYSIS: [MessageHandler(Filters.regex('^(Zurück)$'), back),
                       MessageHandler(Filters.regex(
                           '^(7 Tage|30 Tage|Diesen Monat|Dieses Jahr|Alle)$'),
                           analysis_time),
                       MessageHandler(Filters.text, invalid)],
            ANALYSIS_TIME: [MessageHandler(Filters.text, analysis_tag)],
            ANALYSIS_TAG: [MessageHandler(Filters.regex('^(Zurück)$'), back),
                           MessageHandler(Filters.regex(
                               '^(Einträge anzeigen)$'), analysis_show),
                           MessageHandler(Filters.text, invalid)],
            ANALYSIS_SHOW: [MessageHandler(Filters.regex('^(Nein)$'), back),
                            MessageHandler(Filters.regex('^(Ja)$'),
                                           analysis_select)],
            ANALYSIS_SELECT: [MessageHandler(Filters.text, analysis_edit)],
            ANALYSIS_EDIT: [MessageHandler(Filters.regex('^(Zurück)$'), back),
                            MessageHandler(Filters.regex(
                                '^(Betrag bearbeiten|Datum bearbeiten|'
                                'Kommentar bearbeiten|Eintrag löschen)$'),
                                analysis_edit_select),
                            MessageHandler(Filters.text, invalid)],
            EDIT_VALUE: [MessageHandler(Filters.regex(
                         r'^-?\d+((\.|,)\d{1,2})?€?$'),
                         analysis_edit_value),
                         MessageHandler(Filters.text, invalid)],
            EDIT_DATE: [MessageHandler(Filters.regex(
               r'^\d{1,2}(\.|-| )\d{1,2}((\.|-| )?|((\.|-| )(\d{2}|\d{4})))?$'),
                        analysis_edit_date),
                        MessageHandler(Filters.text, invalid)],
            EDIT_COMMENT: [MessageHandler(Filters.text, analysis_edit_comment)],
            EDIT_SAVE: [MessageHandler(Filters.regex('^(Nein)$'), back),
                        MessageHandler(Filters.regex('^(Ja)$'),
                                       analysis_save)],
            EDIT_REMOVE: [MessageHandler(Filters.regex('^(Nein)$'), back),
                          MessageHandler(Filters.regex('^(Ja)$'),
                                         analysis_remove_entry),
                          MessageHandler(Filters.text, invalid)]
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

    keyboard = [['Heute'], ['Gestern']]

    update.message.reply_text(
        ('Betrag: {:.2f}€\nTag: {}\n\nFür welches Datum? '
         '(Bitte eingeben oder auswählen)')
        .format(data[chat_id]['value'], tag),
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    return ENTER_TAG


def enter_date(update, context):
    """Handling the entered date

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for date entry
    """
    chat_id = update.effective_chat.id
    message = update.message.text

    if message == 'Heute':
        date = datetime.date.today()
        y, m, d = date.year, date.month, date.day
    elif message == 'Gestern':
        date = datetime.date.today() - datetime.timedelta(days=1)
        y, m, d = date.year, date.month, date.day
    else:
        # Eingabe überprüfen und in richtige Form umwandeln
        date, date_values = convert_date(message)
        # Bei ungültiger Eingabe abbrechen
        if not date or not date_values:
            return invalid(update, context)
        y, m, d = date_values

    data[chat_id]['date'] = date

    keyboard = [['Ja'], ['Nein & Speichern']]

    update.message.reply_text(
        'Datum: {:02d}.{:02d}.{:04d}\n\nSoll ein Kommentar hinzugefügt werden?'
        .format(d, m, y),
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    return ENTER_DATE


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
    date = data[chat_id]['date']
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

    tag = data[chat_id]['tag'] = message.strip()
    time_period = data[chat_id]['period']
    show_total = False

    # Überprüfen, ob ausgewählter Tag existiert, oder 'Alle' ist
    # Ergebnisse aus Datenbank laden
    if tag == 'Alle':
        result = db.get_entry_sum(chat_id, time_period=time_period)
        show_total = True
    elif tag in data[chat_id]['tags']:
        result = db.get_entry_sum(chat_id, tag=tag, time_period=time_period)
    else:
        return invalid(update, context)

    # Antwort-Nachricht erstellen
    answer = ''
    total = 0
    for tag in result:
        answer += '{}: {:.2f}€\n'.format(tag[0], tag[1])
        total += float(tag[1])

    if show_total:
        answer += 'Gesamt: {:.2f}€\n'.format(total)
    answer += '\nMöchtest du die Einträge anzeigen lassen?'

    keyboard = [['Einträge anzeigen'],
                ['Zurück']]

    update.message.reply_text(
        answer,
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )
    return ANALYSIS_TAG


def analysis_show(update, context):
    """Sending all selected entries

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for shown entries
    """
    chat_id = update.effective_chat.id
    time_period = data[chat_id]['period']
    tag = data[chat_id]['tag']

    # Einträge je nach Auswahl aus der Datenbank laden
    if tag == 'Alle':
        result = db.get_entries(chat_id, time_period=time_period)
    elif tag in data[chat_id]['tags']:
        result = db.get_entries(chat_id, tag=tag, time_period=time_period)
    else:
        return invalid(update, context)

    # Einträge zwischenspeichern
    data[chat_id]['entries'] = result

    answer = ''
    for i in range(len(result)):
        entry = result[i]
        y, m, d = entry[3].split('-')
        date = '{}.{}.{}'.format(int(d), int(m), int(y))
        if entry[4]:
            answer += '({}) {:.2f}€ - {}\n{}: {}\n\n'.format(
                i + 1, entry[1], date, entry[2], entry[4])
        else:
            answer += '({}) {:.2f}€ - {}\n{}\n\n'.format(
                i + 1, entry[1], date, entry[2])

    answer += 'Möchtest du einen Eintrag bearbeiten?'

    keyboard = [['Ja'],
                ['Nein']]

    update.message.reply_text(
        answer,
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )

    return ANALYSIS_SHOW


def analysis_select(update, context):
    """Prompt for user to select the entry that should be edited

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for entry selection
    """
    update.message.reply_text(
        'Nummer des zu bearbeitenden Eintrags eingeben!',
        reply_markup=ReplyKeyboardRemove()
    )

    return ANALYSIS_SELECT


def analysis_edit(update, context):
    """Asking the user how the entry should be edited

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for edit selection
    """
    chat_id = update.effective_chat.id
    message = update.message.text
    entries = data[chat_id]['entries']

    # Wenn Eingabe eine Zahl
    if message.isdecimal():
        # Index wieder um 1 verringern um auf Index anzupassen
        entry = int(message) - 1
        if entry < len(data[chat_id]['entries']):
            entry = entries[entry]
            data[chat_id]['entry'] = entry
            data[chat_id].pop('entries', None)

            y, m, d = entry[3].split('-')
            date = '{}.{}.{}'.format(int(d), int(m), int(y))
            if entry[4]:
                answer = '{:.2f}€ - {} - "{}"'.format(
                    entry[1], date, entry[4])
            else:
                answer = '{:.2f}€ - {} - Kein Kommentar'.format(
                    entry[1], date)

            answer += '\nWie soll der Eintrag bearbeitet werden?'

            keyboard = [['Betrag bearbeiten', 'Datum bearbeiten'],
                        ['Kommentar bearbeiten', 'Eintrag löschen'],
                        ['Zurück']]

            update.message.reply_text(
                answer,
                reply_markup=ReplyKeyboardMarkup(keyboard)
            )

            return ANALYSIS_EDIT

    # Bei ungültiger Eingabe
    return invalid(update, context)


def analysis_edit_select(update, context):
    """Sending Messages according to how the entry should be edited

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for edit selection
    """
    message = update.message.text

    if message == 'Betrag bearbeiten':
        answer = 'Welcher Betrag soll eingetragen werden?'
        update.message.reply_text(
            answer,
            reply_markup=ReplyKeyboardRemove()
        )
        return EDIT_VALUE
    elif message == 'Datum bearbeiten':
        answer = 'Welches Datum soll eingetragen werden?'
        update.message.reply_text(
            answer,
            reply_markup=ReplyKeyboardRemove()
        )
        return EDIT_DATE
    elif message == 'Kommentar bearbeiten':
        answer = ('Welcher Kommentar soll eingetragen werden?\n'
                  '/löschen um den Kommentar zu löschen')
        update.message.reply_text(
            answer,
            reply_markup=ReplyKeyboardRemove()
        )
        return EDIT_COMMENT
    elif message == 'Eintrag löschen':
        answer = 'Soll der Eintrag gelöscht werden?'
        keyboard = [['Ja'], ['Nein']]
        update.message.reply_text(
            answer,
            reply_markup=ReplyKeyboardMarkup(keyboard)
        )
        return EDIT_REMOVE


def analysis_edit_value(update, context):
    """Asking for the new value of the entry

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for editing the value
    """
    chat_id = update.effective_chat.id
    message = update.message.text
    entry = data[chat_id]['entry']

    value = float(message.strip().replace(',', '.').replace('€', ''))
    data[chat_id]['entry'] = (entry[0], value, entry[2], entry[3], entry[4])

    answer = 'Neuer Betrag: {:.2f}€'.format(value)
    answer += '\nSoll die Änderung gespeichert werden?'

    keyboard = [['Ja'],
                ['Nein']]

    update.message.reply_text(
        answer,
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )

    return EDIT_SAVE


def analysis_edit_date(update, context):
    """Asking for the new date of the entry

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for editing the date
    """
    chat_id = update.effective_chat.id
    message = update.message.text
    entry = data[chat_id]['entry']

    # Eingabe überprüfen und in richtige Form umwandeln
    date, date_values = convert_date(message)
    # Bei ungültiger Eingabe abbrechen
    if not date or not date_values:
        return invalid(update, context)
    y, m, d = date_values

    data[chat_id]['entry'] = (entry[0], entry[1], entry[2], date, entry[4])

    answer = 'Neues Datum: {:02d}.{:02d}.{:04d}'.format(d, m, y)
    answer += '\nSoll die Änderung gespeichert werden?'

    keyboard = [['Ja'],
                ['Nein']]

    update.message.reply_text(
        answer,
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )

    return EDIT_SAVE


def analysis_edit_comment(update, context):
    """Asking for the new comment of the entry

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for editing the comment
    """
    chat_id = update.effective_chat.id
    message = update.message.text
    entry = data[chat_id]['entry']

    # Wenn /löschen geschrieben wurde, Nachricht löschen
    if message == '/löschen':
        comment = None
        answer = 'Kein Kommentar eingetragen.'
    else:
        comment = message.strip()
        answer = 'Neuer Kommentar: "{}"'.format(comment)

    data[chat_id]['entry'] = (entry[0], entry[1], entry[2], entry[3], comment)

    answer += '\nSoll die Änderung gespeichert werden?'

    keyboard = [['Ja'],
                ['Nein']]

    update.message.reply_text(
        answer,
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )

    return EDIT_SAVE


def analysis_save(update, context):
    """Save the edited entry

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for main menu
    """
    chat_id = update.effective_chat.id

    db.update_entry(data[chat_id]['entry'])
    update.message.reply_text('Eintrag geändert!')
    return back(update, context)


def analysis_remove_entry(update, context):
    """Asking the user if the entry should be removed

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for removing the entry
    """
    chat_id = update.effective_chat.id

    db.remove_entry(data[chat_id]['entry'][0])
    update.message.reply_text('Eintrag gelöscht!')
    return back(update, context)


def back(update, context):
    """Returns the user back to the main menu

    :param update: Update of the sent message
    :param context: Context of the sent message
    :return: Status for main menu
    """

    # Zwischengespeicherte Daten löschen
    chat_id = update.effective_chat.id
    data.pop(chat_id, None)

    return main_menu(update, context)


def invalid(update, context):
    """Tells the user that an invalid input was made

    :param update: Update of the sent message
    :param context: Context of the sent message
    """
    update.message.reply_text(
        'Ungültige Eingabe, bitte nochmal versuchen!')


def convert_date(input_string):
    """Takes input and converts to correct date format.
    If an invalid or future date is entered, None will be returned

    :param input_string: String with the date to be converted
    :return: Date string for the database and a tuple with (year, month, day) or
    None, None if the input is invalid
    """
    try:
        date = input_string.strip().replace('.', '-').replace(' ', '-')
        # Wenn Jahr nicht angegeben, aber Punkt am Ende
        if date[-1] == '-':
            date = date[:-1]
        # Wenn nur Tag und Monat angegeben
        if date.count('-') == 1:
            d, m = date.split('-')
            d, m = int(d), int(m)
            y = datetime.date.today().year
            # Wenn Datum in Zukunft, letztes Jahr eintragen
            if datetime.date(y, m, d) > datetime.date.today():
                y -= 1
        # Wenn auch Jahr angegeben
        else:
            d, m, y = date.split('-')
            if len(y) == 2:
                y = '20' + y
        d, m, y = int(d), int(m), int(y)
        date = '{:04d}-{:02d}-{:02d}'.format(y, m, d)

        # Überprüfen, ob Datum gültig und nicht in Zukunft
        if datetime.date(y, m, d) > datetime.date.today():
            return None, None
        else:
            return date, (y, m, d)
    except BaseException:
        return None, None


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
