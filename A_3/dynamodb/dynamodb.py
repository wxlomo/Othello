import boto3
from boto3.dynamodb.conditions import Key
from datetime               import datetime
awsKey={
            'aws_access_key_id' : 'AKIA3NQ4GILKONINMWGT',
            'aws_secret_access_key' : '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'
        }

def createGamesTable():
    db = boto3.resource('dynamodb',
                          region_name='us-east-1',
                          aws_access_key_id=awsKey['aws_access_key_id'],
                          aws_secret_access_key=awsKey['aws_secret_access_key'])

    gamesTable = db.create_table(TableName="Games",
                KeySchema=[
                {'AttributeName': 'GameId', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                {'AttributeName': 'GameId', 'AttributeType': 'S'},
                {'AttributeName': 'OpponentId', 'AttributeType': 'S'},
                {'AttributeName': 'HostId', 'AttributeType': 'S'},
                {'AttributeName': 'StatusDate', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
                },
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'OpponentId',
                        'KeySchema': [
                            {
                                'AttributeName': 'OpponentId',
                                'KeyType': 'HASH',

                            },
                            
                            {
                                'AttributeName': 'StatusDate',
                                'KeyType': 'RANGE',

                            }
                            
                            
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL',
                            
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 1,
                            'WriteCapacityUnits': 1
                        }
                    },
                    {
                        'IndexName': 'HostId',
                        'KeySchema': [
                            {
                                'AttributeName': 'HostId',
                                'KeyType': 'HASH',

                            },
                            
                            {
                                'AttributeName': 'StatusDate',
                                'KeyType': 'RANGE',

                            }
                            
                            
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL',
                            
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 1,
                            'WriteCapacityUnits': 1
                        }
                    }
                ]
                )
    gamesTable.wait_until_exists()
 
    
    return gamesTable

def createNewGame(gameId, creator, invitee, gamesTable):
    games=getGamesWithStatus(creator, "PENDING",gamesTable)
    if games:
        
        return "Exist pending game id:" + games[0]['GameId']
    games=getGamesWithStatus(creator, "INPROGRESS",gamesTable)
    if games:
        return "Exist playing game id:" + games[0]['GameId']
    now = str(datetime.now())
    statusDate = "PENDING_"+now
    item={
            "GameId"     : gameId,
            "HostId"     : creator,
            "StatusDate" : statusDate,
            "OUser"      : creator,
            "Turn"       : invitee,
            "OpponentId" : invitee,
            "Times"       : now,
            "Winner"     : 'unfinished',
            '00'           : ' ',
            '01'           : ' ',
            '02'           : ' ',
            '03'           : ' ',
            '04'           : ' ',
            '05'           : ' ',
            '06'           : ' ',
            '07'           : ' ',
            '10'           : ' ',
            '11'           : ' ',
            '12'           : ' ',
            '13'           : ' ',
            '14'           : ' ',
            '15'           : ' ',
            '16'           : ' ',
            '17'           : ' ',
            '20'           : ' ',
            '21'           : ' ',
            '22'           : ' ',
            '23'           : ' ',
            '24'           : ' ',
            '25'           : ' ',
            '26'           : ' ',
            '27'           : ' ',
            '30'           : ' ',
            '31'           : ' ',
            '32'           : ' ',
            '33'           : 'X',
            '34'           : 'O',
            '35'           : ' ',
            '36'           : ' ',
            '37'           : ' ',
            '40'           : ' ',
            '41'           : ' ',
            '42'           : ' ',
            '43'           : 'O',
            '44'           : 'X',
            '45'           : ' ',
            '46'           : ' ',
            '47'           : ' ',
            '50'           : ' ',
            '51'           : ' ',
            '52'           : ' ',
            '53'           : ' ',
            '54'           : ' ',
            '55'           : ' ',
            '56'           : ' ',
            '57'           : ' ',
            '60'           : ' ',
            '61'           : ' ',
            '62'           : ' ',
            '63'           : ' ',
            '64'           : ' ',
            '65'           : ' ',
            '66'           : ' ',
            '67'           : ' ',
            '70'           : ' ',
            '71'           : ' ',
            '72'           : ' ',
            '73'           : ' ',
            '74'           : ' ',
            '75'           : ' ',
            '76'           : ' ',
            '77'           : ' '
        }
    gamesTable.put_item(
        Item=item    
    )
    return item
    
