from boto3.dynamodb.conditions import Key
from datetime import datetime


def get(game_id, games_table):
    game = games_table.get_item(Key={'GameId': game_id})
    if 'Item' in game:
        return game['Item']
    else:
        return False


def teardown(game_id, games_table):
    games_table.delete_item(
        Key={'GameId': game_id}
    )
    return 'Successfully delete entry ' + str(game_id)


def create_new_game(game_id, creator, joiner, creator_side, games_table):
    games = get_games_status(creator, "Pending", games_table)
    if games:
        return games
    games = get_games_status(creator, "Playing", games_table)
    if games:
        return games
    if creator_side == 'x':
        o_user = joiner
    else:
        o_user = creator
    status = "Pending"
    now = str(datetime.now())
    item = {
        "GameId": game_id,
        "HostId": creator,
        "FoeId": joiner,
        "Statusnow": status,
        "OUser": o_user,
        "Turn": ' ',
        "Times": now,
        "Winner": 'unfinished',
        '00': ' ',
        '01': ' ',
        '02': ' ',
        '03': ' ',
        '04': ' ',
        '05': ' ',
        '06': ' ',
        '07': ' ',
        '10': ' ',
        '11': ' ',
        '12': ' ',
        '13': ' ',
        '14': ' ',
        '15': ' ',
        '16': ' ',
        '17': ' ',
        '20': ' ',
        '21': ' ',
        '22': ' ',
        '23': ' ',
        '24': ' ',
        '25': ' ',
        '26': ' ',
        '27': ' ',
        '30': ' ',
        '31': ' ',
        '32': ' ',
        '33': 'X',
        '34': 'O',
        '35': ' ',
        '36': ' ',
        '37': ' ',
        '40': ' ',
        '41': ' ',
        '42': ' ',
        '43': 'O',
        '44': 'X',
        '45': ' ',
        '46': ' ',
        '47': ' ',
        '50': ' ',
        '51': ' ',
        '52': ' ',
        '53': ' ',
        '54': ' ',
        '55': ' ',
        '56': ' ',
        '57': ' ',
        '60': ' ',
        '61': ' ',
        '62': ' ',
        '63': ' ',
        '64': ' ',
        '65': ' ',
        '66': ' ',
        '67': ' ',
        '70': ' ',
        '71': ' ',
        '72': ' ',
        '73': ' ',
        '74': ' ',
        '75': ' ',
        '76': ' ',
        '77': ' '
    }
    games_table.put_item(
        Item=item
    )
    return item


def update_turn(item, position, current_player, games_table):
    host = item["HostId"]
    foe = item["FoeId"]
    game_id = item["GameId"]
    status = item["Statusnow"]
    if status != 'Playing' or current_player != item["Turn"]:
        return False
    if item["OUser"] == current_player:
        color = "O"
    else:
        color = "X"
    if current_player == host:
        next_player = foe
    else:
        next_player = host
    new_item = item
    for p in position:
        games_table.update_item(
            Key={'GameId': game_id},
            UpdateExpression="set #p = :r",
            ExpressionAttributeNames={
                '#p': str(p)
            },
            ExpressionAttributeValues={
                ':r': str(color)}
        )
    new_item = games_table.update_item(
        Key={'GameId': game_id},
        UpdateExpression="set Turn = :r",
        ExpressionAttributeValues={
            ':r': next_player},
        ReturnValues="ALL_NEW"
    )
    return True


def join_existed_game(item, games_table, user_id):
    game_id = item["GameId"]
    games = get_games_status(user_id, "Pending", games_table)
    if games:
        return "Exist pending game id:" + games['GameId']
    games = get_games_status(user_id, "Playing", games_table)
    if games:
        return "Exist playing game id:" + games['GameId']
    status = item["Statusnow"]
    host_id = item["HostId"]
    if status != 'Pending':
        return 'Not a valid game'
    status = "Playing"
    if item["OUser"] != host_id:
        new_item = games_table.update_item(
            Key={'GameId': game_id},
            UpdateExpression="set FoeId = :u, Statusnow = :r, OUser = :o, Turn = :t",
            ExpressionAttributeValues={
                ':u': str(user_id), ':r': status, ':o': str(user_id), ':t': str(host_id)},
            ReturnValues="ALL_NEW"
        )
    else:
        new_item = games_table.update_item(
            Key={'GameId': game_id},
            UpdateExpression="set Statusnow = :r, FoeId = :u, Turn = :t",
            ExpressionAttributeValues={
                ':r': status, ':u': str(user_id), ':t': str(user_id)},
            ReturnValues="ALL_NEW"
        )
    return new_item['Attributes']


