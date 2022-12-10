import boto3
from datetime               import datetime


def createGamesTable(client):


    gamesTable = client.create_table(TableName="Games",
                KeySchema=[
                {'AttributeName': 'GameId', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                {'AttributeName': 'GameId', 'AttributeType': 'S'}
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
                            'NonKeyAttributes': [
                                'string'
                            ]
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 1,
                            'WriteCapacityUnits': 1
                        }
                    },
                ]
                )

    gamesTable.wait_until_exists()
    
    return gamesTable

def createNewGame(gameId, creator, invitee, gamesTable):
    now = str(datetime.now())
    statusDate = "PENDING"
    item={
            "GameId"     : gameId,
            "HostId"     : creator,
            "StatusDate" : statusDate,
            "OUser"      : creator,
            "Turn"       : invitee,
            "OpponentId" : invitee,
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
    player_one = item["HostId"]
    player_two = item["OpponentId"]
    gameId     = item["GameId"]
    statusDate = item["StatusDate"]
    # date = statusDate.split("_")[1]

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
    return newItem

def getGame(gameId,gamesTable):
    item=gamesTable.get_item(Key={'GameId':gameId})
    return item

def acceptGameInvite(item, gamesTable):

    gameId     = item["GameId"]
    date = str(datetime.now())
    status = "IN_PROGRESS"
    statusDate = status

    newItem=gamesTable.update_item(
            Key={'GameId':gameId},
            UpdateExpression="set StatusDate = :r",
            ExpressionAttributeValues={
                ':r': statusDate},
            ReturnValues="ALL_NEW"
        )

    return newItem

def rejectGameInvite(item, gamesTable):
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
                                        KeyConditionExpression='OpponentId = :r AND StatusDate = :s',
                                        ExpressionAttributeValues={ ":r" : user , ":s" : "PENDING"}
                                        )
    invites=gameInvites['Items']
    return invites