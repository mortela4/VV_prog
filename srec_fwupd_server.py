#!/usr/bin/python3

"""
@file srec_fwupd_server.py
@brief Completely stand-alone multithreaded UDP FW-update server.
"""
import datetime
import locale

locale.setlocale(locale.LC_ALL, "")

from multiprocessing import Process
import socketserver
import threading
import re


pool = None


def parse_sensor_id(data):
    """ Decode and validate data for sensor-ID. """
    from common import common_logging as log

    sensor_id = None    # probably redundant - if data=None then data.encode()=None ...

    log.ERR("test")
    # Format of sensor-ID is "nn-nnnn-XX-nnnnn" where 'n' denotes digit and 'X' denotes letter.
    SENSOR_ID_PROTO = '[0-9][0-9]-[0-9][0-9][0-9][0-9]-[a-z,A-Z][a-z,A-Z]-[0-9][0-9][0-9][0-9][0-9]'
    #
    if data is not None:
        try:
            sensor_id = data.decode('ascii')
        except UnicodeDecodeError:
            log.ERR("Invalid data for sensor-ID - cannot decode to ASCII string!")
            return None
        if len(sensor_id) != 16:
            log.ERR("invalid sensor-ID length - cannot parse '%s'!" % sensor_id)
            return None
        if not re.match(SENSOR_ID_PROTO, sensor_id):
            log.ERR("invalid sensor-ID format - cannot parse '%s'!" % sensor_id)
            return None
    else:
        log.ERR("No data for sensor-ID - cannot decode and validate!")
    #
    return sensor_id


"""
# ******************** UDP threaded socket server ************************
class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):
    #
    from . import socket_num_pool as port_num_pool
    #
    from common import common_logging as log
    from common import settings
    from . import srec_fw_updater

    run_flag = True
    debug = False

    def handle(self):
        global pool
        if pool is None:
            pool = port_num_pool.SocketNumPool(settings.UPDATE_PORT_START + 1, settings.UPDATE_PORT_POOL_SIZE)
        #
        rx_data = self.request[0]
        sock = self.request[1]
        current_thread = threading.current_thread()
        # Debug:
        if self.debug:
            log.DBG("{}: client: {}, sent: {}".format(current_thread.name, self.client_address, rx_data))
        # Parse sensor ID:
        uid = parse_sensor_id(rx_data)
        if uid:
            log.DBG("Starting FW-update for UID = %s" % uid)
        else:
            log.ERR("Illegal data - could not parse UID! Terminating update-thread ...")
            return


        # Error-injection pr.1 - update terminated after init:
        if settings.ERROR_INJECTION["startup_fail"]:
            return

        # ACK to target:
        port_num = pool.GetNextSocketNum()
        sock.sendto(bytes(str(port_num), encoding='ascii'), self.client_address)
        #
        # Basic resolution of firmware file from UID:
        update_process_log_file = settings.LOG_DIR + \
                                      ("FW-update_%s_%s.log" %
                                       (uid, datetime.datetime.now().strftime("%b%d-%Y-%H.%M.%S.%f")))
        # Start background process.
        p_upd = Process(target=srec_fw_updater.run_srec_update,
                        args=(port_num, uid, self.debug, update_process_log_file))
        p_upd.start()
        p_upd.join()
        # Return socket port number to pool:
        pool.FreeSocketNum(port_num)
        # Check status from updater process:
        if p_upd.exitcode != 0:
            log.ERR("Updater process failed for target ID = %s!" % uid)
        else:
            log.DBG("Successful update of target with ID = %s" % uid)  # TODO: add more info(?).
        # Thread termination here after correct update-sequence:
        return


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass
"""

if __name__ == "__main__":
    """ No code here - run 'main.py' to test! """
    print("This is not a module supposed to be run stand-alone; run 'main.py' to test it!")

    # However, it IS possible to (unit-)test function parse_sensor_id():
    # ==================================================================
    # Test1: ID invalid format.
    test_data = b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
    sensor_id = parse_sensor_id(test_data)
    if sensor_id:
        print("Sensor-ID : ", sensor_id)
    # Test2: ID too short.
    test_data = b'00-0000-AA-0000'
    sensor_id = parse_sensor_id(test_data)
    if sensor_id:
        print("Sensor-ID : ", sensor_id)
    # Test2: ID too long.
    test_data = b'00-0000-AA-000000'
    sensor_id = parse_sensor_id(test_data)
    if sensor_id:
        print("Sensor-ID : ", sensor_id)
    # Test3a: ID invalid format.
    test_data = b'00-0000-A9-000000'
    sensor_id = parse_sensor_id(test_data)
    if sensor_id:
        print("Sensor-ID : ", sensor_id)
    # Test3b: ID invalid format.
    test_data = b'00-0000-AA-000A00'
    sensor_id = parse_sensor_id(test_data)
    if sensor_id:
        print("Sensor-ID : ", sensor_id)
    # Test4: no data.
    test_data = None
    sensor_id = parse_sensor_id(test_data)
    if sensor_id:
        print("Sensor-ID : ", sensor_id)
    # Test5: PASS!
    test_data = b'21-1020-AA-01234'
    sensor_id = parse_sensor_id(test_data)
    if sensor_id:
        print("Sensor-ID : ", sensor_id)