def get_invites(user, games_table):
    invites = []
    if not user:
        return invites

    game_invites = games_table.query(IndexName='FoeId',
                                     Select='ALL_ATTRIBUTES',
                                     Limit=10,
                                     # KeyConditionExpression='FoeId = :r AND Status = :s',
                                     KeyConditionExpression=Key('FoeId').eq(str(user)) & Key(
                                         'Statusnow').begins_with("Pending")
                                     # ExpressionAttributeValues={ ":r" : str(user) , ":s" : "Pending"}
                                     )['Items']
    n = min(10, len(game_invites))
    for i in range(n - 1, -1, -1):
        invites.append(game_invites[i])
    return invites


def finish_game(item, games_table, winner_id):
    # winnerID: str of winner's id or 'draw'
    if item["Statusnow"] != 'Playing':
        return 'Not a valid game'
    game_id = item["GameId"]
    status = "Finished"
    status = status
    date = str(datetime.now())
    new_item = games_table.update_item(
        Key={'GameId': game_id},
        UpdateExpression="set Statusnow = :r, Times = :t , Winner = :w",
        ExpressionAttributeValues={
            ':r': status, ':t': date, ':w': str(winner_id)},
        ReturnValues="ALL_NEW"
    )
    return new_item['Attributes']


def check_result(item):
    count_o = count_disks(item, 'O')
    count_x = count_disks(item, 'X')
    if count_o > count_x:
        return item['HostId']
    elif count_o < count_x:
        return item['FoeId']
    else:
        return 'draw'


def count_disks(item, color):
    boxes = ['00', '01', '02', '03', '04', '05', '06', '07', '10', '11', '12', '13', '14', '15', '16', '17', '20', '21',
             '22', '23', '24', '25', '26', '27', '30', '31', '32', '33', '34', '35', '36', '37', '40', '41', '42', '43',
             '44', '45', '46', '47',
             '50', '51', '52', '53', '54', '55', '56', '57', '60', '61', '62', '63', '64', '65', '66', '67', '70', '71',
             '72', '73', '74', '75', '76', '77']
    count = 0
    for b in boxes:
        if item[b] == color:
            count += 1
    return count


def make_board(item):
    boxes = ['00', '01', '02', '03', '04', '05', '06', '07', '10', '11', '12', '13', '14', '15', '16', '17', '20', '21',
             '22', '23', '24', '25', '26', '27', '30', '31', '32', '33', '34', '35', '36', '37', '40', '41', '42', '43',
             '44', '45', '46', '47',
             '50', '51', '52', '53', '54', '55', '56', '57', '60', '61', '62', '63', '64', '65', '66', '67', '70', '71',
             '72', '73', '74', '75', '76', '77']
    board = []
    for i in range(8):
        board.append([' '] * 8)
    for b in boxes:
        board[int(b[0])][int(b[1])] = item[b]
    return board


def get_games_status(user, status, games_table):
    if not user:
        return None
    host_games = games_table.query(IndexName='HostId',
                                   Select='ALL_ATTRIBUTES',
                                   Limit=10,
                                   # KeyConditionExpression='FoeId = :r AND Status = :s',
                                   KeyConditionExpression=Key('HostId').eq(str(user)) & Key('Statusnow').begins_with(
                                       status)
                                   # ExpressionAttributeValues={ ":r" : str(user) , ":s" : "Pending"}
                                   )
    foe_games = games_table.query(IndexName='FoeId',
                                  Select='ALL_ATTRIBUTES',
                                  Limit=10,
                                  # KeyConditionExpression='FoeId = :r AND Status = :s',
                                  KeyConditionExpression=Key('FoeId').eq(str(user)) & Key(
                                      'Statusnow').begins_with(status)
                                  # ExpressionAttributeValues={ ":r" : str(user) , ":s" : "Pending"}
                                  )
    if host_games['Items']:
        return host_games['Items'][0]
    elif foe_games['Items']:
        return foe_games['Items'][0]
    else:
        return None
