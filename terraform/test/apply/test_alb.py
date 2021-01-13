import pytest
import boto3
import tftest
import requests
import time

TEST_HTTP_REQUEST_TIMEOUT = 2 #seconds
AWS_REGION = 'us-east-1'

@pytest.fixture(scope='session')
def terraform_outputs(terraform_dir):
    tf = tftest.TerraformTest('alb_example', terraform_dir)
    tf.setup()
    tf.apply()
    # This is kind of hacky, but we need to give the alb targets
    # time to become healthy.
    time.sleep(30)
    yield tf.output()
    tf.destroy()

@pytest.fixture()
def ec2_client():
    return boto3.client('ec2', AWS_REGION)

@pytest.fixture()
def alb_client():
    boto3.client('elbv2', AWS_REGION)

def test_outputs(terraform_outputs):
    assert terraform_outputs

def test_http_response_from_alb(terraform_outputs):
    alb_dns = "http://{}".format(terraform_outputs['alb_public_dns'])
    r = requests.get(alb_dns, timeout=TEST_HTTP_REQUEST_TIMEOUT)
    assert r.status_code == 200
    assert r.text == "<p> Let's start testing! </p>\n"

def test_no_http_response_from_instances(terraform_outputs):
    ec2_dns = terraform_outputs['ec2_public_dns']
    if not isinstance(ec2_dns, list):
        ec2_dns = list(ec2_dns)
    ec2_dns = [ "http://{}".format(d) for d in ec2_dns ]
    expectedException = requests.exceptions.ConnectTimeout
    with pytest.raises(expectedException, match=r".*Connection to.*timed out.*"):
        for d in ec2_dns:
            requests.get(d, timeout=TEST_HTTP_REQUEST_TIMEOUT)


def test_availability_with_impared_instance(terraform_outputs, ec2_client):
    one_ec2_instance = terraform_outputs['ec2_instance_ids'][0]
    ec2_client.stop_instances(InstanceIds=[one_ec2_instance], Force=True)
    waiter = ec2_client.get_waiter('instance_stopped')
    waiter.wait(InstanceIds=[one_ec2_instance])

    alb_dns = "http://{}".format(terraform_outputs['alb_public_dns'])
    r = requests.get(alb_dns, timeout=TEST_HTTP_REQUEST_TIMEOUT)
    assert r.status_code == 200
    assert r.text == "<p> Let's start testing! </p>\n"

def test_target_group_reporting_unhealthy(terraform_outputs):
    pass