import pytest
import tftest


@pytest.fixture
def plan(terraform_dir):
    #import pdb; pdb.set_trace()
    tf = tftest.TerraformTest('vpc', terraform_dir)
    return tf.plan(output=True)


def test_tags(plan):
    """
    Collect all resources that will be tagged. Confirm that the all contain our expected
    tag keys
    """
    expected_tag_keys = set(['Environment', 'User'])
    # Captures all of the tags from our plan
    resource_changes = plan.resource_changes
    resource_tags = [ v['change']['after']['tags'] for v in resource_changes.values() if 'tags' in v['change']['after']]
    assert all([ set(expected_tag_keys).issubset(tags.keys()) for tags in resource_tags ])

def test_nat_redundancy(plan):
    """
    Given we want to configure one NAT Gateway per public subnet, confirm
    the length of these two values match
    """
    created_resources = plan.resource_changes.keys()
    subnet_resource_name = 'module.vpc.aws_subnet.public'
    nat_resource_name = 'module.vpc.aws_nat_gateway'
    public_subnet_resources = [ resource for resource in created_resources if resource.startswith(subnet_resource_name) ]
    nat_resources = [ resource for resource in created_resources if resource.startswith(nat_resource_name) ]

    assert len(public_subnet_resources) == len(nat_resources)

def test_ipv6_disabled(plan):
    """
    Confirm no subnets have an IPv6 block specified
    """
    created_resources = plan.resource_changes
    subnet_changes = [ v['change']['after'] for k, v in created_resources.items() if 'module.vpc.aws_subnet' in k ]
    assert not all([change['ipv6_cidr_block'] for change in subnet_changes])