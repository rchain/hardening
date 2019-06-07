from orchestrator.main import Hostname


def test_hostname():
    hostname = Hostname('hardnet1-orchestrator.c.developer-222401.internal')

    assert hostname.get_instance_name() == 'hardnet1-orchestrator'
    assert hostname.get_domain() == 'c.developer-222401.internal'

    new_hostname = hostname.with_instance_name('hardnet1-node0')
    assert new_hostname.get_instance_name() == 'hardnet1-node0'
    assert new_hostname.get_domain() == 'c.developer-222401.internal'
