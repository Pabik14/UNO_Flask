from flask import Flask, render_template, redirect, request, session
from flask_session import Session
import random
import uuid


app = Flask(__name__)
app.secret_key = '4d992318-53c5-49a6-9297-5c958ddacf69'
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route('/')
def index():
    return redirect('/form')


@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/rules')
def rules():
    return render_template('rules.html')


@app.route('/board')
def board():
    if not players_exists():
        return redirect('/form')
    else:
        checkForMoves()
        checkForButtons()
        if not session['PLAYABLE'] and not session['PICKBUTTON'] and session['ENDBUTTON']:
            return redirect('/endturn')
        else:
            return render_template('board.html', drawbutton=session['DRAWBUTTON'], pickbutton=session['PICKBUTTON'],
                                   endbutton=session['ENDBUTTON'], playable=session['PLAYABLE'],
                                   players=session['PLAYERS'], playername=session['PLAYERNAME'],
                                   currentPlayer=session['PLAYERTURN'], numPlayers=session['NUMPLAYERS'],
                                   discards=session['DISCARDS'], wildcard=session['WILDCARD'],
                                   plusfour=session['PLUSFOUR'],
                                   wait=session['WAIT'], reverse=session['REVERSE'], drawcards=session['DRAWCARDS'])


@app.route('/reset', methods=['POST'])
def reset():
    session['WINNER'] = None

    session['PLAYERS'] = []
    session['PLAYERTURN'] = 0
    session['NUMPLAYERS'] = int(request.form['numPlayers'])
    session['PLAYERNAME'] = request.form.getlist("fname")

    session['DISCARDS'] = []
    session['CURRENTVAL'] = None
    session['CURRENTCOLOR'] = None
    session['PLAYABLE'] = []
    session['ENDBUTTON'] = False
    session['PICKBUTTON'] = False
    session['DRAWBUTTON'] = False

    session['PLAYEDVALUE'] = 0

    session['PLAYEDCOLOR'] = 0

    session['PICKED'] = False

    session['MOVEMADE'] = False

    session['DRAWCARDS'] = 0
    session['DRAWN'] = False

    session['WILDCARD'] = None

    session['PLUSFOUR'] = None

    session['REVERSE'] = 1

    session['WAIT'] = 0

    session['visits'] = 0

    session['unoDeck'] = buildDeck()
    session['unoDeck'] = shuffleDeck(session['unoDeck'])

    dealCards()
    putTheCorrectStartingCard()

    x = session['PLAYERNAME']
    y = session['NUMPLAYERS']
    if y == 2:
        if x[0] == '' or x[1] == '':
            return redirect('/form')
        else:
            return redirect('/board')
    elif y == 3:
        if x[0] == '' or x[1] == '' or x[2] == '':
            return redirect('/form')
        else:
            return redirect('/board')
    elif y == 4:
        if x[0] == '' or x[1] == '' or x[2] == '' or x[3] == '':
            return redirect('/form')
        else:
            return redirect('/board')
    elif y == 5:
        if x[0] == '' or x[1] == '' or x[2] == '' or x[3] == '' or x[4] == '':
            return redirect('/form')
        else:
            return redirect('/board')


@app.route('/move/<discardedCard>')
def move(discardedCard):
    if not players_exists():
        return redirect('/form')
    else:
        for card in session['PLAYERS'][session['PLAYERTURN']]:
            if card == discardedCard:
                session['PLAYERS'][session['PLAYERTURN']].remove(card)
                session['DISCARDS'].insert(0, card)
                session['PLAYEDVALUE'], session['PLAYEDCOLOR'] = checkColorAndValOfDiscardedCard()

                checkForFunctionalCards()
                session['MOVEMADE'] = True
                session['PICKBUTTON'] = False
                session['PLAYABLE'] = []

                if checkWinner():
                    return redirect('/win')

    return redirect('/board')


@app.route('/pick')
def pick():
    if not session['PICKED']:
        if len(session['unoDeck']) == 0:
            session['unoDeck'] = buildDeck()
            for player in range(int(session['NUMPLAYERS'])):
                print(player[session['NUMPLAYERS']])
                for card in session['unoDeck']:
                    if card in player:
                        session['unoDeck'].remove(card)
                        print(session['unoDeck'])
            shuffleDeck(session['unoDeck'])

        if session['DRAWCARDS'] != 0:
            session['DRAWCARDS'] -= 1

        session['PLAYERS'][session['PLAYERTURN']].extend(drawCards(1, session['unoDeck']))
        session['PICKED'] = True
        session['PICKBUTTON'] = False
        session.modified = True

    return redirect('/board')


