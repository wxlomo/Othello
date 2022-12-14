"""
 * frontend.py
 * front-end interface and router of the othello web application
 *
 * Author: Weixuan Yang
 * Date: Dec. 11, 2022
"""
import boto3
from . import front, config, dynamodb as ddb
from flask import render_template, request, g, redirect, escape, jsonify
from uuid import uuid4


def get_db():
    """Get the game table.
    Args:
      n/a
    Returns:
      dynamoDB Object: data
    """
    if 'db' not in g:
        dynamodb_client = boto3.client('dynamodb',
                                       region_name=config.aws_key['aws_region'],
                                       aws_access_key_id=config.aws_key['aws_access_key_id'],
                                       aws_secret_access_key=config.aws_key['aws_secret_access_key'])
        dynamodb = boto3.resource('dynamodb',
                                  region_name=config.aws_key['aws_region'],
                                  aws_access_key_id=config.aws_key['aws_access_key_id'],
                                  aws_secret_access_key=config.aws_key['aws_secret_access_key'])
        if 'Games' not in dynamodb_client.list_tables()['TableNames']:
            ddb.create_game_table()
        g.game_table = dynamodb.Table('Games')
    return g.game_table


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
    all_items = ddb.get_invites('None', get_db())
    for i in all_items:
        all_hosts.append(str(i['GameId']))
        front.logger.debug('\n* Current pending games: ' + str(i['GameId']))
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
    player_name = escape(request.form['player_name'].strip())
    if not player_name or player_name == 'None' or player_name == 'draw':
        return render_template('result.html', title='Invalid Player Name', message='Do not use spaces/None/draw as your player name')
    tile = request.form['player_side']
    front.logger.debug('\n* Creating a game with name: ' + str(player_name))
    game_id = str(uuid4())
    response = ddb.create_new_game(game_id, str(player_name), 'None', tile, get_db())
    front.logger.debug(str(response))
    return redirect('/game/' + str(game_id) + '/' + str(player_name))


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
        return render_template('result.html', title='Invalid Player Name', message='Do not use spaces as your player name')
    game_id = request.form['game_id']
    front.logger.debug(
        '\n* Joining a game with name: ' + str(player_name) + ' and game id: ' + str(game_id))
    game_data = ddb.get(game_id, get_db())
    if not game_data:
        return render_template('result.html', title='Fail to Join the Game',
                               message='The game you want to join does not exist, please try again.')
    front.logger.debug(str(game_data))
    response = ddb.join_existed_game(game_data, get_db(), str(player_name))
    if response == 'Not a valid game':
        return render_template('result.html', title='Fail to Join the Game',
                               message='The game you want to join does not exist, please try again.')
    return redirect('/game/' + str(game_id) + '/' + str(player_name))


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
    game_data = ddb.get(game_id, get_db())
    front.logger.debug(str(game_data))
    if not game_data:
        return render_template('result.html', title='500 Internal Server Error', message='Failed to render the game board.')
    status = game_data["Statusnow"]
    if status == 'Finished':
        return refresh(game_id, player_name)
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
                    ddb.update_turn(game_data, [], player_name, get_db())
                else:
                    player_score = ddb.count_disks(game_data, tile)
                    foe_score = ddb.count_disks(game_data, other_tile)
                    front.logger.debug('\n* Game end with: ' + str(player_score) + ' vs ' + str(foe_score))
                    if player_name == game_data['HostId']:
                        foe_name = game_data['FoeId']
                    else:
                        foe_name = game_data['HostId']
                    if player_score > foe_score:
                        ddb.finish_game(game_data, get_db(), player_name)
                    elif player_score < foe_score:
                        ddb.finish_game(game_data, get_db(), foe_name)
                    else:
                        ddb.finish_game(game_data, get_db(), 'draw')
            board = board_render(game_id, player_name, game_board, moves)
        else:
            message = 'Now it is your foe ' + str(foe_name) + "'s turn!"
            board = board_render(game_id, player_name, game_board, [])
    return render_template('game.html', board=board, surr='/game/' + str(game_id)+'/' + str(player_name) + '/surrender', message=message)


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
    game_data = ddb.get(game_id, get_db())
    front.logger.debug(str(game_data))
    if not game_data:
        return render_template('result.html', title='500 Internal Server Error', message='Failed to render the game board.')
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
    print(valid)
    print(position)
    ddb.update_turn(game_data, position, player_name, get_db())
    front.logger.debug('\n* A move is made on game: ' + str(game_id) + ' at ' + str(loc))
    return redirect('/game/' + str(game_id) + '/' + str(player_name))


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
    game_data = ddb.get(game_id, get_db())
    front.logger.debug(str(game_data))
    if player_name == game_data['HostId']:
        winner = game_data['FoeId']
    else:
        winner = game_data['HostId']
    ddb.finish_game(game_data, get_db(), winner)
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
    game_data = ddb.get(game_id, get_db())
    status = game_data["Statusnow"]
    turn = game_data["Turn"]

    return jsonify(gameId=game_id, status=status, turn=turn)


@front.route('/game/<game_id>/<player_name>/refresh')
def refresh(game_id, player_name):
    """Refresh the game board, check if the game is finished

    Args:
      game_id (str): the identity of the game
      player_name (str): the name of the player

    Returns:
      str: the arguments for the Jinja template
    """
    if not player_name or not game_id:
        return render_template('result.html', title='403 Forbidden', message='This page is not reachable.')
    game_data = ddb.get(game_id, get_db())
    front.logger.debug(str(game_data))
    status = game_data["Statusnow"]
    if status == 'Finished':
        if game_data['OUser'] == player_name:
            tile = 'O'
        else:
            tile = 'X'
        player_score = ddb.count_disks(game_data, tile)
        front.logger.debug('\n* The player' + str(player_name) + ' has score ' + str(player_score))
        winner = game_data['Winner']
        # response = ddb.teardown(game_id, get_db())
        # front.logger.debug(str(response))
        if winner == player_name:
            # upload the final score to the ranking
            return render_template('result.html', title='You Win :)',
                                   message='Your final score is ' + str(player_score) + '.')
        elif winner != 'draw':
            return render_template('result.html', title='You Lose :(',
                                   message='Your final score is ' + str(player_score) + '.')
        else:
            return render_template('result.html', title='Draw...', message='Your final score is ' + str(player_score) + '.')
    else:
        front.logger.debug('\n* Refreshing the game board')
        return redirect('/game/' + str(game_id) + '/' + str(player_name))


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
    updated_board = board
    updated_list = []
    if valid_moves:
        for x, y in valid_moves:
            updated_board[x][y] = '.'
    for x in range(len(updated_board)):
        for y in range(len(updated_board[x])):
            current_disk = updated_board[x][y]
            if current_disk == 'X':
                updated_list.append('<img src="/static/img/dark.svg">')
            elif current_disk == 'O':
                updated_list.append('<img src="/static/img/light.svg">')
            elif current_disk == '.':
                updated_list.append(
                    '<input type="image" src="/static/img/placeable.svg" alt="Submit" class="placeable" formaction="/game/'
                    + str(game_id) + '/' + str(player_name) + '/move/' + str(index[x][y]) + '">')
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