def updateBoardAndTurn(item, position, current_player, gamesTable):
    # position need to be a list that contain all the place that changed, can be an empty list
    player_one = item["HostId"]
    player_two = item["OpponentId"]
    gameId     = item["GameId"]
    statusDate = item["StatusDate"]
    status=statusDate.split("_")[0]
    if status != 'INPROGRESS':
        return False
    if current_player!=item["Turn"]:
        return False
    representation = "X"
    if item["OUser"] == current_player:
        representation = "O"

    if current_player == player_one:
        next_player = player_two
    else:
        next_player = player_one
    newItem=item
    for p in position:

        gamesTable.update_item(
            Key={'GameId':gameId},
            UpdateExpression="set #p = :r",
            ExpressionAttributeNames={
            '#p' : str(p)
            },
            ExpressionAttributeValues={
                ':r': str(representation)}
            )
    newItem=gamesTable.update_item(
            Key={'GameId':gameId},
            UpdateExpression="set Turn = :r",
            ExpressionAttributeValues={
                ':r': next_player},
            ReturnValues="ALL_NEW"
        )
    return True

def getGame(gameId,gamesTable):
    item=gamesTable.get_item(Key={'GameId':gameId})
    return item

def acceptGameInvite(item, gamesTable, userId):
    
    gameId     = item["GameId"]
    games=getGamesWithStatus(userId, "PENDING",gamesTable)
    if games and games[0]['GameId'] != gameId:
        
        return "Exist pending game id:" + games[0]['GameId']+ " please join with this id"
    if games[0]['GameId'] == gameId:
        return item
    games=getGamesWithStatus(userId, "INPROGRESS",gamesTable)
    if games and games[0]['GameId'] != gameId:
        
        return "Exist playing game id:" + games[0]['GameId']+ " please join with this id"
    if games[0]['GameId'] == gameId:
        return item
    statusDate = item["StatusDate"]
    status=statusDate.split("_")[0]
    if status != 'PENDING':
        return 'Not a valid game'
    date = str(datetime.now())
    status = "INPROGRESS_"
    statusDate = status+date
    userId=str(userId)
    newItem=gamesTable.update_item(
            Key={'GameId':gameId},
            UpdateExpression="set StatusDate = :r, OpponentId = :u, Turn = :t",
            ExpressionAttributeValues={
                ':r': statusDate, ':u':userId, ':t':userId},
            ReturnValues="ALL_NEW"
        )

    return newItem['Attributes']

def rejectGameInvite(item, gamesTable):
    statusDate = item["StatusDate"]
    status=statusDate.split("_")[0]
    if status != 'PENDING':
        return 'Not a valid game'
    gameId     = item["GameId"]
    gamesTable.delete_item(
            Key={'GameId':gameId}
        )

    return True

def getGameInvites(user, gamesTable):

    invites = []
    if user == None:
        return invites

    gameInvites = gamesTable.query(IndexName='OpponentId',
                                        Select='ALL_ATTRIBUTES',
                                        Limit=10,
                                        # KeyConditionExpression='OpponentId = :r AND StatusDate = :s',
                                        KeyConditionExpression=Key('OpponentId').eq(str(user)) & Key('StatusDate').begins_with("PENDING")
                                        # ExpressionAttributeValues={ ":r" : str(user) , ":s" : "PENDING"}
                                        )
    
    gameInvites=gameInvites['Items']
    n=min(10,len(gameInvites))
    for i in range (n-1,-1,-1):
        invites.append(gameInvites[i])
    
    
    return invites