@app.route('/draw')
def draw():
    session['PLAYERS'][session['PLAYERTURN']].extend(drawCards(int(session['DRAWCARDS']), session['unoDeck']))
    session['DRAWCARDS'] = 0
    session['PICKED'] = True
    session['MOVEMADE'] = True
    session['DRAWN'] = True
    session['DRAWBUTTON'] = False

    return redirect('/board')


@app.route('/endturn')
def endturn():
    session['PLAYABLE'] = []
    session['DRAWN'] = False

    if session['REVERSE'] == 1:
        session['PLAYERTURN'] += 1

        if session['PLAYERTURN'] == session['NUMPLAYERS']:
            session['PLAYERTURN'] = 0

    elif session['REVERSE'] == -1:
        session['PLAYERTURN'] += -1

        if session['PLAYERTURN'] < 0:
            session['PLAYERTURN'] = int(session['NUMPLAYERS'] - 1)

    session['PLAYEDVALUE'] = 0
    session['PICKED'] = False
    session['MOVEMADE'] = False
    session['ENDBUTTON'] = False
    session['PICKBUTTON'] = False

    if session['WAIT'] == 1:
        if session['REVERSE'] == 1:
            session['PLAYERTURN'] += 1
            if session['PLAYERTURN'] == session['NUMPLAYERS']:
                session['PLAYERTURN'] = 0
            session['WAIT'] -= 1
        elif session['REVERSE'] == -1:
            session['PLAYERTURN'] -= 1
            if session['PLAYERTURN'] < 0:
                session['PLAYERTURN'] = int(session['NUMPLAYERS'] - 1)
            session['WAIT'] -= 1
    if session['WAIT'] == 2:
        if session['REVERSE'] == 1:
            session['PLAYERTURN'] += 1
            if session['PLAYERTURN'] == session['NUMPLAYERS']:
                session['PLAYERTURN'] = 0
            session['WAIT'] -= 2
        elif session['REVERSE'] == -1:
            session['PLAYERTURN'] -= 1
            if session['PLAYERTURN'] < 0:
                session['PLAYERTURN'] = int(session['NUMPLAYERS'] - 1)
            session['WAIT'] -= 2

    session.modified = True

    return redirect('/nastepny')


@app.route('/win')
def win():
    return render_template('win.html', winner=session['WINNER'], playername=session['PLAYERNAME'], turns=session['visits'])


@app.route('/nastepny')
def nastepny():
    return render_template('nastepny.html',drawbutton=session['DRAWBUTTON'], pickbutton=session['PICKBUTTON'],
                                   endbutton=session['ENDBUTTON'], playable=session['PLAYABLE'],
                                   players=session['PLAYERS'],
                                   currentPlayer=session['PLAYERTURN'], numPlayers=session['NUMPLAYERS'],
                                   discards=session['DISCARDS'], wildcard=session['WILDCARD'],
                                   plusfour=session['PLUSFOUR'], playername=session['PLAYERNAME'],
                                   wait=session['WAIT'], reverse=session['REVERSE'], drawcards=session['DRAWCARDS'])


@app.route('/WILDCARD/<card>')
def wildcard(card):
    session['DISCARDS'].insert(0, card)
    session['WILDCARD'] = False
    session.modified = True
    return redirect('/board')


@app.route('/PLUSFOUR/<card>')
def plusfour(card):
    session['DISCARDS'].insert(0, card)
    session['PLUSFOUR'] = False
    session.modified = True
    return redirect('/board')


def checkForMoves():
    session['CURRENTVAL'], session['CURRENTCOLOR'] = checkColorAndValOfDiscardedCard()
    session['PLAYABLE'] = ['magic_card']
    for card in session['PLAYERS'][session['PLAYERTURN']]:

        if session['DRAWCARDS'] != 0:
            if 'plusfour' in session['CURRENTVAL']:
                if session['CURRENTCOLOR'] == 'yellow':
                    if 'yellow_plustwo' in card or'black_plusfour' in card:
                        session['PLAYABLE'].append(card)
                elif session['CURRENTCOLOR'] == 'blue':
                    if 'blue_plustwo' in card or'black_plusfour' in card:
                        session['PLAYABLE'].append(card)
                elif session['CURRENTCOLOR'] == 'red':
                    if 'red_plustwo' in card or'black_plusfour' in card:
                        session['PLAYABLE'].append(card)
                elif session['CURRENTCOLOR'] == 'green':
                    if 'green_plustwo' in card or'black_plusfour' in card:
                        session['PLAYABLE'].append(card)
            elif session['CURRENTVAL'] in card or'black_plusfour' in card:
                session['PLAYABLE'].append(card)
        elif session['DRAWCARDS'] == 0 and not session['DRAWN']:
            if session['PLAYEDVALUE'] == 0:
                if session['CURRENTCOLOR'] in card or session['CURRENTVAL'] in card or 'black_wildcard' in card or 'black_plusfour' in card:
                    session['PLAYABLE'].append(card)
            elif session['PLAYEDVALUE'] != 0 and session['PLAYEDVALUE'] in card and session['PLAYEDVALUE'] != 'skip':
                session['PLAYABLE'].append(card)


