
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder
from PyQt5.QtCore import QThread


class getOSCMessages(QThread):

    def __init__(self, IP=None, Port=None, soma=None):
        QThread.__init__(self)
        self.IP = IP
        self.Port = Port
        self.soma = soma
        self.TABLE_FORWARDING = soma.TABLE_FORWARDING
        self.dispatcher_osc = dispatcher.Dispatcher()
        self.dispatcher_osc.set_default_handler(self.OSC_handler, needs_reply_address=True)

        self.server = osc_server.ThreadingOSCUDPServer((self.IP, self.Port), self.dispatcher_osc)

    def __del__(self):
        self.wait()

    def run(self):
        print("Serving on {}".format(self.server.server_address))
        self.server.serve_forever()

    def OSC_handler(self, address, *args):
        client_IP = address[0]
        #client_Port = address[1]
        address_client = args[0]
        msg = args[1]

        for rows in range(len(self.TABLE_FORWARDING)):
            if self.TABLE_FORWARDING.iloc[rows]['Sensor Address'] == address_client and self.TABLE_FORWARDING.iloc[rows]['Sensor IP'] == client_IP:
                sensor_range = self.TABLE_FORWARDING.iloc[rows]['Sensor Range'].split("%")
                actuator_range = self.TABLE_FORWARDING.iloc[rows]['Actuator Range'].split("%")
                # Map values
                value = self.maprange((float(sensor_range[0]), float(sensor_range[1])),
                                        (float(actuator_range[0]), float(actuator_range[1])), float(msg))
                # Send values
                client = udp_client.SimpleUDPClient(str(self.TABLE_FORWARDING.iloc[rows]['Actuator IP']), int(self.TABLE_FORWARDING.iloc[rows]['Actuator Port']))
                client.send_message(self.TABLE_FORWARDING.iloc[rows]['Actuator Address'], value)

                print("Value = %s" % value)

    def maprange(self, a, b, s):
        (a1, a2), (b1, b2) = a, b
        return b1 + ((s - a1) * (b2 - b1) / (a2 - a1))



