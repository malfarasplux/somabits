import logging
import sys
import socket
import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (Qt, pyqtSignal)
import ifaddr


from gui import Ui_MainWindow

from typing import cast
from zeroconf import ServiceInfo,ServiceBrowser, ServiceStateChange, Zeroconf
from typing import List

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

TYPE = '_osc._udp.local.'
NAME = 'Server'


class StartQT5(QtWidgets.QMainWindow):
    def __init__(self):
        super(StartQT5, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.discover_button.clicked.connect(self.zeroconf_start)
        self.ui.save_button.clicked.connect(self.start_forwarding)
        self.TABLE_INFO = pd.DataFrame(columns=['Address', 'Port', 'Server', 'Device Count', 'Device Type', 'Device Address', 'Device Range', '*'])
        self.TABLE_NOT_ACCESSIBLE = pd.DataFrame(columns=['Address'])

        self.model = PandasModel(self.TABLE_INFO)
        self.ui.tableView.setModel(self.model)
        #self.ui.tableView.hideColumn(0)

    def start_forwarding(self):

        sensors = []
        actuators = []
        forward_table=pd.DataFrame()
        for rows in range(len(self.TABLE_INFO)):
            for devices in range(self.TABLE_INFO.iloc[rows]['Device Count']):

                if(True):
                    if('sensor' in str(self.TABLE_INFO.iloc[rows]['Device Type'][devices])):
                        sensors.append(self.TABLE_INFO.iloc[rows]['Device Address'][devices])
                    else:
                        actuators.append(self.TABLE_INFO.iloc[rows]['Device Address'][devices])

        forward_table = pd.DataFrame(index=sensors,columns=actuators)
        model=PandasModel(forward_table)
        self.ui.tableView_2.setModel(model)

        for rows in range(model.rowCount()):
            for column in range(model.columnCount()):
                self.Checkbox = QtWidgets.QCheckBox(' ')
                self.Checkbox.setAccessibleName('hello')
                self.Checkbox.setAccessibleDescription('hello')
                self.Checkbox.clicked.connect(self.handleCheckboxClicked)

                checkBoxWidget = QtWidgets.QWidget()
                layoutCheckBox = QtWidgets.QHBoxLayout(checkBoxWidget)
                layoutCheckBox.addWidget(self.Checkbox)
                layoutCheckBox.setAlignment(Qt.AlignCenter);

                item = model.index(rows, column )
                self.ui.tableView_2.setIndexWidget(item, self.Checkbox)

        self.ui.tableView_2.setModel(model)

    def resizeEvent(self, event):
        tableSize = self.ui.tableView.width()  # Retrieves your QTableView width
        sideHeaderWidth = self.ui.tableView.verticalHeader().width()  # Retrieves the left header width
        tableSize -= sideHeaderWidth  # Perform a substraction to only keep all the columns width
        numberOfColumns = self.model.columnCount()  # Retrieves the number of columns

        for columnNum in range(self.model.columnCount()):  # For each column
            self.ui.tableView.setColumnWidth(columnNum,
                                     int(tableSize / numberOfColumns))  # Set the width = tableSize / nbColumns
        super(StartQT5, self).resizeEvent(event)  # Restores the original behaviour of the resize event

    def handleCheckboxClicked(self):
        Checkbox = QtWidgets.qApp.focusWidget()
        if Checkbox.isChecked():
            self.discovery.register_service(Checkbox.accessibleName(), Checkbox.accessibleDescription())
        else:

            self.discovery.unregister_service(Checkbox.accessibleName(), Checkbox.accessibleDescription())

    def handleServiceAdded(self, info, name):
        device_type = []
        device_address = []
        device_range = []

        self.ui.plainTextEdit.appendPlainText(
            "  Address: %s:%d" % (socket.inet_ntoa(cast(bytes, info.address)), cast(int, info.port)))
        self.ui.plainTextEdit.appendPlainText(
            "  Weight: %d, priority: %d, ttl: %s" % (info.weight, info.priority, info.ttl))
        self.ui.plainTextEdit.appendPlainText("  Server: %s" % (info.server,))

        if info.properties:
            self.ui.plainTextEdit.appendPlainText("  Properties are:")

            for key, value in info.properties.items():
                self.ui.plainTextEdit.appendPlainText("    %s: %s" % (key, value))
                key_str = str(key).split("'")[1]
                device_type.append(key_str)
                if ":" in str(value):
                    # the device has sensor values
                    value_str = str(value).split("'")[1].split(':')
                    device_address.append(value_str[0])
                    device_range.append(value_str[1])
                else:
                    # the device does not have sensor values
                    value_str = str(value).split("'")[1]
                    device_address.append(value_str)
        else:
            print("  No properties")

        if (socket.inet_ntoa(cast(bytes, info.address)) not in self.TABLE_INFO["Address"].to_list()):

            if (socket.inet_ntoa(cast(bytes, info.address)) == NeighborDiscovery().get_local_ip()):
                pass  # ignore own server message

            elif ('Server' in str(info.server)):  # if its a Server side message other than our own
                self.TABLE_NOT_ACCESSIBLE.loc[len(self.TABLE_NOT_ACCESSIBLE)] = [
                    device_address[1]]  # Add connected device IP address to TABLE_NOT_ACCESSIBLE
                if (device_address[1] in self.TABLE_INFO[
                    "Address"].to_list()):  # If device IP address already exist in TABLE_INFO, remove it
                    self.TABLE_INFO = self.TABLE_INFO[self.TABLE_INFO["Address"] != device_address[1]]
                    self.model.removeRows(device_address[1])

            elif (socket.inet_ntoa(cast(bytes, info.address)) not in self.TABLE_NOT_ACCESSIBLE[
                "Address"].to_list()):  # If IP address is not in TABLE_NOT_ACCESSIBLE
                self.TABLE_INFO.loc[len(self.TABLE_INFO)] = [
                    socket.inet_ntoa(cast(bytes, info.address)), cast(int, info.port), info.server,
                    len(device_type), device_type, device_address, device_range, ""]

                self.Checkbox = QtWidgets.QCheckBox(' ')
                self.Checkbox.setAccessibleName(socket.inet_ntoa(cast(bytes, info.address)))
                self.Checkbox.setAccessibleDescription(name)
                self.Checkbox.clicked.connect(self.handleCheckboxClicked)

                checkBoxWidget = QtWidgets.QWidget()
                layoutCheckBox = QtWidgets.QHBoxLayout(checkBoxWidget)
                layoutCheckBox.addWidget(self.Checkbox)
                layoutCheckBox.setAlignment(Qt.AlignCenter);

                item = self.model.index(self.model.rowCount() - 1, self.model.columnCount() - 1)
                self.ui.tableView.setIndexWidget(item, self.Checkbox)

                self.model.insertRows()

        self.ui.plainTextEdit.appendPlainText('\n')

    def handleServiceRemoved(self, name):
        pass


    def on_device_found(self, zeroconf, service_type, name, state_change):
        self.ui.plainTextEdit.appendPlainText(
            "Service %s of type %s state changed: %s" % (name, service_type, state_change))

        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                self.handleServiceAdded(info, name)
        elif state_change is ServiceStateChange.Removed:
            print("Service Removed")
            self.handleServiceRemoved(name)

    def zeroconf_start(self):
        self.discovery = NeighborDiscovery()
        self.discovery.neighbor_signal.connect(self.on_device_found)


class NeighborDiscovery(QtCore.QThread):
    neighbor_signal = QtCore.pyqtSignal(object, object, object, object)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, TYPE, handlers=[self.on_service_state_change])

    def on_service_state_change(self,zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange, ) -> None:
        self.neighbor_signal.emit(zeroconf, service_type, name, state_change)

    def register_service(self, ip, service_name):
        TXT_record = {'server': self.get_local_ip()}
        TXT_record.update({"device": ip})

        name = service_name.split('.')[0]
        name = NAME + "_" + name

        print(name)

        info = ServiceInfo(type_="_osc._udp.local.",
                           name=name + "." + TYPE,
                           address=socket.inet_aton(self.get_local_ip()),
                           port=80,
                           weight=0,
                           priority=0,
                           properties=TXT_record,
                           server=name + ".local.")

        print("Registration of a service %s" % (name))
        self.zeroconf.register_service(info)

    def unregister_service(self, ip, service_name):
        name = NAME + "_" + service_name

        print(name)

        info = self.zeroconf.get_service_info(TYPE, name)
        if info:
            self.zeroconf.unregister_service(info)
            print("Unregistering service %s with IP %s" % (name, ip))


    def get_all_addresses(self) -> List[str]:
        return list(set(
            addr.ip
            for iface in ifaddr.get_adapters()
            for addr in iface.ips
            if addr.is_IPv4 and addr.network_prefix != 32  # Host only netmask 255.255.255.255
        ))

    def get_local_ip(self, starts_with="192"):
        list_ip = self.get_all_addresses()
        local_ip = [i for i in list_ip if i.startswith(starts_with)]
        return local_ip[0]


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df = pd.DataFrame(), parent=None):
        QtCore.QAbstractTableModel.__init__(self)
        self._df = df

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == QtCore.Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError, ):
                return QtCore.QVariant()
        elif orientation == QtCore.Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return self._df.index.tolist()[section]
            except (IndexError, ):
                return QtCore.QVariant()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if not index.isValid():
            return QtCore.QVariant()

        return QtCore.QVariant(str(self._df.ix[index.row(), index.column()]))

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        print(index.row())
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        if hasattr(value, 'toPyObject'):
            # PyQt4 gets a QVariant
            value = value.toPyObject()
        else:
            # PySide gets an unicode
            dtype = self._df[col].dtype
            if dtype != object:
                value = None if value == '' else dtype.type(value)
        self._df.set_value(row, col, value)
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending= order == QtCore.Qt.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

    def insertRows(self):
        self.layoutAboutToBeChanged.emit()
        self._df.append(self._df.tail(1))
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

    def removeRows(self, row):
        print("==============")
        print(self._df)
        self.layoutAboutToBeChanged.emit()
        # self._df.drop([row], axis='index')
        self._df = self._df[self._df['Address'] != row]
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()
        print("--------------")
        print(self._df)
        print("==============")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) > 1:
        assert sys.argv[1:] == ['--debug']
        logging.getLogger('zeroconf').setLevel(logging.DEBUG)


    app = QtWidgets.QApplication(sys.argv)
    myapp = StartQT5()
    myapp.show()
    sys.exit(app.exec_())
    #sys.exit(myapp.close(app))