def checkDrawCards():
    if session['DRAWCARDS'] != 0 and not session['MOVEMADE']:
        return True


def checkPick():
    if session['DRAWN']:
        return False


    if (not session['MOVEMADE'] and not session['PICKED'] and not session['DRAWN']):
        return True


def checkEndTurn():
    if session['WILDCARD']:
        return False

    elif session['PLUSFOUR']:
        return False

    elif session['DRAWCARDS'] != 0 and not session['DRAWN'] and not session['MOVEMADE']:
        return False

    elif session['DRAWCARDS'] == 0 and session['MOVEMADE']:
        return True

    elif (session['MOVEMADE'] or session['PICKED']):
        return True


def checkForFunctionalCards():
    if session['PLAYEDVALUE'] == "plustwo":
        session['DRAWCARDS'] += 2
    if session['PLAYEDVALUE'] == "plusfour":
        session['DRAWCARDS'] += 4
        session['PLUSFOUR'] = True

    if session['PLAYEDVALUE'] == "reverse":
        session['REVERSE'] *= -1

    if session['PLAYEDVALUE'] == "wildcard":
        session['WILDCARD'] = True

    if session['PLAYEDVALUE'] == "skip":
        session['WAIT'] += 1

    session.modified = True


def checkValueOfACard(card):
    splitCard = card.split("_", 1)
    color = splitCard[0]
    value = splitCard[1]
    return value, color


def checkColorAndValOfDiscardedCard():
    splitCard = session['DISCARDS'][0].split("_", 1)
    currentColor = splitCard[0]
    currentVal = splitCard[1]
    return currentVal, currentColor


numCards = 7


def dealCards():
    for player in range(int(session['NUMPLAYERS'])):
        session['PLAYERS'].append(drawCards(7, session['unoDeck']))


def putTheCorrectStartingCard():
    values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    while True:
        session['DISCARDS'].insert(0, session['unoDeck'].pop(0))

        if any(value in session['DISCARDS'][0] for value in values):
            break


def players_exists():
    if not session.get('PLAYERS') or len(session['PLAYERS']) < 2:
        return False
    else:
        return True


"""
generowanie talii 112 kart x4 wild, 4x +4, 4x20 kart każdego koloru 0-9, 4x po 2 karty reverse każdego koloru,
4x po 2 karty skip każdego koloru, 4x po 2 karty +2 każdego koloru
"""


def buildDeck():
    deck = ['black_plusfour', 'black_plusfour', 'black_plusfour', 'black_plusfour', 'black_wildcard', 'black_wildcard',
            'black_wildcard', 'black_wildcard']
    suits = ['blue', 'green', 'yellow', 'red', 'blue', 'green', 'yellow', 'red']
    values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 'plustwo', 'reverse', 'skip']
    for suit in suits:
        for value in values:
            cardVal = "{}_{}".format(suit, value)
            deck.append(cardVal)
    return deck


"""
losowanie kart z talii
"""


def shuffleDeck(deck):
    random.shuffle(deck)
    return deck


def drawCards(numCards, deck):
    cardsDrawn = []
    if numCards <= len(deck):
        newDeck = buildDeck()
        newDeck = shuffleDeck(newDeck)
        session['unoDeck'].extend(newDeck)

    for x in range(numCards):
        cardsDrawn.append(deck.pop(0))
    return cardsDrawn


def checkWinner():
    if len(session['PLAYERS'][session['PLAYERTURN']]) == 0:
        session['WINNER'] = session['PLAYERTURN']
        session.modified = True
        return True


def checkForButtons():
    if checkDrawCards():
        session['DRAWBUTTON'] = True
    else:
        session['DRAWBUTTON'] = False

    if checkPick():
        session['PICKBUTTON'] = True
    else:
        session['PICKBUTTON'] = False

    if checkEndTurn():
        session['ENDBUTTON'] = True
    else:
        session['ENDBUTTON'] = False


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='5118', debug=True)
