import dynamodb
import boto3
awsKey={
            'aws_access_key_id' :,
            'aws_secret_access_key' :
        }
if __name__ == '__main__':
    client = boto3.client('dynamodb',
                          region_name='us-east-1',
                          aws_access_key_id=awsKey['aws_access_key_id'],
                          aws_secret_access_key=awsKey['aws_secret_access_key'])
    db = boto3.resource('dynamodb',
                          region_name='us-east-1',
                          aws_access_key_id=awsKey['aws_access_key_id'],
                          aws_secret_access_key=awsKey['aws_secret_access_key'])
    # print(client.list_tables()['TableNames'])
    # if 'Games' in client.list_tables()['TableNames']:
    #     db.delete_table(
    #     TableName='Games'
    #     )
    if 'Games' not in client.list_tables()['TableNames']:
        dynamodb.createGamesTable()
    print(client.list_tables()['TableNames'])
    gamesTable=db.Table('Games')
    item1=dynamodb.createNewGame('1', '3', '2', gamesTable)
    print(item1)
    # item1=dynamodb.acceptGameInvite(item1,gamesTable)
    # print(item1)
    item2=dynamodb.createNewGame('11', '33', '2', gamesTable)
    print(item2)
    invite=dynamodb.getGameInvites(2, gamesTable)
    print(invite)
    # dynamodb.rejectGameInvite(item2, gamesTable)
    game1=dynamodb.acceptGameInvite(invite[0],gamesTable)
    print(game1)
    game1=dynamodb.updateBoardAndTurn(game1, ['11','12'], game1['Turn'], gamesTable)
    print(game1)
    game1=dynamodb.updateBoardAndTurn(game1, ['21','12'], game1['Turn'], gamesTable)
    print(game1)
    game1=dynamodb.finishGame(game1, gamesTable, game1['HostId'])
    print(game1)