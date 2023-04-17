"""
This test suits focus on the exposed RPC calls.
It utilizes a vip agent to evoke the RPC calls.
The volltron instance and dnp3-agent is start manually.
Note: need to define VOLTTRON_HOME at pytest.ini
    and vip-identity for dnp3 outstation agent (default "dnp3_outstation")
Note: several fixtures are used
    volttron_platform_wrapper_new
    vip_agent
    dnp3_outstation_agent
"""
import pathlib

import gevent
import pytest
import os
from volttron.client.vip.agent import build_agent
from time import sleep
import datetime
from dnp3_outstation.agent import Dnp3OutstationAgent
from dnp3_python.dnp3station.outstation_new import MyOutStationNew
import random
import subprocess
from volttron.utils import is_volttron_running
import json
from utils.testing_utils import *

dnp3_vip_identity = "dnp3_outstation"


@pytest.fixture(scope="module")
def volttron_home():
    """
    VOLTTRON_HOME environment variable suggested to setup at pytest.ini [env]
    """
    volttron_home: str = os.getenv("VOLTTRON_HOME")
    assert volttron_home
    return volttron_home


def test_volttron_home_fixture(volttron_home):
    assert volttron_home
    print(volttron_home)


def test_testing_file_path():
    parent_path = os.getcwd()
    dnp3_agent_config_path = os.path.join(parent_path, "dnp3-outstation-config.json")
    # print(dnp3_agent_config_path)
    logging_logger.info(f"test_testing_file_path {dnp3_agent_config_path}")


# from volttrontesting.fixtures.volttron_platform_fixtures import volttron_instance
# @pytest.fixture(scope="module")
# def volttron_platform_wrapper_new(volttron_instance):
#
#     volttron_home = volttron_instance.volttron_home
#     print(f"==== 1st, is_volttron_running at volttron_home={volttron_home}:  {is_volttron_running(volttron_home)}")
#     # start the platform, check status with flexible retry
#     # process = subprocess.Popen(["volttron"])  # use Popen, no-blocking
#
#     retry_call(f=is_volttron_running, f_kwargs=dict(volttron_home=volttron_home), max_retries=100, delay_s=2,
#                pass_criteria=True)
#     print(f"==== 2nd, is_volttron_running at volttron_home={volttron_home}:  {is_volttron_running(volttron_home)}")
#     if not is_volttron_running(volttron_home):
#         raise Exception("VOLTTRON platform failed to start with volttron_home: {volttron_home}.")
#
#     yield volttron_home
#     # TODO: add clean up options to remove volttron_home
#     # subprocess.Popen(["vctl", "shutdown", "--platform"])
#     volttron_instance
#     retry_call(f=is_volttron_running, f_kwargs=dict(volttron_home=volttron_home), max_retries=100, delay_s=1,
#                wait_before_call_s=2,
#                pass_criteria=False)
#     print(f"==== 3rd, is_volttron_running at volttron_home={volttron_home}:  {is_volttron_running(volttron_home)}")


from utils.platform_fixture_new import volttron_instance_new

def test_volttron_instance_new_fixture(volttron_instance_new):
    print(volttron_instance_new)
    logging_logger.info(f"=========== volttron_instance_new.volttron_home: {volttron_instance_new.volttron_home}")
    logging_logger.info(f"=========== volttron_instance_new.skip_cleanup: {volttron_instance_new.skip_cleanup}")
    logging_logger.info(f"=========== volttron_instance_new.vip_address: {volttron_instance_new.vip_address}")

@pytest.fixture(scope="module")
def vip_agent(volttron_instance_new):
    # build a vip agent
    a = volttron_instance_new.build_agent()
    print(a)
    return a


def test_vip_agent_fixture(vip_agent):
    print(vip_agent)
    logging_logger.info(f"=========== vip_agent: {vip_agent}")
    logging_logger.info(f"=========== vip_agent.core.identity: {vip_agent.core.identity}")
    logging_logger.info(f"=========== vip_agent.vip.peerlist().get(): {vip_agent.vip.peerlist().get()}")


