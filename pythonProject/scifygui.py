from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton
from PyQt5.QtCore import QTimer
from PyQt5.uic import loadUi
from opcua import OPCUAConnection
from asyncua.sync import Client
import asyncio
from asyncua import ua
import time
from datetime import datetime

# async def call_method_async(opcua_client, node_id, method_name, args):
#     method_node = opcua_client.get_node(node_id)
#     input_args = [ua.Variant(arg, ua.VariantType.Variant) for arg in args]
#     result = await method_node.call_method(method_name, *input_args)
#     return result

async def call_method_async(opcua_conn, node_id, method_name, *args):
    try:
        # get the node and method objects from the server
        node = await opcua_conn.get_node(node_id)
        method = await node.get_child([ua.QualifiedName(4, method_name)])

        # call the method on the server
        result = await method.call(*args)
        return result

    except Exception as e:
        print(f"Error calling RPC method: {e}")


class MainWindow(QMainWindow):
    def __init__(self, opcua_conn):
        super(MainWindow, self).__init__()
        # save the OPC UA connection
        self.opcua_conn = opcua_conn

        # set up the main window
        self.ui = loadUi('main_window.ui', self)

        # print("self.opcua_conn in MainWindow", self.opcua_conn)
        # Show Delay line window
        self.ui.main_pb_delay_lines.clicked.connect(self.open_delay_lines)

        # Dl status on main window
        self.load_dl1_status()

        # update the temp values
        self.update_cryo_temps()

        self.t = QTimer()
        self.t.timeout.connect(self.refresh_status)
        self.t.start(10000)

    def closeEvent(self, *args):
        self.t.stop()
        self.opcua_conn.disconnect()
        super().closeEvent(*args)

    def refresh_status(self):
        try:
            self.load_dl1_status()
            self.update_cryo_temps()

            now = datetime.utcnow()
            fileName = r'C:\Users\fys-lab-ivs\Documents\Python Scripts\Log\Temperatures_' \
                            + now.strftime(r'%Y-%m-%d') + '.csv'

            f = open(fileName, 'a')
            f.write(f'{str(now)}, {self.temp1}, {self.temp2}, {self.temp3}, {self.temp4} \n')
        except Exception as e:
            print(e)



    def open_delay_lines(self):

        try:

            self.delay_lines_window = DelayLinesWindow(self.opcua_conn)
            self.delay_lines_window.show()
            print("Dl window is opening fine")


            # set the OPC UA connection on the delay lines window
            # print("self.opcua_conn in set_opcua_conn", self.opcua_conn)
            # self.delay_lines_window.set_opcua_conn(self.opcua_conn)

        except Exception as e:
            print(f"Error opening delay lines window: {e}")

    def load_dl1_status(self):

        self.ui.label_dl_status.setText(str(self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.sStatus")))
        self.ui.label_dl_state.setText(str(self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.sState")))

    def update_cryo_temps(self):
        # update the value in the delay lines window
        self.temp1 = str(self.opcua_conn.read_node("ns=4;s=GVL_Cryo_Temperatures.Temp_1"))
        self.ui.main_label_temp1.setText(self.temp1)

        self.temp2 = str(self.opcua_conn.read_node("ns=4;s=GVL_Cryo_Temperatures.Temp_2"))
        self.ui.main_label_temp2.setText(self.temp2)

        self.temp3 = str(self.opcua_conn.read_node("ns=4;s=GVL_Cryo_Temperatures.Temp_3"))
        self.ui.main_label_temp3.setText(self.temp3)

        self.temp4 = str(self.opcua_conn.read_node("ns=4;s=GVL_Cryo_Temperatures.Temp_4"))
        self.ui.main_label_temp4.setText(self.temp4)

class DelayLinesWindow(QWidget):
    def __init__(self, opcua_conn):
        super(DelayLinesWindow, self).__init__()
        # save the OPC UA connection
        self.opcua_conn = OPCUAConnection()
        self.opcua_conn.connect()

        # set up the delay lines window
        self.ui = loadUi('delay_lines.ui', self)
        # Dl statuses
        self.dl1_status()

        self.ui.dl1_pb_homming.clicked.connect(lambda: self.homing())
        self.ui.dl_dl1_pb_scan.clicked.connect(lambda: self.scan_fringes())

        self.ui.dl1_pb_reset.clicked.connect(lambda: self.reset_motor())
        self.ui.dl1_pb_init.clicked.connect(lambda: self.init_motor())
        self.ui.dl1_pb_enable.clicked.connect(lambda: self.enable_motor())
        self.ui.dl1_pb_disable.clicked.connect(lambda: self.disable_motor())
        self.ui.dl1_pb_stop.clicked.connect(lambda: self.stop_motor())
        self.ui.dl1_pb_move_rel.clicked.connect(lambda: self.move_rel_motor())
        self.ui.dl1_pb_move_abs.clicked.connect(lambda: self.move_abs_motor())


        # update the initial value in the window
        self.update_value()

        self.t = QTimer()
        self.t.timeout.connect(self.refresh_status)
        self.t.start(500)  # ms

    def closeEvent(self, *args):
        self.t.stop()
        self.opcua_conn.disconnect()
        super().closeEvent(*args)

    def refresh_status(self):
        self.dl1_status()

    def dl1_status(self):

        timerElapsed = datetime.utcnow()

        self.ui.dl_dl1_status.setText(str(self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.sStatus")))
        self.ui.dl_dl1_state.setText(str(self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.sState")))
        self.ui.dl_dl1_substate.setText(str(self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.sSubstate")))

        current_pos = self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.lrPosActual")
        # Convert mm -> micron
        current_pos = current_pos * 1000
        self.ui.dl_dl1_current_position.setText(f'{current_pos:.1f}')

        target_pos = self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.ctrl.lrPosition")
        target_pos = target_pos * 1000
        self.ui.dl_dl1_target_position.setText(f'{target_pos:.1f}')

        current_speed = self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.lrVelActual")
        current_speed = current_speed * 1000
        self.ui.dl_dl1_current_speed.setText(f'{current_speed:.1f}')

        now = datetime.utcnow()

        print('Time elapsed loading, DL position, DL speed : ', str(now - timerElapsed), current_pos, current_speed)
        fileName = r'C:\Users\fys-lab-ivs\Documents\Python Scripts\Log\DLPositions_' \
                        + now.strftime(r'%Y-%m-%d') + '.csv'

        f = open(fileName, 'a')
        f.write(f'{str(now)}, {current_pos:.1f}, {current_speed:.1f} \n')


    def update_value(self):
        # update the value in the delay lines window
        value = self.opcua_conn.read_node("ns=4;s=GVL_Cryo_Temperatures.Temp_1")
        # self.ui.value_label.setText(str(value))

    def write_to_server(self):
        # write the value to the server
        value = self.ui.value_input.text()
        # self.opcua_conn.write_node("ns=4;s=GVL_Cryo_Temperatures.Temp_1", value)
        # self.update_value()

    # Reset motor
    def reset_motor(self):
        try:
            parent = self.opcua_conn.client.get_node('ns=4;s=MAIN.DL_Servo_1')
            method = parent.get_child("4:RPC_Reset")
            arguments = []
            res = parent.call_method(method, *arguments)
        except Exception as e:
            print(f"Error calling RPC method: {e}")

    # Homming
    def homing(self):
        try:
            self.reset_motor()
            time.sleep(5.0)
            self.init_motor()
            time.sleep(10)
            if not self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.bInitialised"):
                self.ui.dl_dl1_homming.setText("Homing")
            else:
                self.ui.dl_dl1_homming.setText("Home")
        except Exception as e:
            print(f"Error calling RPC method: {e}")

    # Scan Fringes
    def scan_fringes(self):
        try:
            pos = 10.0  #the required position
            speed = 0.1 # mm/s

            # Homing motor first
            #self.reset_motor()
            #time.sleep(5.0)
            #self.init_motor()
            #time.sleep(10)

            # Triggering camera to START taking images

            #self.trigger_camera_to_take_images(True)


            parent = self.opcua_conn.client.get_node('ns=4;s=MAIN.DL_Servo_1')
            method = parent.get_child("4:RPC_MoveVel")
            arguments = [speed]
            res = parent.call_method(method, *arguments)

            if self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.lrPosActual") >= pos:
                self.ui.dl_dl1_scanning.setText("Scanning Complete")
                # Triggering camera to STOP taking images
                #self.trigger_camera_to_take_images(False)
                self.stop_motor()

            elif self.opcua_conn.read_node("ns=4;s=MAIN.DL_Servo_1.stat.lrPosActual") <pos:
                self.ui.dl_dl1_scanning.setText("Scanning")
        except Exception as e:
            print(f"Error calling RPC method: {e}")

    # Initialize motor
    def init_motor(self):
        try:
            parent = self.opcua_conn.client.get_node('ns=4;s=MAIN.DL_Servo_1')
            method = parent.get_child("4:RPC_Init")
            arguments = []
            res = parent.call_method(method, *arguments)
        except Exception as e:
            print(f"Error calling RPC method: {e}")

    # Enable motor
    def enable_motor(self):
        try:
            parent = self.opcua_conn.client.get_node('ns=4;s=MAIN.DL_Servo_1')
            method = parent.get_child("4:RPC_Enable")
            arguments = []
            res = parent.call_method(method, *arguments)
        except Exception as e:
            print(f"Error calling RPC method: {e}")

    # Disable motor
    def disable_motor(self):
        try:
            parent = self.opcua_conn.client.get_node('ns=4;s=MAIN.DL_Servo_1')
            method = parent.get_child("4:RPC_Disable")
            arguments = []
            res = parent.call_method(method, *arguments)
        except Exception as e:
            print(f"Error calling RPC method: {e}")

    # Stop motor
    def stop_motor(self):
        try:
            parent = self.opcua_conn.client.get_node('ns=4;s=MAIN.DL_Servo_1')
            method = parent.get_child("4:RPC_Stop")
            arguments = []
            res = parent.call_method(method, *arguments)
        except Exception as e:
            print(f"Error calling RPC method: {e}")


    # Move absolute motor
    def move_abs_motor(self):
        try:
            pos = self.ui.dl1_textEdit_pos.toPlainText()
            #Convert to mm
            pos = float(pos) / 1000
            speed = 0.1

            parent = self.opcua_conn.client.get_node('ns=4;s=MAIN.DL_Servo_1')
            method = parent.get_child("4:RPC_MoveAbs")
            arguments = [pos,speed]
            res = parent.call_method(method, *arguments)
            print(res)
        except Exception as e:
            print(f"Error calling RPC method: {e}")

    # Move rel motor
    def move_rel_motor(self):
        try:
            rel_pos = self.ui.dl1_textEdit_rel_pos.toPlainText()
            # Convert to mm
            rel_pos = float(rel_pos) / 1000
            print("rel_pos = ",rel_pos)
            speed = 0.05

            parent = self.opcua_conn.client.get_node('ns=4;s=MAIN.DL_Servo_1')
            method = parent.get_child("4:RPC_MoveRel")
            arguments = [rel_pos, speed]
            res = parent.call_method(method, *arguments)
        except Exception as e:
            print(f"Error calling RPC method: {e}")

    # Move velocity
    def move_velocity_motor(self, vel):
        try:
            parent = self.opcua_conn.client.get_node('ns=4;s=MAIN.DL_Servo_1')
            method = parent.get_child("4:RPC_MoveVel")
            arguments = [vel]
            res = parent.call_method(method, *arguments)
        except Exception as e:
            print(f"Error calling RPC method: {e}")

    def trigger_camera_to_take_images(self, bTrig):

        # Triggering camera to start taking images
        # CameraOut1_node = self.opcua_conn.read_node("ns = 4;s = GVL_DL_Scanning_Homming.bTrigCameraImages")
        CameraOut1_node_dv = ua.DataValue(ua.Variant(bTrig, ua.VariantType.Boolean))
        # CameraOut1_node.set_value(CameraOut1_node_dv)
        self.opcua_conn.write_node("ns = 4;s = GVL_DL_Scanning_Homming.bTrigCameraImages", CameraOut1_node_dv)


# if __name__=='__main__':
#     app = QApplication(sys.argv)

    # Connect to OPC-UA server
    # url = "opc.tcp://10.33.178.141:4840"
    # client = Client(url)
    # client.connect()
    #
    # # Read a variable
    # var_node = client.get_node("ns=4;s=GVL_Cryo_Temperatures.Temp_1")
    # print("Original value:", var_node.get_value())
    #
    # # Write a new value to the variable
    #
    # # new_value = 10.0
    # # var_node.set_value(60.3)
    # # var_node.set_attribute(client.A
    # # .AttributeIds.Value, ua.DataValue(True))
    # # print("New value:", var_node.get_value())
    #
    # # Disconnect from OPC-UA server
    # client.disconnect()

    # window_1 = Window()
    # window_1.show()
    #
    #
    #
    # try:
    #     sys.exit(app.exec())
    # except:
    #     print("Exiting")
