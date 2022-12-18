"""
 * frontend.py
 * front-end interface and router of the othello web application
 *
 * Author: Weixuan Yang
 * Date: Dec. 11, 2022
"""
from . import front, dynamodb as ddb, games_table, rank_bucket, ses
from flask import render_template, request, redirect, escape, jsonify, json, url_for
from uuid import uuid4


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
    all_hosts = []
    all_items = ddb.get_invites('None', games_table)
    for i in all_items:
        all_hosts.append(str(i['HostId']))
        front.logger.debug('\n* Current pending games: ' + str(i['GameId']))
    return render_template('join.html', pending=all_hosts)


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
    rank = []
    try:
        for obj in rank_bucket.objects.all():
            rank.append([obj.key, int.from_bytes(obj.get()['Body'].read(), byteorder='big')])
    except Exception as error:
        front.logger.debug('\n* Error: ' + str(error))
        return render_template('result.html', title='500 Internal Server Error',
                               message='Server Failure.')
    rank.sort(key=lambda content: content[1], reverse=True)
    return render_template('rank.html', rank=rank[:10])


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
    player_name = escape(request.form['player_name'].strip())
    if not player_name or player_name == 'None' or player_name == 'draw':
        return render_template('result.html', title='Invalid Player Name',
                               message='Do not use spaces/None/draw as your player name')
    tile = request.form['player_side']
    front.logger.debug('\n* Creating a game with name: ' + str(player_name))
    game_id = str(uuid4())
    response = ddb.create_new_game(game_id, str(player_name), 'None', tile, games_table)
    front.logger.debug(str(response))
    game_id = response['GameId']
    '''
    invite_email = request.form['invite_email'].strip()
    try:
        ses.send_email(
            Destination={'ToAddresses': [invite_email,],},
            Message={
                'Body': {
                    'Text': {
                        'Charset': "UTF-8",
                        'Data': 'Greetings! Your friend invite you to join them playing Othello! Please join use their player name: ' + str(player_name),
                    },
                },
                'Subject': {
                    'Charset': "UTF-8",
                    'Data': 'Game Invitation from ' + str(player_name),
                },
            },
            source='othello.endreim@outlook.com',
        )
    except Exception as error:
        front.logger.debug('\n* Error: ' + str(error))
    '''
    return redirect(url_for('game', game_id=str(game_id), player_name=str(player_name)))