def finishGame(item, gamesTable, winnerId):
    # winnerID: str of winner's id or 'draw'
    statusDate = item["StatusDate"]
    status=statusDate.split("_")[0]
    if status != 'INPROGRESS':
        return 'Not a valid game'
    gameId     = item["GameId"]
    date = str(datetime.now())
    status = "FINISHED_"
    statusDate = status+date

    newItem=gamesTable.update_item(
            Key={'GameId':gameId},
            UpdateExpression="set StatusDate = :r, Times = :t , Winner = :w",
            ExpressionAttributeValues={
                ':r': statusDate , ':t' : date , ':w' : str(winnerId)},
            ReturnValues="ALL_NEW"
        )
    return newItem['Attributes']

def checkResult(item, gamesTable):
    boxes=['00','01','02','03','04','05','06','07','10','11','12','13','14','15','16','17','20','21','22','23','24','25','26','27','30','31','32','33','34','35','36','37','40','41','42','43','44','45','46','47',
        '50','51','52','53','54','55','56','57','60','61','62','63','64','65','66','67','70','71','72','73','74','75','76','77']
    countO=0
    countX=0
    for b in boxes:
        if item[b]==' ':
            return 'unfinished'
        elif item[b]=='O':
            countO+=1
        elif item[b]=='X':
            countX+=1
    if countO>countX:
        return item['HostId']
    if countO<countX:
        return item['OpponentId']
    if countO==countX:
        return 'draw'
    
def makeBoard(item, gamesTable):
    boxes=['00','01','02','03','04','05','06','07','10','11','12','13','14','15','16','17','20','21','22','23','24','25','26','27','30','31','32','33','34','35','36','37','40','41','42','43','44','45','46','47',
        '50','51','52','53','54','55','56','57','60','61','62','63','64','65','66','67','70','71','72','73','74','75','76','77']
    board = []

    for i in range(8):

        board.append([' '] * 8)
    for b in boxes:
        board[int(b[0])][int(b[1])]=item[b]
    return board



def mergeQueries(host, opp, limit=10):
    """
    Taking the two iterators of games you've played in (either host or opponent)
    you sort through the elements taking the top 10 recent games into a list.
    Returns a list of Game objects.
    """
    games = []
    
    i=len(host)-1
    j=len(opp)-1
    
    while len(games) < limit and i>=0 and j >= 0:
        game_one = host[i]
        game_two = opp[j]
        statusDate = game_one["StatusDate"]
        date1=statusDate.split("_")[1]
        date1=datetime.strptime(date1, '%Y-%m-%d %H:%M:%S.%f')
        statusDate = game_two["StatusDate"]
        date2=statusDate.split("_")[1]
        date2=datetime.strptime(date2, '%Y-%m-%d %H:%M:%S.%f')

        if date1> date2:
            games.append(game_one)
            i-=1
        else:
            games.append(game_two)
            j-=1
    if len(games) < limit:
        if i>=0:
            while len(games) < limit and i>=0:
                game_one = host[i]
                games.append(game_one)
                i-=1
        elif j>=0:
            while len(games) < limit and j>=0:
                game_two = opp[j]
                games.append(game_two)
                j-=1
    return games

def getGamesWithStatus(user, status,gamesTable):
    """
    Query for all games that a user appears in and have a certain status.
    Sorts/merges the results of the two queries for top 10 most recent games.
    Return a list of Game objects.
    """

    if user == None:
        return []
    hostGames = gamesTable.query(IndexName='HostId',
                                        Select='ALL_ATTRIBUTES',
                                        Limit=10,
                                        # KeyConditionExpression='OpponentId = :r AND StatusDate = :s',
                                        KeyConditionExpression=Key('HostId').eq(str(user)) & Key('StatusDate').begins_with(status)
                                        # ExpressionAttributeValues={ ":r" : str(user) , ":s" : "PENDING"}
                                        )
    opponentGames = gamesTable.query(IndexName='OpponentId',
                                        Select='ALL_ATTRIBUTES',
                                        Limit=10,
                                        # KeyConditionExpression='OpponentId = :r AND StatusDate = :s',
                                        KeyConditionExpression=Key('OpponentId').eq(str(user)) & Key('StatusDate').begins_with(status)
                                        # ExpressionAttributeValues={ ":r" : str(user) , ":s" : "PENDING"}
                                        )

    games = mergeQueries(hostGames['Items'],
                            opponentGames['Items'])
    return games