import contextlib
import os
from pathlib import Path
import shutil
from typing import Optional

import psutil
import pytest

from volttron.utils.context import ClientContext as cc
# is_web_available
# from volttron.platform import update_platform_config
from volttron.utils.keystore import get_random_key
from volttrontesting.fixtures.cert_fixtures import certs_profile_1
from volttrontesting.platformwrapper import PlatformWrapper, with_os_environ
from volttrontesting.platformwrapper import create_volttron_home
from volttrontesting.utils import get_hostname_and_random_port, get_rand_vip, get_rand_ip_and_port

# from volttron.utils.rmq_mgmt import RabbitMQMgmt
# from volttron.utils.rmq_setup import start_rabbit

PRINT_LOG_ON_SHUTDOWN = False
HAS_RMQ = cc.is_rabbitmq_available()
HAS_WEB = False  # is_web_available()

ci_skipif = pytest.mark.skipif(os.getenv('CI', None) == 'true', reason='SSL does not work in CI')
rmq_skipif = pytest.mark.skipif(not HAS_RMQ,
                                reason='RabbitMQ is not setup and/or SSL does not work in CI')
web_skipif = pytest.mark.skipif(not HAS_WEB, reason='Web libraries are not installed')


def print_log(volttron_home):
    if PRINT_LOG_ON_SHUTDOWN:
        if os.environ.get('PRINT_LOGS', PRINT_LOG_ON_SHUTDOWN):
            log_path = volttron_home + "/volttron.log"
            if os.path.exists(log_path):
                with open(volttron_home + "/volttron.log") as fin:
                    print(fin.read())
            else:
                print('NO LOG FILE AVAILABLE.')


def build_wrapper(vip_address: str, should_start: bool = True, messagebus: str = 'zmq',
                  remote_platform_ca: Optional[str] = None,
                  instance_name: Optional[str] = None, secure_agent_users: bool = False, **kwargs):
    wrapper = PlatformWrapper(ssl_auth=kwargs.pop('ssl_auth', False),
                              messagebus=messagebus,
                              instance_name=instance_name,
                              secure_agent_users=secure_agent_users,
                              remote_platform_ca=remote_platform_ca)
    if should_start:
        wrapper.startup_platform(vip_address=vip_address, **kwargs)
    return wrapper

def build_wrapper_new(vip_address: str, should_start: bool = True, messagebus: str = 'zmq',
                  remote_platform_ca: Optional[str] = None,
                  instance_name: Optional[str] = None, secure_agent_users: bool = False, **kwargs):
    wrapper = PlatformWrapperNew(ssl_auth=kwargs.pop('ssl_auth', False),
                              messagebus=messagebus,
                              instance_name=instance_name,
                              secure_agent_users=secure_agent_users,
                              remote_platform_ca=remote_platform_ca)
    # if should_start:
        # wrapper.startup_platform(vip_address=vip_address, **kwargs)
    return wrapper


def cleanup_wrapper(wrapper):
    print('Shutting down instance: {0}, MESSAGE BUS: {1}'.format(wrapper.volttron_home, wrapper.messagebus))
    # if wrapper.is_running():
    #     wrapper.remove_all_agents()
    # Shutdown handles case where the platform hasn't started.
    wrapper.shutdown_platform()
    if wrapper.p_process is not None:
        if psutil.pid_exists(wrapper.p_process.pid):
            proc = psutil.Process(wrapper.p_process.pid)
            proc.terminate()
    # if not wrapper.debug_mode:
    #     assert not Path(wrapper.volttron_home).parent.exists(), \
    #         f"{str(Path(wrapper.volttron_home).parent)} wasn't cleaned!"


def cleanup_wrappers(platforms):
    for p in platforms:
        cleanup_wrapper(p)



# Generic fixtures. Ideally we want to use the below instead of
# Use this fixture when you want a single instance of volttron platform for
# test
@pytest.fixture(scope="module",
                params=[
                    dict(messagebus='zmq', ssl_auth=False),
                    # pytest.param(dict(messagebus='rmq', ssl_auth=True), marks=rmq_skipif),
                ])
def volttron_instance_new(request, **kwargs):
    """Fixture that returns a single instance of volttron platform for volttrontesting

    @param request: pytest request object
    @return: volttron platform instance
    """
    address = kwargs.pop("vip_address", get_rand_vip())
    # wrapper: PlatformWrapper = build_wrapper(address,
    #                                          messagebus=request.param['messagebus'],
    #                                          ssl_auth=request.param['ssl_auth'],
    #                                          **kwargs)
    wrapper: PlatformWrapperNew = build_wrapper_new(address,
                                             messagebus=request.param['messagebus'],
                                             ssl_auth=request.param['ssl_auth'],
                                             **kwargs)
    wrapper.skip_cleanup = True
    # wrapper.volttron_home = "/tmp/tmpt1gh6ff4/volttron_home"
    wrapper.startup_platform(vip_address=address, **kwargs)
    wrapper_pid = wrapper.p_process.pid

    try:
        yield wrapper
    except Exception as ex:
        print(ex.args)
    finally:
        cleanup_wrapper(wrapper)
        # if not wrapper.debug_mode:
        #     assert not Path(wrapper.volttron_home).exists()
        # Final way to kill off the platform wrapper for the tests.
        if psutil.pid_exists(wrapper_pid):
            psutil.Process(wrapper_pid).kill()


class PlatformWrapperNew(PlatformWrapper):
    def __init__(self, messagebus=None, ssl_auth=False, instance_name=None,
                 secure_agent_users=False, remote_platform_ca=None):
        self.volttron_home = create_volttron_home()
        self.skip_cleanup = True
        super().__init__(messagebus=messagebus, ssl_auth=ssl_auth, instance_name=instance_name,
                         secure_agent_users=secure_agent_users, remote_platform_ca=remote_platform_ca)
        # self.volttron_home = "/tmp/ewerew"  # override self.volttron_home = create_volttron_home()
        """ Initializes a new VOLTTRON instance

                Creates a temporary VOLTTRON_HOME directory with a packaged directory
                for agents that are built.

                :param messagebus: rmq or zmq
                :param ssl_auth: if message_bus=rmq, authenticate users if True
                """