@front.route('/join_game', methods=['POST'])
def join_game():
    """Join an existing game.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    player_name = escape(request.form['player_name'].strip())
    if not player_name or player_name == 'None' or player_name == 'draw':
        return render_template('result.html', title='Invalid Player Name',
                               message='Do not use spaces as your player name')
    host_name = request.form['host_name']
    front.logger.debug(
        '\n* Joining a game with name: ' + str(player_name) + ' and host name: ' + str(host_name))
    game_data = ddb.get_games_status(host_name, "Pending", games_table)
    front.logger.debug(str(game_data))
    if not game_data:
        return render_template('result.html', title='Fail to Join the Game',
                               message='The game you want to join does not exist, please try again.')
    response = ddb.join_existed_game(game_data, games_table, str(player_name))
    front.logger.debug(str(response))
    if response == 'Not a valid game':
        return render_template('result.html', title='Fail to Join the Game',
                               message='The game you want to join does not exist, please try again.')
    return redirect(url_for('game', game_id=str(game_data['GameId']), player_name=str(player_name)))


@front.route('/game/<game_id>/<player_name>')
def game(game_id, player_name):
    """Game board page render.

    Args:
      game_id (str): the identity of the game
      player_name (str): the name of the player

    Returns:
      str: the arguments for the Jinja template
    """
    if not player_name or not game_id:
        return render_template('result.html', title='403 Forbidden', message='This page is not reachable.')
    game_data = ddb.get(game_id, games_table)
    front.logger.debug(str(game_data))
    if not game_data:
        return render_template('result.html', title='500 Internal Server Error',
                               message='Failed to render the game board.')
    status = game_data["Statusnow"]
    if status == 'Finished':
        return settlement(game_id, player_name)
    game_board = ddb.make_board(game_data)
    foe_name = game_data['FoeId']
    if player_name == foe_name:
        foe_name = game_data['HostId']

    if not foe_name or foe_name == 'None':  # the foe does not come in
        board = board_render(game_id, player_name, game_board, [])
        front.logger.debug('\n* Current game board: ' + str(board) + ', current foe name: ' + str(foe_name))
        message = 'Waiting for another player to join...'
    else:  # game is ready
        message = 'Now it is your turn!'
        if game_data['OUser'] == player_name:
            tile = 'O'
            other_tile = 'X'
        else:
            tile = 'X'
            other_tile = 'O'
        if game_data['Turn'] == str(player_name):  # current player's turn
            moves = get_valid_moves(game_board, tile)
            front.logger.debug('\n* Valid moves: ' + str(moves))
            if not moves:  # impossible to move
                message = 'No valid move!'
                if get_valid_moves(game_board, other_tile):
                    ddb.update_turn(game_data, [], player_name, games_table)
                else:
                    player_score = ddb.count_disks(game_data, tile)
                    foe_score = ddb.count_disks(game_data, other_tile)
                    front.logger.debug('\n* Game end with: ' + str(player_score) + ' vs ' + str(foe_score))
                    if player_name == game_data['HostId']:
                        foe_name = game_data['FoeId']
                    else:
                        foe_name = game_data['HostId']
                    if player_score > foe_score:  # player wins
                        ddb.finish_game(game_data, games_table, player_name)
                    elif player_score < foe_score:  # foe wins
                        ddb.finish_game(game_data, games_table, foe_name)
                    else:  # draw
                        ddb.finish_game(game_data, games_table, 'draw')
            board = board_render(game_id, player_name, game_board, moves)
        else:
            message = 'Now it is your foe ' + str(foe_name) + "'s turn!"
            board = board_render(game_id, player_name, game_board, [])
    game_json = json.dumps({'gameId': game_id, 'status': status, 'turn': game_data['Turn']})
    surr = url_for('surrender', game_id=str(game_id), player_name=str(player_name))
    curr = url_for('data', game_id=str(game_id))
    return render_template('game.html', board=board,
                           surr=surr, message=message,
                           game=game_json,
                           data=curr)


@front.route('/game/<game_id>/<player_name>/move/<loc>', methods=['POST'])
def move(game_id, player_name, loc):
    """Player makes a move

    Args:
      game_id (str): the identity of the game
      player_name (str): the name of the player
      loc (str): the location to place the disk

    Returns:
      str: the arguments for the Jinja template
    """
    if not player_name or not game_id or not loc:
        return render_template('result.html', title='403 Forbidden', message='This page is not reachable.')
    game_data = ddb.get(game_id, games_table)
    front.logger.debug(str(game_data))
    if not game_data:
        return render_template('result.html', title='500 Internal Server Error',
                               message='Failed to render the game board.')
    game_board = ddb.make_board(game_data)
    x_start, y_start = loc[0], loc[1]
    if game_data['OUser'] == player_name:
        tile = 'O'
    else:
        tile = 'X'
    valid = valid_move(game_board, tile, int(x_start), int(y_start))
    if not valid:
        return render_template('result.html', title='403 Forbidden', message='This move cannot be performed.')
    position = [str(x_start) + str(y_start)]
    for p in valid:
        position.append(str(p[0]) + str(p[1]))
    ddb.update_turn(game_data, position, player_name, games_table)
    front.logger.debug('\n* A move is made on game: ' + str(game_id) + ' at ' + str(loc))
    return redirect(url_for('game', game_id=str(game_id), player_name=str(player_name)))


@front.route('/game/<game_id>/<player_name>/surrender', methods=['POST'])
def surrender(game_id, player_name):
    """A player surrender

    Args:
      game_id (str): the identity of the game
      player_name (str): the name of the player

    Returns:
      str: the arguments for the Jinja template
    """
    if not player_name or not game_id:
        return render_template('result.html', title='403 Forbidden', message='This page is not reachable.')
    game_data = ddb.get(game_id, games_table)
    front.logger.debug(str(game_data))
    if player_name == game_data['HostId']:
        winner = game_data['FoeId']
    else:
        winner = game_data['HostId']
    ddb.finish_game(game_data, games_table, winner)
    front.logger.debug('\n* A player with name' + str(player_name) + ' surrender in game ' + str(game_id))
    return render_template('result.html', title='You Lose :(', message='Sorry to hear your leave.')


@front.route('/data/<game_id>')
def data(game_id):
    """
    Method associated the with the '/data/<gameId>' route where the
    gameId is in the URL.
    Validates that the gameId actually exists.
    Returns a JSON representation of the game to support AJAX to poll to see
    if the page should be refreshed
    """
    game_data = ddb.get(game_id, games_table)
    if not game_data:
        return render_template('result.html', title='500 Internal Server Error',
                               message='Failed to render the game board.')
    status = game_data["Statusnow"]
    turn = game_data["Turn"]
    return jsonify(gameId=game_id, status=status, turn=turn)


@front.route('/game/<game_id>/<player_name>/settlement')
def settlement(game_id, player_name):
    """settle the game, return the result

    Args:
      game_id (str): the identity of the game
      player_name (str): the name of the player

    Returns:
      str: the arguments for the Jinja template
    """
    if not player_name or not game_id:
        return render_template('result.html', title='403 Forbidden', message='This page is not reachable.')
    game_data = ddb.get(game_id, games_table)
    front.logger.debug(str(game_data))
    status = game_data["Statusnow"]
    if status == 'Finished':
        if game_data['OUser'] == player_name:
            tile = 'O'
        else:
            tile = 'X'
        player_score = ddb.count_disks(game_data, tile)
        front.logger.debug('\n* The player ' + str(player_name) + ' has score ' + str(player_score))
        winner = game_data['Winner']
        if winner == player_name:
            try:
                rank_bucket.put_object(Key=winner, Body=player_score.to_bytes(8, byteorder='big'))
            except Exception as error:
                front.logger.debug('\n* Error: ' + str(error))
                return render_template('result.html', title='500 Internal Server Error',
                                       message='Server Failure.')
            return render_template('result.html', title='You Win :)',
                                   message='Your final score is ' + str(player_score) + '.')
        elif winner != 'draw':
            return render_template('result.html', title='You Lose :(',
                                   message='Your final score is ' + str(player_score) + '.')
        else:
            return render_template('result.html', title='Draw...',
                                   message='Your final score is ' + str(player_score) + '.')
    else:
        front.logger.debug('\n* Refreshing the game board')
        return redirect(url_for('game', game_id=str(game_id), player_name=str(player_name)))


def board_render(game_id, player_name, board, valid_moves):
    """Update the disks and placeable places on the game board

    Args:
      game_id (str): the identity of the game
      player_name (str): the name of the player
      board (list): the nested list of the game board
      valid_moves (list): the coordinates of the valid moves

    Returns:
      list: the updated lattices list to update the page
    """
    index = [[str(outer) + str(inner) for inner in range(len(board[outer]))] for outer in range(len(board))]
    dark_url = url_for('static', filename='img/dark.svg')
    light_url = url_for('static', filename='img/light.svg')
    placeable_url = url_for('static', filename='img/placeable.svg')
    updated_board = board
    updated_list = []
    if valid_moves:
        for x, y in valid_moves:
            updated_board[x][y] = '.'
    for x in range(len(updated_board)):
        for y in range(len(updated_board[x])):
            current_disk = updated_board[x][y]
            if current_disk == 'X':
                updated_list.append('<img src="' + dark_url + '">')
            elif current_disk == 'O':
                updated_list.append('<img src="' + light_url + '">')
            elif current_disk == '.':
                move_url = url_for('move', game_id=str(game_id), player_name=str(player_name), loc=str(index[x][y]))
                updated_list.append(
                    '<input type="image" src="' + placeable_url + '" alt="Submit" class="placeable" formaction= "' + move_url + '" >')
            else:
                updated_list.append(' ')
    return updated_list


def valid_move(board, tile, x, y):
    """Check if the move is valid and obtain the result

    Args:
      board (list): the nested list of the game board
      tile (str): the side of the disk, 'X' if dark, 'O' if white
      x (int): the x coordinate of the moved disk
      y (int): the y coordinate of the moved disk

    Returns:
      list: the resulting changed disks, None if is not a valid move
    """

    def is_on_board(x_current, y_current):
        return 0 <= x_current <= 7 and 0 <= y_current <= 7

    if board[x][y] != ' ' or not is_on_board(x, y):
        return False
    board[x][y] = tile
    if tile == 'X':
        other_tile = 'O'
    else:
        other_tile = 'X'
    tiles_to_flip = []
    for x_direction, y_direction in [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]:
        x_start, y_start = x, y
        x_start += x_direction  # first step in the direction
        y_start += y_direction  # first step in the direction
        if is_on_board(x_start, y_start) and board[x_start][y_start] == other_tile:
            # There is a piece belonging to the other player next to current piece.
            x_start += x_direction
            y_start += y_direction
            if not is_on_board(x_start, y_start):
                continue
            while board[x_start][y_start] == other_tile:
                x_start += x_direction
                y_start += y_direction
                if not is_on_board(x_start, y_start):  # break out of while loop, then continue in for loop
                    break
            if not is_on_board(x_start, y_start):
                continue
            if board[x_start][y_start] == tile:
                # There are pieces to flip over. Go in the reverse direction until reach the original space, noting all the tiles along the way.
                while True:
                    x_start -= x_direction
                    y_start -= y_direction
                    if x_start == x and y_start == y:
                        break

                    tiles_to_flip.append([x_start, y_start])
    board[x][y] = ' '  # restore the empty space
    return tiles_to_flip


def get_valid_moves(board, tile):
    """Check if the move is valid and obtain the result

    Args:
        board (list): the nested list of the game board
        tile (str): the side of the disk, 'X' if dark, 'O' if white

    Returns:
        list: the list of the valid moves
    """
    return [[x, y] for x in range(len(board)) for y in range(len(board[x])) if valid_move(board, tile, x, y)]


@front.route('/api/join', methods=['POST'])
def get_join():
    """get id of the existing games

    Args:
      n/a

    Returns:
      json: the response of the request
    """
    all_hosts = []
    all_items = ddb.get_invites('None', games_table)
    for i in all_items:
        all_hosts.append(str(i['GameId']))
        front.logger.debug('\n* Current pending games: ' + str(i['GameId']))
    return {
        'success': 'true',
        'games': all_hosts
    }


@front.route('/api/create_game', methods=['POST'])
def create_game():
    """Create a new game.

    Args:
      n/a

    Returns:
      json: the response of the request
    """
    player_name = escape(request.form['player_name'].strip())
    if not player_name or player_name == 'None' or player_name == 'draw':
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: Invalid player name.'
            }
        }
    tile = request.form['player_side']
    if not tile:
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: Invalid player side.'
            }
        }
    front.logger.debug('\n* Creating a game with name: ' + str(player_name))
    game_id = str(uuid4())
    response = ddb.create_new_game(game_id, str(player_name), 'None', tile, games_table)
    front.logger.debug(str(response))
    return {
        'success': 'true',
        'game': {
            'id': response['GameId'],
            'time': response['Times']
        }
    }


@front.route('/api/join_game', methods=['POST'])
def join_game():
    """Join an existing game.

    Args:
      n/a

    Returns:
      json: the response of the request
    """
    player_name = escape(request.form['player_name'].strip())
    if not player_name or player_name == 'None' or player_name == 'draw':
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: Invalid player name.'
            }
        }
    game_id = request.form['game_id']
    front.logger.debug(
        '\n* Joining a game with name: ' + str(player_name) + ' and game id: ' + str(game_id))
    game_data = ddb.get(game_id, games_table)
    front.logger.debug(str(game_data))
    if not game_data:
        return {
            'success': 'false',
            'error': {
                'code': 500,
                'message': 'Internal Server Error: dynamoDB error'
            }
        }
    response = ddb.join_existed_game(game_data, games_table, str(player_name))
    front.logger.debug(str(response))
    if response == 'Not a valid game':
        return {
            'success': 'false',
            'error': {
                'code': 404,
                'message': 'Not Found: Invalid game id.'
            }
        }
    return {
        'success': 'true',
        'game': {
            'id': response['GameId'],
            'time': response['Times']
        }
    }
