import json
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key, Attr
def lambda_handler(event, context):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    deadlinenow = datetime.now() - timedelta(hours=1)
    table_name = 'Games'
    table = dynamodb.Table(table_name)
    event_name = ''
    response = []
    key = ''
    if 'Records' in event and event['Records'][0]['eventSource'] == 'aws:dynamodb':
        event_name = event['Records'][0]['eventName']
        
    if event_name == "INSERT":
        response = table.scan(
            FilterExpression=Attr("Times").lt(str(deadlinenow))
        )
        for item in response['Items']:
            
            key = {
            'GameId': item['GameId']
            }
            table.delete_item(Key=key)
              
    return {
        'statusCode': 200,
        'time': str(deadlinenow),
        'response': response,
        'key' : key,
        'body': json.dumps('Item Deleted')
    }
  
  def lambda_handler(event, context):
    table_name = "Games"
    attribute_name = "Statusnow"
    attribute_value = "Pending"
    attribute_value2 = "Playing"
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table(table_name)
    result = table.scan(
        FilterExpression=f"{attribute_name} = :val",
        ExpressionAttributeValues={
            ":val": attribute_value
        }
    )
    result2 = table.scan(
        FilterExpression=f"{attribute_name} = :val",
        ExpressionAttributeValues={
            ":val": attribute_value2
        }
    )
    total = len(result["Items"])+(len(result2["Items"])*2)
    
    return "Current Player Online:" + str(total)
           
