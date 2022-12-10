import dynamodb
import boto3
awsKey={
            'aws_access_key_id' : 'AKIA3NQ4GILKONINMWGT',
            'aws_secret_access_key' : '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'
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
    print(client.list_tables()['TableNames'])
    if 'Games' in client.list_tables()['TableNames']:
        db.delete_table(
        TableName='Games'
        )
    
    dynamodb.createGamesTable()
    print(client.list_tables()['TableNames'])
    gamesTable=db.Table('Games')
    item1=dynamodb.createNewGame('1', '2', '3', gamesTable)
    print(item1)
    # item1=dynamodb.acceptGameInvite(item1,gamesTable)
    # print(item1)
    item2=dynamodb.createNewGame('11', '2', '33', gamesTable)
    print(item2)
    invite=dynamodb.getGameInvites(2, gamesTable)
    print(invite)
    # dynamodb.rejectGameInvite(item2, gamesTable)
    