"""
Meerkat Nest Deactivation Test

Unit tests Meerkat Nest Deactivation functionality
"""

import meerkat_nest
import copy
import meerkat_nest.util
from meerkat_nest import app
from meerkat_nest.test.test_data.upload_payload import upload_payload, processed_upload_payload
from meerkat_nest import message_service
from unittest import mock
import unittest
import logging
import json


class MeerkatNestDeactivationTest(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        """Setup for testing"""

        app.config.from_object('config.Testing')

        # Only show warning level+ logs from boto3, botocore and nose.
        # Too verbose otherwise.
        logging.getLogger('boto3').setLevel(logging.WARNING)
        logging.getLogger('botocore').setLevel(logging.WARNING)
        logging.getLogger('nose').setLevel(logging.WARNING)

    def setUp(self):
        self.queue_name = 'nest-queue-demo'
        self.dead_letter_queue_name = 'nest-dead-letter-queue-demo-record'
        self.topic = 'nest-incoming-topic-demo'
        self.topic_arn = 'aws123:nest-incoming-topic-demo'
        self.data_entry = upload_payload
        self.processed_data_entry = processed_upload_payload

    def tearDown(self):
        pass

    # test upload data flow
    @mock.patch('meerkat_nest.resources.upload_data.validate_request')
    @mock.patch('meerkat_nest.resources.upload_data.upload_to_raw_data')
    @mock.patch('meerkat_nest.message_service.send_data')
    def test_valid_upload(self, mock_send_data, mock_upload_to_raw_data, mock_validate_request):
        pass

    # test processing data
    def test_data_processing(self):
        # TODO: Test scrambling

        # TODO: Test column name conversion
        pass

    # Test sending data to SQS
    @mock.patch('meerkat_nest.message_service.sns_client.publish')
    @mock.patch('meerkat_nest.message_service.sns_client.create_topic')
    @mock.patch('meerkat_nest.message_service.sts_client.get_caller_identity')
    @mock.patch('meerkat_nest.message_service.sqs_client.get_queue_url')
    @mock.patch('meerkat_nest.message_service.sqs_client.create_queue')
    @mock.patch('meerkat_nest.message_service.sqs_client.send_message')
    def test_data_sending(self, mock_send_message, mock_create_queue, mock_get_queue_url, mock_get_caller_identity,
                          mock_create_topic, mock_publish):
        mock_get_caller_identity.return_value = {'Account': 'test_account'}
        mock_get_queue_url.return_value = {'QueueUrl': 'http://queue-url.test'}

        delete_data_entry = copy.deepcopy(self.data_entry)
        delete_data_entry['data'] = 'delete'
        message_service.send_deactivation_message(self.data_entry)

        # Check that SQS queue is created
        self.assertTrue(mock_create_queue.called)
        mock_create_queue.assert_called_with(
            QueueName=self.queue_name
        )

        # Check that the notification for new messages is sent
        self.assertTrue(mock_send_message.called)

        # TODO: json.dumps does not guarantee the order of key-value pairs
        #mock_send_message.assert_called_with(
        #    QueueUrl='http://queue-url.test',
        #    MessageBody=json.dumps(delete_data_entry)
        #)

    # Test notifying SNS about new data
    @mock.patch('meerkat_nest.message_service.sns_client.publish')
    @mock.patch('meerkat_nest.message_service.sns_client.create_topic')
    def test_notifying(self, mock_create_topic, mock_publish):
        mock_create_topic.return_value = {'TopicArn': self.topic_arn}

        message_service.notify_sns(self.queue_name, self.dead_letter_queue_name)

        message = {
            "queue": self.queue_name,
            "dead-letter-queue": self.dead_letter_queue_name
        }

        # Check that SNS topic is created
        self.assertTrue(mock_create_topic.called)
        mock_create_topic.assert_called_with(
            Name=self.topic
        )

        # Check that the notification for new messages is sent
        self.assertTrue(mock_publish.called)
        mock_publish.assert_called_with(
            TopicArn=self.topic_arn,
            Message=json.dumps({'default': json.dumps(message)}),
            MessageStructure='json'
        )



