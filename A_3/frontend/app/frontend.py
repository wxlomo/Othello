"""
 * frontend.py
 * front-end interface and router of the gallery web application
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
"""
import dynamodb
from . import front, config
from flask import render_template, request, escape, jsonify, session, redirect


@front.route('/')
def get_home():
    """Home page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    return render_template('index.html')


@front.route('/create')
def get_create():
    """New game creating page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    return render_template('create.html')


@front.route('/join')
def get_join():
    """Existing game joining page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    all_hosts = []  # the function to retrieve all available hosts
    return render_template('join.html', hosts=all_hosts)


@front.route('/rule')
def get_rule():
    """Rule page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    return render_template('rule.html')


@front.route('/rank')
def get_rank():
    """Rank page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    rank = []  # Retrieve the rank data from S3
    return render_template('rank.html', rank=rank)


@front.route('/about')
def get_about():
    """About page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    return render_template('about.html')


@front.route('/create_game', methods=['POST'])
def create_game():
    """Create a new game.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    session['player_name'] = request.form['player_name']
    player_side = request.form['player_side']
    front.logger.debug('\n* Creating a game with name: ' + str(session['player_name']))
    game_id = escape(session['player_name'])  # the function to create a game to dynamoDB
    return redirect('/game/' + str(game_id))


@front.route('/join_game', methods=['POST'])
def join_game():
    """Join an existing game.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    session['player_name'] = request.form['player_name']
    game_id = request.form['game_id']
    front.logger.debug('\n* Joining a game with name: ' + str(session["player_name"]) + ' and game id: ' + str('game_id'))
    if True:  # Check if game id exist
        return redirect('/game/' + str(game_id))
    else:
        return render_template('result', title='Fail to Join the Game', message='The game you want to join does not exist, please try again.')


@front.route('/game/<game_id>/')
def game(game_id):
    """Game board page render.

    Args:
      game_id (str): the identity of the game

    Returns:
      str: the arguments for the Jinja template
    """
    player_name = session['player_name']
    if not player_name or not game_id:
        return render_template('result', title='403 Forbidden', message='This page is not reachable.')
    disks = []  # get the disks from dynamoDB
    board = board_render(game_id, player_name, disks)
    if len(board) != 64:
        return render_template('result', title='500 Internal Server Error', message='Failed to render the game board.')
    foe_name = ''  # get the name of another player
    front.logger.debug('\n* Current game board: ' + str(board) + ', current foe name: ' + str(foe_name))
    if not foe_name:  # check if another player joined
        message = 'Waiting for another player to join...'
    else:
        if True:  # check if it is current player's turn
            message = 'Now it is your turn!'
        else:
            message = 'Now it is your foe ' + str(foe_name) + "'s turn!"
    return render_template('game.html', board=board, surr='/game/' + str(game_id) + '/surrender', message=message)


@front.route('/game/<game_id>/move/<loc>')
def move(game_id, loc):
    """Player makes a move

    Args:
      game_id (str): the identity of the game
      loc (str): the location to place the disk

    Returns:
      str: the arguments for the Jinja template
    """
    player_name = session['player_name']
    if not player_name or not game_id or not loc:
        return render_template('result', title='403 Forbidden', message='This page is not reachable.')
    if False:  # check if the move can be made
        return render_template('result', title='403 Forbidden', message='This move cannot be performed.')
    # update the database with loc
    front.logger.debug('\n* A move is made on game: ' + str(game_id) + ' at ' + str(loc))
    return redirect('/game/' + str(game_id))


@front.route('/game/<game_id>/surrender')
def surrender(game_id):
    """A player surrender

    Args:
      game_id (str): the identity of the game

    Returns:
      str: the arguments for the Jinja template
    """
    player_name = session['player_name']
    if not player_name or not game_id:
        return render_template('result', title='403 Forbidden', message='This page is not reachable.')
    ended = True  # mark the game as ended on dynamoDB
    player_score = 0  # mark the current player's score as 0
    front.logger.debug('\n* A player with name' + str(player_name) + ' surrender in game ' + str(game_id))
    return render_template('result', title='You Lose :(', message='Sorry to hear your leave.')


@front.route('/game/<game_id>/refresh')
def refresh(game_id):
    """Refresh the game status

    Args:
      game_id (str): the identity of the game

    Returns:
      str: the arguments for the Jinja template
    """
    player_name = session['player_name']
    if not player_name or not game_id:
        return render_template('result', title='403 Forbidden', message='This page is not reachable.')
    ended = ""  # check if the game ends
    if ended:
        player_score = 0  # get the player's final score
        foe_score = 0  # get the other player's final score
        front.logger.debug('\n* The player' + str(player_name) + ' has score ' + str(player_score) + ', their foe has score ' + str(foe_score))
        if player_score > foe_score:
            # upload the final score to the ranking
            return render_template('result', title='You Win :)', message='Your final score is ' + str(player_score) + '.')
        elif player_score < foe_score:
            return render_template('result', title='You Lose :(', message='Your final score is ' + str(player_score) + '.')
        else:
            return render_template('result', title='Draw...', message='Your final score is ' + str(player_score) + '.')
    else:
        return redirect('/game/' + str(game_id))


def board_render(game_id, player_name, disks):
    """Update the disks and placeable places on the game board

    Args:
      game_id (str): the identity of the game
      player_name (str): the name of current player
      disks (list): the list of disks on the game board

    Returns:
      list: the updated lattices list to update the page
    """
    index = [outer * 10 + inner for inner in range(1, 9) for outer in range(1, 9)]
    current_index = 0
    grid = []  # Preprocess: mark the lattices as dark, light, or placeable, size must be 64,
    board = []
    for lattice in grid:
        if lattice == 'dark':
            board.append('<img src="src/img/dark.svg">')
        elif lattice == 'light':
            board.append('<img src="src/img/light.svg">')
        elif lattice == 'placeable':
            board.append('<input type="image" src="src/img/placeable.svg" alt="Submit" class="placeable" formaction="/game/' + str(game_id) + '/move/' + index[current_index] + '">')
        else:
            board.append('')
        current_index += 1
    return board