@pytest.fixture(scope="module")
def dnp3_outstation_agent(volttron_instance_new) -> dict:
    """
    Install and start a dnp3-outstation-agent, return its vip-identity
    """
    # install a dnp3-outstation-agent
    parent_path = os.getcwd()
    dnp3_outstation_package_path = pathlib.Path(parent_path).parent
    dnp3_agent_config_path = os.path.join(parent_path, "dnp3-outstation-config.json")
    config = {
        "outstation_ip": "0.0.0.0",
        "master_id": 2,
        "outstation_id": 1,
        "port":  20000
    }
    agent_vip_id = dnp3_vip_identity
    uuid = volttron_instance_new.install_agent(agent_dir=dnp3_outstation_package_path,
                            config_file=config,
                            start=False,
                            vip_identity=agent_vip_id)
    # start agent with retry
    pid = retry_call(volttron_instance_new.start_agent, f_kwargs=dict(agent_uuid=uuid), max_retries=5, delay_s=2,
                     wait_before_call_s=2)
    # check if running with retry
    retry_call(volttron_instance_new.is_agent_running, f_kwargs=dict(agent_uuid=uuid), max_retries=5, delay_s=2,
                     wait_before_call_s=2)
    return {"uuid": uuid, "pid": pid}


def test_install_dnp3_outstation_agent_fixture(dnp3_outstation_agent, vip_agent, volttron_instance_new):
    puid = dnp3_outstation_agent
    print(puid)
    logging_logger.info(f"=========== dnp3_outstation_agent ids: {dnp3_outstation_agent}")
    logging_logger.info(f"=========== vip_agent.vip.peerlist().get(): {vip_agent.vip.peerlist().get()}")
    logging_logger.info(f"=========== volttron_instance_new.is_agent_running(puid): "
                        f"{volttron_instance_new.is_agent_running(dnp3_outstation_agent['uuid'])}")


def test_dummy(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.rpc_dummy
    peer_method = method.__name__  # "rpc_dummy"
    rs = vip_agent.vip.rpc.call(peer, peer_method).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)


def test_outstation_reset(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.reset_outstation
    peer_method = method.__name__  # "reset_outstation"
    rs = vip_agent.vip.rpc.call(peer, peer_method).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)


def test_outstation_get_db(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.display_outstation_db
    peer_method = method.__name__  # "display_outstation_db"
    rs = vip_agent.vip.rpc.call(peer, peer_method).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)


def test_outstation_get_config(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.get_outstation_config
    peer_method = method.__name__  # "get_outstation_config"
    rs = vip_agent.vip.rpc.call(peer, peer_method).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)


def test_outstation_is_connected(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.is_outstation_connected
    peer_method = method.__name__  # "is_outstation_connected"
    rs = vip_agent.vip.rpc.call(peer, peer_method).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)


def test_outstation_apply_update_analog_input(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.apply_update_analog_input
    peer_method = method.__name__  # "apply_update_analog_input"
    val, index = random.random(), random.choice(range(5))
    print(f"val: {val}, index: {index}")
    rs = vip_agent.vip.rpc.call(peer, peer_method, val, index).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)

    # verify
    val_new = rs.get("Analog").get(str(index))
    assert val_new == val


def test_outstation_apply_update_analog_output(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.apply_update_analog_output
    peer_method = method.__name__  # "apply_update_analog_output"
    val, index = random.random(), random.choice(range(5))
    print(f"val: {val}, index: {index}")
    rs = vip_agent.vip.rpc.call(peer, peer_method, val, index).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)

    # verify
    val_new = rs.get("AnalogOutputStatus").get(str(index))
    assert val_new == val


def test_outstation_apply_update_binary_input(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.apply_update_binary_input
    peer_method = method.__name__  # "apply_update_binary_input"
    val, index = random.choice([True, False]), random.choice(range(5))
    print(f"val: {val}, index: {index}")
    rs = vip_agent.vip.rpc.call(peer, peer_method, val, index).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)

    # verify
    val_new = rs.get("Binary").get(str(index))
    assert val_new == val


def test_outstation_apply_update_binary_output(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.apply_update_binary_output
    peer_method = method.__name__  # "apply_update_binary_output"
    val, index = random.choice([True, False]), random.choice(range(5))
    print(f"val: {val}, index: {index}")
    rs = vip_agent.vip.rpc.call(peer, peer_method, val, index).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)

    # verify
    val_new = rs.get("BinaryOutputStatus").get(str(index))
    assert val_new == val


def test_outstation_update_config_with_restart(vip_agent, dnp3_outstation_agent):
    peer = dnp3_vip_identity
    method = Dnp3OutstationAgent.update_outstation
    peer_method = method.__name__  # "update_outstation"
    port_to_set = 20001
    rs = vip_agent.vip.rpc.call(peer, peer_method, port=port_to_set).get(timeout=5)
    print(datetime.datetime.now(), "rs: ", rs)

    # verify
    rs = vip_agent.vip.rpc.call(peer, "get_outstation_config").get(timeout=5)
    port_new = rs.get("port")
    # print(f"========= port_new {port_new}")
    assert port_new == port_to_set
