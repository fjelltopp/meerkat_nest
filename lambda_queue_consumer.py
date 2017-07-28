import boto3
import os

class LambdaQueueHandler():

    def __init__(self):
        region_name = 'eu-west-1'
        self.sns_client = boto3.client('sns', region_name=region_name)
        self.sqs_client = boto3.client('sqs', region_name=region_name)
        self.sts_client = boto3.client('sts', region_name=region_name)

    def get_account_id(self):
        """
        Returns AWS account ID
    
        Returns:\n
            account ID for the configured AWS user\n
        """
        account_id = self.sts_client.get_caller_identity()["Account"]
        return account_id

    def get_queue_url(self, queue_name):
        """
        Creates a queue URL based on given queue name
    
        Returns:\n
            URL for the given queue\n
        """
        response = self.sqs_client.get_queue_url(
            QueueName=queue_name,
            QueueOwnerAWSAccountId=get_account_id()
        )
        return response['QueueUrl']
    
    def get_outgoing_subscriptions(topic_arn):
        """
        Get all subscribers that have subscribed to the output of the Lambda function
        :param topic_arn: ARN of the output topic
        :return: return a list of subscriptions
        """
        subscriptions = []
        response = self.sns_client.list_subscriptions_by_topic(
            TopicArn=topic_arn
        )
        subscriptions += response['Subscriptions']
        next_token = response.get('NextToken', None)
    
        # SNS returns at most 100 subscriptions, concatenate them if needed
        while next_token is not None:
            response = self.sns_client.list_subscriptions_by_topic(
                TopicArn=topic_arn,
                NextToken=next_token
            )
            next_token = response.get('NextToken', None)
            subscriptions += response['Subscriptions']
    
        return subscriptions
    
    
    def get_outgoing_queue(subscriber, incoming_queue):
        return incoming_queue + '-' + subscriber['Endpoint']
    
    
    def get_outgoing_topic():
        """
        Get the topic for outgoing data from Lambda queue consumer
        :return: Topic name where lambda publishes notifications about new data
        """
        return 'nest-outgoing-topic-' + os.environ['ORG'].lower()
    
    
    def get_incoming_data(queue_name, n=1):
        """
        Fetch data from SQS
        :param queue_name: name of the queue with incoming data
        :param n: how many times the receive_message function is run
        :return: returns a list of return values from AWS
        """
        return_set = []
        # TODO empty the whole queue
    
        for i in range(0, n):
            return_set += (self.sqs_client.receive_message(
                QueueUrl=get_queue_url(queue_name),
                MaxNumberOfMessages=10
                )
            )['Messages']
        return return_set
    
    
    def notify_outgoing_subscribers(queue):
        # TODO
        pass
    
    
    def acknowledge_data_entry(queue, data_entry):
        """
        Sends an ACK message to SQS to delete the message from queue
        :param data_entry: data entry returned by SQS receive_message
        :return: AWS delete message return value
        """
        response = self.sqs_client.delete_message(
            QueueUrl=get_queue_url(queue),
            ReceiptHandle=data_entry['ReceiptHandle']
        )
        return response
    
    
    def redirect_data_to_subscriber(subscriber, incoming_queue, data_entry):
        """
        Sends data fetched from the incoming queue to the subscriber and data type specific queues
        :param subscriber: Subscriber to redirect data to
        :param incoming_queue: Queue from where Lambda fetched the data
        :param data_entry: Data entry to be forwarded
        :return: 
        """
        outgoing_queue = get_outgoing_queue(subscriber, incoming_queue)
        queue_response = self.sqs_client.create_queue(
            QueueName=outgoing_queue
        )
        send_data_response = self.sqs_client.send_message(
            QueueUrl=get_queue_url(outgoing_queue),
            MessageBody=json.dumps(data_entry['data'])
        )
        topic = self.sns_client.create_topic(
            Name='get_outgoing_topic_'
        )
    
        pass
        # TODO
    
    
    def lambda_handler(event, context):
        """
        Iterates through the subscribers of a country data flow and distributers data forwards
        :param event: Includes the queue name of the queue that has new data available
        :param context:
        :return: returns information about where the data was forwarded to
        """
        subscriptions = get_outgoing_subscriptions(get_outgoing_topic())
    
        incoming_queue = event['queue']
        incoming_data = get_incoming_data(incoming_queue)
        for data_entry in incoming_data:
            for subscriber in subscriptions:
                redirect_data_to_subscriber(subscriber, incoming_queue, data_entry)
            notify_outgoing_subscribers(incoming_queue)
            acknowledge_data_entry(incoming_queue, data_entry)
    
        return 'Hello from Lambda'
