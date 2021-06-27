from datetime import date, datetime, timezone, timedelta
import logging
import os
import requests
import sqlite3
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from unidecode import unidecode

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()


def clima(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Digite o nome da cidade que deseja obter informações sobre o clima\.',
        reply_markup=ForceReply(selective=True),
    )


def ajuda(update: Update, _: CallbackContext) -> None:
    update.message.reply_text(
        'Comandos:\n\n'
        '/ajuda - Exibe os comandos disponíveis e suas funções.\n'
        '/clima - Solicita o nome de uma cidade para exibir informações sobre o clima.\n\n'
        'Informações gerais:\n\n'
        '1- Basta responder a qualquer mensagem do bot com o nome de uma cidade para obter informações a respeito do clima.\n'
        '2- Se houver mais de uma cidade no Brasil com o mesmo nome da cidade que deseja obter informações, especifique também o estado. Exemplo: "São Paulo/SP".\n'
        '3- Se quiser obter a previsão do tempo de um dia posterior, basta escrever o nome da cidade + a quantidade de dias. Exemplo: "São Paulo+1 ou São Paulo/SP+1".\n'
    )


def requisicao(update: Update, _: CallbackContext) -> None:
    data = unidecode(update.message.text)
    data = data.lower()

    foundUf = data.find('/')
    foundDay = data.find('+')
    day = ''
    infos = ''

    if foundUf != -1:
        city = data[:foundUf]
        uf = data[foundUf + 1:foundUf + 3]
        cursor.execute('SELECT geocode FROM city WHERE name = ? AND uf = ?;', (city, uf))
    elif foundDay != -1:
        city = data[:foundDay]
        cursor.execute('SELECT geocode FROM city WHERE name = ?;', (city,))
    else:
        cursor.execute('SELECT geocode FROM city WHERE name = ?;', (data,))

    if foundDay != -1:
        day = data[foundDay + 1:foundDay + 2]
        if day != '1' and day != '2' and day != '3' and day != '4':
            update.message.reply_text('Só é possível prever o clima de até 4 dias.')
            return

    geoCodes = cursor.fetchall()

    if len(geoCodes) == 0:
        update.message.reply_text('A cidade informada não existe ou contêm erro na forma que foi digitada. Segue um exemplo da forma correta: "São Paulo/SP".')
        return
    elif len(geoCodes) > 1:
        update.message.reply_text('Especifique também o UF da cidade. Exemplo: "São Paulo/SP".')
        return
    else:
        cursor.execute('SELECT name, uf FROM city WHERE geocode = ?;', (geoCodes[0][0],))
        city = cursor.fetchone()

        if city[1] == 'ac':
            utc = -5
        elif city[1] == 'am':
            if city[0] == 'atalaia do norte' or city[0] == 'benjamin constant' or city[0] == 'boca do acre' or city[0] == 'eirunepe' or city[0] == 'envira' or city[0] == 'guajara' or city[0] == 'ipixuna' or city[0] == 'itamarati' or city[0] == 'jutai' or city[0] == 'labrea' or city[0] == 'pauini' or city[0] == 'sao paulo de olivenca' or city[0] == 'tabatinga':
                utc = -5
            else:
                utc = -4
        elif city[1] == 'rr' or city[1] == 'ro' or city[1] == 'mt' or city[1] == 'ms':
            utc = -4        
        elif city[1] == 'ap' or city[1] == 'pa' or city[1] == 'ma' or city[1] == 'to' or city[1] == 'pi' or city[1] == 'ce' or city[1] == 'rn' or city[1] == 'pb' or city[1] == 'pe' or city[1] == 'al' or city[1] == 'se' or city[1] == 'ba' or city[1] == 'go' or city[1] == 'mg' or city[1] == 'es' or city[1] == 'rj' or city[1] == 'sp' or city[1] == 'df' or city[1] == 'pr' or city[1] == 'sc' or city[1] == 'rs':
            if city[1] == 'pe' and city[0] == 'fernando de noronha':
                utc = -2
            else:
                utc = -3

        weather = requests.get('https://apiprevmet3.inmet.gov.br/previsao/{0}'.format(geoCodes[0][0]))

        dateTimeFunc = datetime.now()
        difference = timedelta(hours = utc)
        if day == '' or day == '1':
            if day == '1':
                dateTimeFunc = dateTimeFunc + timedelta(days=int(day))
                timeZone = timezone(difference)
                dateTime = dateTimeFunc.astimezone(timeZone)
                actualDate = dateTime.strftime('%d/%m/%Y')
                actualTime = dateTime.strftime('%H:%M')
            else:
                timeZone = timezone(difference)
                dateTime = dateTimeFunc.astimezone(timeZone)
                actualDate = dateTime.strftime('%d/%m/%Y')
                actualTime = dateTime.strftime('%H:%M')

            if actualTime >= '00:00' and actualTime <= '11:59':
                dayTime = 'manha'
            elif actualTime >= '12:00' and actualTime <= '17:59':
                dayTime = 'tarde'
            elif actualTime >= '18:00' and actualTime <= '23:59':
                dayTime = 'noite'

            infos = weather.json()['{0}'.format(geoCodes[0][0])]['{0}'.format(actualDate)]['{0}'.format(dayTime)]
        else:
            dateTimeFunc = dateTimeFunc + timedelta(days=int(day))
            timeZone = timezone(difference)
            dateTime = dateTimeFunc.astimezone(timeZone)
            actualDate = dateTime.strftime('%d/%m/%Y')

            infos = weather.json()['{0}'.format(geoCodes[0][0])]['{0}'.format(actualDate)]

    update.message.reply_text('{0} / {1}\n\nData: {2}, {3};\n\nResumo: {4};\n\nTemperatura máxima: {5}ºC;\n\nTemperatura mínima: {6}ºC;\n\nIntensidade dos ventos: {7}.\n\n'.format(infos['entidade'], infos['uf'], infos['dia_semana'], actualDate, infos['resumo'], infos['temp_max'], infos['temp_min'], infos['int_vento']))


def main() -> None:
    updater = Updater(os.environ['TOKEN'])

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('clima', clima))
    dispatcher.add_handler(CommandHandler('ajuda', ajuda))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, requisicao))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()