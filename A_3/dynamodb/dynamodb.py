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
            '11'           : ' ',
            '12'           : ' ',
            '13'           : ' ',
            '14'           : ' ',
            '15'           : ' ',
            '16'           : ' ',
            '17'           : ' ',
            '18'           : ' ',
            '21'           : ' ',
            '22'           : ' ',
            '23'           : ' ',
            '24'           : ' ',
            '25'           : ' ',
            '26'           : ' ',
            '27'           : ' ',
            '28'           : ' ',
            '31'           : ' ',
            '32'           : ' ',
            '33'           : ' ',
            '34'           : ' ',
            '35'           : ' ',
            '36'           : ' ',
            '37'           : ' ',
            '38'           : ' ',
            '41'           : ' ',
            '42'           : ' ',
            '43'           : ' ',
            '44'           : 'O',
            '45'           : 'X',
            '46'           : ' ',
            '47'           : ' ',
            '48'           : ' ',
            '51'           : ' ',
            '52'           : ' ',
            '53'           : ' ',
            '54'           : 'X',
            '55'           : 'O',
            '56'           : ' ',
            '57'           : ' ',
            '58'           : ' ',
            '61'           : ' ',
            '62'           : ' ',
            '63'           : ' ',
            '64'           : ' ',
            '65'           : ' ',
            '66'           : ' ',
            '67'           : ' ',
            '68'           : ' ',
            '71'           : ' ',
            '72'           : ' ',
            '73'           : ' ',
            '74'           : ' ',
            '75'           : ' ',
            '76'           : ' ',
            '77'           : ' ',
            '78'           : ' ',
            '81'           : ' ',
            '82'           : ' ',
            '83'           : ' ',
            '84'           : ' ',
            '85'           : ' ',
            '86'           : ' ',
            '87'           : ' ',
            '88'           : ' '
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

def acceptGameInvite(item, gamesTable):

    gameId     = item["GameId"]
    statusDate = item["StatusDate"]
    status=statusDate.split("_")[0]
    if status != 'PENDING':
        return 'Not a valid game'
    date = str(datetime.now())
    status = "INPROGRESS_"
    statusDate = status+date

    newItem=gamesTable.update_item(
            Key={'GameId':gameId},
            UpdateExpression="set StatusDate = :r",
            ExpressionAttributeValues={
                ':r': statusDate},
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
    print(gameInvites)
    invites=gameInvites['Items']
    
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
    boxes=['11','12','13','14','15','16','17','18','21','22','23','24','25','26','27','28','31','32','33','34','35','36','37','38','41','42','43','44','45','46','47',
        '48','51','52','53','54','55','56','57','58','61','62','63','64','65','66','67','68','71','72','73','74','75','76','77','78','81','82','83','84','85','86','87','88']
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
    boxes=['11','12','13','14','15','16','17','18','21','22','23','24','25','26','27','28','31','32','33','34','35','36','37','38','41','42','43','44','45','46','47',
        '48','51','52','53','54','55','56','57','58','61','62','63','64','65','66','67','68','71','72','73','74','75','76','77','78','81','82','83','84','85','86','87','88']
    board = []

    for i in range(8):

        board.append([' '] * 8)
    for b in boxes:
        board[int(b[0])-1][int(b[1])-1]=item[b]
    return board