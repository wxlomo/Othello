"""
 * frontend.py
 * front-end interface and router of the gallery web application
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
"""
import dynamodb as ddb
import boto3
import hashlib
from . import front, config
from flask import render_template, request, escape, jsonify, session, redirect

global db
global game_entry
global dbclient


@front.before_first_request
def init():
    """Create game tables

    Args:
      n/a

    Returns:
      n/a
    """
    global db
    global game_entry
    global dbclient
    dbclient = boto3.client('dynamodb',
                            region_name=config.aws_key['aws_region'],
                            aws_access_key_id=config.aws_key['aws_access_key_id'],
                            aws_secret_access_key=config.aws_key['aws_secret_access_key'])
    db = boto3.resource('dynamodb',
                        region_name=config.aws_key['aws_region'],
                        aws_access_key_id=config.aws_key['aws_access_key_id'],
                        aws_secret_access_key=config.aws_key['aws_secret_access_key'])
    if 'Games' not in dbclient.list_tables()['TableNames']:
        ddb.createGamesTable()
    game_entry = db.Table('Games')


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
    all_hosts = ddb.getGameInvites('None', game_entry)['GameId']
    front.logger.debug('\n* Current pending games: ' + str(all_hosts))
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
    player_name = request.form['player_name'].strip()
    if player_name or player_name == 'None':
        session['player_name'] = player_name.strip()
    else:
        return render_template('result', title='Invalid Player Name', message='Do not use spaces as your player name')
    # layer_side = request.form['player_side']  # do not support choosing side
    front.logger.debug('\n* Creating a game with name: ' + str(session['player_name']))
    game_id = str(hashlib.md5(player_name.encode('utf-8')).hexdigest())
    response = ddb.createNewGame(game_id, str(session['player_name']), 'None', game_entry)
    front.logger.debug(str(response))
    return redirect('/game/' + str(game_id))


@front.route('/join_game', methods=['POST'])
def join_game():
    """Join an existing game.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    player_name = request.form['player_name'].strip()
    if player_name or player_name == 'None':
        session['player_name'] = player_name.strip()
    else:
        return render_template('result', title='Invalid Player Name', message='Do not use spaces as your player name')
    game_id = request.form['game_id']
    front.logger.debug('\n* Joining a game with name: ' + str(session["player_name"]) + ' and game id: ' + str('game_id'))
    response = ddb.getGame(game_id, game_entry)
    front.logger.debug(str(response))
    if not response:
        return render_template('result', title='Fail to Join the Game', message='The game you want to join does not exist, please try again.')
    response = ddb.acceptGameInvite(response, game_entry, str(session["player_name"]))
    front.logger.debug(str(response))
    return redirect('/game/' + str(game_id))


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
    response = ddb.getGame(game_id, game_entry)
    front.logger.debug(str(response))
    if not response:
        return render_template('result', title='500 Internal Server Error', message='Failed to render the game board.')
    game_data = ddb.makeBoard(response, game_entry)
    board = board_render(game_id, player_name, disks)
    if len(board) != 64:
        return render_template('result', title='500 Internal Server Error', message='Failed to render the game board.')
    foe_name = game_data['OpponentId']
    front.logger.debug('\n* Current game board: ' + str(board) + ', current foe name: ' + str(foe_name))
    if not foe_name or foe_name == 'None':
        message = 'Waiting for another player to join...'
    else:
        if game_data['Turn'] == str(player_name):
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
    # need loc and tiles to flip
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
    game_data = ddb.getGame(game_id, game_entry)
    front.logger.debug(str(game_data))
    if player_name == game_data['HostId']:
        winner = game_data['OpponentId']
    else:
        winner = game_data['HostId']
    ddb.finishGame(game_data, game_entry, winner)
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
    game_data = ddb.getGame(game_id, game_entry)
    front.logger.debug(str(game_data))
    status = game_data["StatusDate"].split("_")[0]
    if status == 'FINISHED':
        if game_data['HostId'] == player_name:
            player_side = 'O'
        else:
            player_side = 'X'
        player_score = ddb.count_disks(game_data, player_side)
        front.logger.debug('\n* The player' + str(player_name) + ' has score ' + str(player_score))
        winner = game_data['Winner']
        if player_name == winner:
            # upload the final score to the ranking
            return render_template('result', title='You Win :)', message='Your final score is ' + str(player_score) + '.')
            # Your final score is ' + str(player_score) +
        elif winner != 'draw':
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
    index = [[outer * 10 + inner for inner in range(9)] for outer in range(9)]
    grid = []  # Preprocess: mark the lattices as dark, light, or placeable, size must be 64,
    board = []
    for row in range(len(index)):
        for lattice in range(len(index[row])):
            current_disk = grid[row][lattice]
            if current_disk == 'X':
                board.append('<img src="src/img/dark.svg">')
            elif current_disk == 'O':
                board.append('<img src="src/img/light.svg">')
            elif current_disk == 'placeable':
                board.append('<input type="image" src="src/img/placeable.svg" alt="Submit" class="placeable" formaction="/game/' + str(game_id) + '/move/' + index[row][lattice] + '">')
            else:
                board.append(' ')
    return board


def isOnBoard(x, y):
# Returns True if the coordinates are located on the board.
  return x >= 0 and x <= 7 and y >= 0 and y <=7

def isValidMove(board, tile, xstart, ystart):

  # Returns False if the player's move on space xstart, ystart is invalid.

  # If it is a valid move, returns a list of spaces that would become the player's if they made a move here.

  if board[xstart][ystart] != ' ' or not isOnBoard(xstart, ystart):
      return False
  board[xstart][ystart] = tile # temporarily set the tile on the board.

  if tile == 'X':
      otherTile = 'O'
  else:
      otherTile = 'X'

  tilesToFlip = []
  for xdirection, ydirection in [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]:
      x, y = xstart, ystart
      x += xdirection # first step in the direction
      y += ydirection # first step in the direction
      if isOnBoard(x, y) and board[x][y] == otherTile:
          # There is a piece belonging to the other player next to our piece.
          x += xdirection
          y += ydirection
          if not isOnBoard(x, y):
              continue
          while board[x][y] == otherTile:
              x += xdirection
              y += ydirection
              if not isOnBoard(x, y): # break out of while loop, then continue in for loop
                  break
          if not isOnBoard(x, y):
              continue
          if board[x][y] == tile:
              # There are pieces to flip over. Go in the reverse direction until we reach the original space, noting all the tiles along the way.
              while True:
                  x -= xdirection
                  y -= ydirection
                  if x == xstart and y == ystart:
                      break
                  tilesToFlip.append([x, y])



  board[xstart][ystart] = ' ' # restore the empty space

  if len(tilesToFlip) == 0: # If no tiles were flipped, this is not a valid move.

      return False

  return tilesToFlip

def getValidMoves(board, tile):

 # Returns a list of [x,y] lists of valid moves for the given player on the given board.
  validMoves = []
  for x in range(8):
    for y in range(8):
      if isValidMove(board, tile, x, y) != False:
        validMoves.append([x, y])
  return validMoves

def getBoardWithValidMoves(board, tile):
  # Returns a new board with . marking the valid moves the given player can make.
  dupeBoard = []
  for i in range(8):
    dupeBoard.append([' '] * 8)
  for x in range(8):
    for y in range(8):
      dupeBoard[x][y] = board[x][y]
  for x, y in getValidMoves(dupeBoard, tile):
      dupeBoard[x][y] = '.'
  return dupeBoard
