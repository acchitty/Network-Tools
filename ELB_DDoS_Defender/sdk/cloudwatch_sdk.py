"""
CloudWatch SDK for logging and metrics
"""
import boto3
import time
from datetime import datetime

class CloudWatchSDK:
    def __init__(self, log_group='/aws/elb-monitor', region='us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
        self.log_group = log_group
        self.log_stream = f'monitor-{datetime.now().strftime("%Y-%m-%d")}'
        self.sequence_token = None
        self._setup_log_group()
    
    def _setup_log_group(self):
        """Create log group and stream if they don't exist"""
        try:
            self.logs_client.create_log_group(logGroupName=self.log_group)
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        
        try:
            self.logs_client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self.log_stream
            )
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass
    
    def put_log(self, message):
        """Send log message to CloudWatch Logs"""
        try:
            log_event = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': [{
                    'timestamp': int(time.time() * 1000),
                    'message': message
                }]
            }
            
            if self.sequence_token:
                log_event['sequenceToken'] = self.sequence_token
            
            response = self.logs_client.put_log_events(**log_event)
            self.sequence_token = response.get('nextSequenceToken')
            return True
        except Exception as e:
            print(f"CloudWatch Logs error: {e}")
            return False
    
    def put_metric(self, metric_name, value, dimensions=None, unit='Count'):
        """Send custom metric to CloudWatch"""
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.now()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace='ELB/Monitor',
                MetricData=[metric_data]
            )
            return True
        except Exception as e:
            print(f"CloudWatch Metrics error: {e}")
            return False
