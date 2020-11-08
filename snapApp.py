# Standard Python3 libraries
import sys
# External Python3 libraries
import pandas as pd
import numpy as np
# Pyside2 related library imports
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import (QRect, Qt, QTimeZone, Slot, Signal, QObject)
from PySide2.QtGui import QColor, QPainter, QIcon
from PySide2.QtWidgets import (QAction, QApplication, QHBoxLayout, QMainWindow, 
                               QSizePolicy,  QWidget, QFileDialog, QListWidget,
                               QCheckBox, QListWidgetItem, QVBoxLayout, 
                               QLineEdit, QGroupBox, QRadioButton, QLabel, 
                               QFormLayout, QGridLayout, QErrorMessage)
from PySide2.QtCharts import QtCharts
# Matplotlib import (necessary to import after Pyside2 libs because of backend
# preparation of qt5agg)
from matplotlib.backends.backend_qt5agg import (FigureCanvas, 
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Time conversion function
def convert_seconds(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
      
    return "%d:%02d:%02d" % (hour, minutes, seconds) 

# Widget class which handles widgets display, functionality and layout 
# management
class Widget(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        # Data for plotting and marker data storage
        self.data = {}
        self.slice_index = {
            'ind1': 0, 
            'ind2': 0
            }
        self.marker_id = 0
        self.marker_ind = []
        self.marker_setpoint = {
            'Marker1': 0, 
            'Marker2': 0, 
            }

        # Error message dialog widget
        self.error_popup = QErrorMessage()
        self.error_popup.setWindowTitle('Snap file error')

        # Left (List of Checkboxes)
        self.list_widget = QListWidget()
        #Resize width and height
        self.list_widget.setSizePolicy(QSizePolicy.Preferred, 
                                       QSizePolicy.Preferred)
        self.list_widget.setMinimumWidth(200)
        self.list_widget.setMaximumWidth(400)
        # self.list_widget.setMinimumHeight(300)
        self.list_widget.setMaximumHeight(500)

        # Signal groupbox
        self.signal_groupbox = QGroupBox('Available Signals')
        self.signal_groupbox.setMinimumWidth(200)
        self.signal_groupbox.setMaximumWidth(350)
        self.signal_groupbox.setMinimumHeight(100)
        self.sig_group_layout = QVBoxLayout()
        self.signal_groupbox.setLayout(self.sig_group_layout)
        # Statistics groupbox
        self.stats_groupbox = QGroupBox('Statistics')
        self.stats_groupbox.setMinimumWidth(200)
        self.stats_groupbox.setMaximumWidth(350)
        self.stats_groupbox.setMinimumHeight(240)
        self.stats_group_layout = QFormLayout()

        # Label initiation
        # Marker Time 1
        self.mark_one_time_label = QLabel('Marker1_time: ')
        self.mark_one_time_value = QLabel()
        # Marker Time 2
        self.mark_two_time_label = QLabel('Marker2_time: ')
        self.mark_two_time_value = QLabel()
        # On/Off labels for 0/1 signals counter
        self.on_off_label = QLabel('On/Off: ')
        self.on_off_value = QLabel()
        # Mean value
        self.mean_label = QLabel('Mean: ')
        self.mean_value = QLabel()
        # Standard deviation
        self.std_label = QLabel('Sigma(STD): ')
        self.std_value = QLabel()
        # Minimal value
        self.min_label = QLabel('Min: ')
        self.min_value = QLabel()
        # Maximual value
        self.max_label = QLabel('Max: ')
        self.max_value = QLabel()
        # Max - Min value
        self.val_diff_label = QLabel('Max-Min: ')
        self.val_diff_value = QLabel()
        # Time difference (X-axis)
        self.time_diff_label = QLabel('Time_diff: ')
        self.time_diff_value = QLabel('')

        # Row addition of labels
        self.stats_group_layout.addRow(self.mark_one_time_label, 
                                       self.mark_one_time_value)
        self.stats_group_layout.addRow(self.mark_two_time_label,
                                       self.mark_two_time_value)
        self.stats_group_layout.addRow(self.time_diff_label, 
                                       self.time_diff_value)
        self.stats_group_layout.addRow(self.on_off_label, self.on_off_value)
        self.stats_group_layout.addRow(self.mean_label, self.mean_value)
        self.stats_group_layout.addRow(self.std_label, self.std_value)
        self.stats_group_layout.addRow(self.min_label, self.min_value)
        self.stats_group_layout.addRow(self.max_label, self.max_value)
        self.stats_group_layout.addRow(self.val_diff_label, 
                                       self.val_diff_value)
        self.stats_groupbox.setLayout(self.stats_group_layout)

        # Set markers section of the application (bottom left)
        self.marker_grid = QGridLayout()
        self.marker_one_notice = QLabel()
        self.marker_two_notice = QLabel()
        self.set_marker_one_label = QLabel('Set Marker1:')
        self.set_marker_two_label = QLabel('Set Marker2:')
        self.set_marker_one_value = QLineEdit()
        self.set_marker_one_value.setMaximumWidth(100)
        self.set_marker_two_value = QLineEdit()
        self.set_marker_two_value.setMaximumWidth(100)

        self.marker_grid.addWidget(self.set_marker_one_label)
        self.marker_grid.addWidget(self.set_marker_one_value)
        self.marker_grid.addWidget(self.marker_one_notice)
        self.marker_grid.addWidget(self.set_marker_two_label)
        self.marker_grid.addWidget(self.set_marker_two_value)
        self.marker_grid.addWidget(self.marker_two_notice)
                                        
        # Leftside app layout
        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.list_widget)
        self.v_layout.addWidget(self.signal_groupbox)
        self.v_layout.addWidget(self.stats_groupbox)
        self.v_layout.addLayout(self.marker_grid)

        # Matplotlib figure
        self.fig = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, 
                                  QSizePolicy.Expanding)
        self.ax = self.canvas.figure.subplots()
        self.ax.grid()
        self.ax.set_xlabel('Time[s]')
        self.fig.suptitle('Parameter Plot')
      
        # QWidget Layout
        self.h_layout = QHBoxLayout()
        self.h_layout.addLayout(self.v_layout)
        self.h_layout.addWidget(self.canvas)

        # Set the layout to the QWidget
        self.setLayout(self.h_layout)

        # ListWidget and plot connections
        self.list_widget.itemChanged.connect(self.item_changed)
        self.click_event = self.fig.canvas.mpl_connect('button_press_event',
                                                       self.on_click)
        self.set_marker_one_value.returnPressed.connect(
                                                lambda: self.add_marker('one'))
        self.set_marker_two_value.returnPressed.connect(
                                                lambda: self.add_marker('two'))
        
    # Add radio button when signal is checked for plotting
    def add_radio_button(self, name):
        self.rad_btn = QRadioButton(name)
        self.rad_btn.toggled.connect(self.calculate_signal_stats)
        self.sig_group_layout.addWidget(self.rad_btn)

    # Remove radio button when signal is unchecked for plotting
    def remove_radio_button(self, name):
        for item in self.signal_groupbox.children():
            try:
                if item.text() == name:
                    item.setParent(None)
            except AttributeError:
                pass
    
    # Remove all radiobuttons on new data load
    def clear_signals(self):
        count = 0
        for item in self.signal_groupbox.children():
            if count == 0:
                count = 1
                continue 
            else:
                item.setParent(None)  
    # Check state of all radiobuttons, if none is checked remove stats values
    def check_signals(self):
        count = 0
        num_of_check = 0
        for item in self.signal_groupbox.children():
            if count == 0:
                count = 1
                continue 
            else:
                if item.isChecked():
                    num_of_check += 1
        # If no radiobuttons are checked, remove stats
        if num_of_check == 0:
            self.mean_value.setText('') 
            self.std_value.setText('') 
            self.max_value.setText('') 
            self.min_value.setText('') 
            self.val_diff_value.setText('') 
            self.on_off_value.setText('')               

    # Item additon of listWidget
    def fill_list(self, list_items):
        self.list_widget.clear()

        for column in list_items:
            item = QListWidgetItem(column)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

        self.show()
    
    # If new data is loaded, replace the old one
    def replace_data(self, temp):
        if not temp == self.data:
            self.data = temp
            self.clear_signals()

    @Slot()
    # Item state changed in listWidget event handler
    def item_changed(self, item):
        if item.checkState() == Qt.Unchecked:
           self.remove_plot(item.text())
           self.remove_radio_button(item.text())
           self.check_signals()
        else:
            self.add_plot(self.data['Time'], 
                          self.data[item.text()], item.text())
            self.add_radio_button(item.text())
                
    # Method for plotting data
    def add_plot(self, x_data, y_data, name):
        self.ax.plot(x_data, y_data, label=name, picker=3)
        self.ax.grid(True)
        self.ax.relim()
        self.ax.set_xlabel('Time[s]')
        self.ax.autoscale_view()
        self.ax.legend(loc='upper right')
        self.canvas.draw()

    # Method for marker addition via QLineEdit
    def add_marker(self, label):
        # Check if any signal is plotted
        sig_count = 0
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).checkState() == Qt.Checked:
                sig_count += 1

        if sig_count == 0:
            self.marker_one_notice.setText('No active signal!')
            self.marker_two_notice.setText('No active signal!')
            return
        try:
            max_time = self.data['Time'][-1]
            min_time = self.data['Time'][0]
        except KeyError:
            self.marker_one_notice.setText('Signal data not loaded!')
            self.marker_two_notice.setText('Signal data not loaded!')
        if label == 'one':
            try:
                mark1_value = float(self.set_marker_one_value.text())
                if mark1_value < max_time and mark1_value > min_time:
                    if self.marker_id == 0:
                        self.marker_id += 1
                        label_id = self.marker_id
                    elif self.marker_id == 1:
                        self.marker_id += 1
                        label_id = self.marker_id
                        self.remove_marker('first')
                    else:
                        self.remove_marker('first')
                        label_id = 1

                    self.marker_one_notice.setText('')
                    self.marker_setpoint['Marker1'] = mark1_value
                    self.mark_one_time_value.setText(
                                            self.set_marker_one_value.text())
                    self.calculate_marker_stats()
                    self.calculate_signal_stats()
                    
                    # Draw the marker
                    L =  self.ax.axvline(
                                    x=float(self.set_marker_one_value.text()), 
                                    linestyle='dashed', 
                                    color='red', 
                                    label='_Marker' + str(label_id))
                    self.fig.canvas.draw()
                else:
                    self.marker_one_notice.setText('Marker1 out of bounds')
            except ValueError:
                self.marker_one_notice.setText('Non-Valid value entered!')
        else:
            try:
                mark2_value = float(self.set_marker_two_value.text()) 
                if mark2_value < max_time and mark2_value > min_time:
                    if self.marker_id == 1:
                        self.marker_id += 1
                        label_id = self.marker_id
                    elif self.marker_id == 2:
                        label_id = 2
                        self.remove_marker('second')
                    else:
                        self.marker_two_notice.setText('Marker1 not placed')
                    self.marker_two_notice.setText('')
                    self.marker_setpoint['Marker2'] = mark2_value
                    self.mark_two_time_value.setText(
                                            self.set_marker_two_value.text())
                    self.calculate_marker_stats()
                    self.calculate_signal_stats()
                    # Draw the marker
                    L =  self.ax.axvline(
                                    x=float(self.set_marker_two_value.text()), 
                                    linestyle='dashed', 
                                    color='red', 
                                    label='_Marker' + str(label_id))
                    self.fig.canvas.draw()
                else:
                    self.marker_two_notice.setText('Marker2 out of bounds')
            except:
                self.marker_two_notice.setText('Non-Valid value entered!')
    
    # Marker removal method
    def remove_marker(self, label):
        for item in self.ax.lines:
            if 'Marker' in item.get_label():
                self.marker_ind.append(item)

        # If there are two markers remove them from plot and adjust marker
        # time labels
        if label == 'both':
            self.marker_ind[0].remove()
            self.marker_ind[1].remove()
            self.marker_ind = []
            self.marker_setpoint['Marker1'] = 0
            self.marker_setpoint['Marker2'] = 0
            self.mark_one_time_value.setText('')
            self.mark_two_time_value.setText('')
            self.time_diff_value.setText('')
            self.marker_id = 0
        # Remove only marker1
        elif label == 'first':
            self.marker_ind[0].remove()
            self.marker_ind = []
            self.marker_setpoint['Marker1'] = 0
            self.mark_one_time_value.setText('')
            self.marker_id -= 1
        elif label == 'second':
            self.marker_ind[1].remove()
            self.marker_ind = []
            self.marker_setpoint['Marker2'] = 0
            self.mark_two_time_value.setText('')
            self.marker_id -= 1

        self.ax.set_xlabel('Time[s]')
        self.canvas.draw()
    
    # Method for plot removal
    def remove_plot(self, name):
        cnt = 0
        for item in self.ax.lines:
            if item.get_label() == name:
                self.ax.lines[cnt].remove()
            cnt += 1
        self.ax.relim()
        self.ax.autoscale_view()
        self.ax.legend(loc='upper right')
        self.ax.set_xlabel('Time[s]')
        self.canvas.draw()

        # Check if all elements are unticked
        counter = 0
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).checkState() == Qt.Checked:
                counter +=1
        if counter == 0:
            self.remove_marker('both')
            
    # On click event for plot, only two markers can be active at the time
    def on_click(self, event):
        try:
            # Catch left click event
            if event.button == 1:
                x = event.xdata
                if self.marker_id < 2:
                    if self.marker_id == 0:
                        self.marker_setpoint['Marker1'] = round(x)
                        self.mark_one_time_value.setText(
                                            str(self.marker_setpoint['Marker1']))
                        self.calculate_marker_stats()
                        self.calculate_signal_stats()
                    else:
                        self.marker_setpoint['Marker2'] = round(x)
                        self.mark_two_time_value.setText(
                                            str(self.marker_setpoint['Marker2']))
                        self.calculate_marker_stats()
                        self.calculate_signal_stats()
                    self.marker_id += 1
                    L =  self.ax.axvline(x=x, 
                                        linestyle='dashed', 
                                        color='red', 
                                        label='_Marker' + str(self.marker_id))
                    self.fig.canvas.draw()
            # Catch right click event
            elif event.button == 3:
                self.remove_marker('both')
        except TypeError:
            pass
    # Marker analysis method
    def calculate_marker_stats(self):
        if self.marker_setpoint['Marker2'] == 0:
            diff = self.data['Time'][-1] - self.marker_setpoint['Marker1']
            self.time_diff_value.setText(str(diff))
        else:
            diff = self.marker_setpoint['Marker2'] -  \
                   self.marker_setpoint['Marker1']
            
            self.time_diff_value.setText(convert_seconds(diff))
    # Signal analysis method
    def calculate_signal_stats(self):
        self.check_signals()
        selected_signal = ''
        signal_data = []
        num_off, num_on = 0, 0
        for item in self.signal_groupbox.children():
            try:
                if item.isChecked():
                    # Signal extraction block
                    selected_signal = item.text()
                    # If only one marker, Marker1 is placed on graph
                    if self.marker_setpoint['Marker2'] == 0 and self.marker_setpoint['Marker1'] != 0:
                        for i in range(len(self.data['Time'])):
                            if self.data['Time'][i] > self.marker_setpoint['Marker1']:
                                self.slice_index['ind1'] = i
                                break
                        signal_data = np.asarray(
                        self.data[selected_signal][self.slice_index['ind1']:], 
                                    dtype=np.float32)
                    # Both markers, Marker1 and Marker2 are present on graph
                    elif self.marker_setpoint['Marker1'] != 0 and self.marker_setpoint['Marker2'] != 0:
                        for i in range(len(self.data['Time'])):
                            if self.data['Time'][i] > self.marker_setpoint['Marker1']:
                                self.slice_index['ind1'] = i
                                break
                        for i in range(len(self.data['Time'])):
                            if self.data['Time'][len(self.data['Time']) - i - 1] < self.marker_setpoint['Marker2']:
                                self.slice_index['ind2'] = len(self.data['Time']) - i
                                break
                        signal_data = np.asarray(
                        self.data[selected_signal][self.slice_index['ind1']:self.slice_index['ind2'] - 1], 
                                                    dtype=np.float32)
                        
                    # No markers present, whole signal stats are showed
                    else:
                        signal_data = np.asarray(self.data[selected_signal], 
                                                    dtype=np.float32)
                    try:
                        # Signal mean calculation
                        self.mean_value.setText(str(np.mean(signal_data)))
                        # Standard deviation
                        self.std_value.setText(str(np.std(signal_data)))
                        # Maximum value
                        self.max_value.setText(str(np.max(signal_data)))
                        # Minimum value
                        self.min_value.setText(str(np.min(signal_data)))
                        # Max - Min
                        self.val_diff_value.setText(str(np.max(signal_data) - 
                                                    (np.min(signal_data))))
                        if np.max(signal_data) == 1.0:
                            for i in range(len(signal_data)):
                                if i != len(signal_data) - 1:
                                    temp = signal_data[i] - signal_data[i+1]
                                    if temp == 1:
                                        num_off += 1
                                    elif temp == -1:
                                        num_on += 1
                            self.on_off_value.setText(str(num_on) + 
                                                    '\\' + str(num_off))
                    except ValueError:
                        err_line1 = 'Missing data, result is empty array!'
                        err_line2 = '\n Please check snap file.' 
                        self.error_popup.showMessage(err_line1 + err_line2)
            except AttributeError:
                pass

# Application main window
class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('Snap Reader')
        self.setWindowIcon(QIcon('assets\\fridge@2x.png'))

        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu('File')

        # Open QAction
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        
        # Exit QAction
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.exit_app)

        # Menubar actions
        self.file_menu.addAction(open_action)
        self.file_menu.addAction(exit_action)

        # Status Bar
        self.status = self.statusBar()
        self.status.showMessage('Application started')

        # Window dimensions and positioning
        geometry = app.desktop().availableGeometry(self)
        self.left = 20
        self.right = 30
        self.setGeometry(self.left, 
                            self.right, 
                            geometry.width() * 0.9, 
                            geometry.height() * 0.8)
        self.move(30,30)

        # Widget object instance
        self.centralWidget = Widget()
        self.setCentralWidget(self.centralWidget)
        # Add toolbar which is native for the matplotlib
        self.addToolBar(NavigationToolbar(self.centralWidget.canvas, self))

    # File -> Exit Handler
    @Slot()
    def exit_app(self, checked):
        sys.exit()
    
    # File -> Open Handler
    @Slot()
    def open_file(self, checked):
        try:
            filename = QFileDialog.getOpenFileName(self,
                                                   'Open File', 
                                                   '', 
                                                   'Snap Files (*.csv)')
            df = pd.read_csv(filename[0],
                             skiprows=1,
                             delimiter=',')

            # Extract necessary columns for display in listWidget
            list_items_columns = list(df.columns)
            list_items_columns.remove('Date')
            list_items_columns.remove('Time')

            # Pass the loaded dataframe as data for ploting
            temp = {}
            for column in df.columns:
                temp[str(column)] = df[column].values
            
            # Convert time to only seconds format and adjust it for plotting
            # purposes
            for i in range(len(temp['Time'])):
                h, m, s = temp['Time'][i].split(':')
                temp['Time'][i] = int(h) * 3600 + int(m) * 60 + int(s)
            
            temp['Time'] = [temp['Time'][i] - temp['Time'][0] \
                            for i in range(len(temp['Time']))]

            # Check for data replacement if new .csv is loaded
            self.centralWidget.replace_data(temp)

            # Call listWidget item update
            self.centralWidget.fill_list(list_items_columns)

            # Clear all previous plots
            self.centralWidget.ax.clear()
            try:
                self.centralWidget.ax.legend.remove()
            except:
                pass
            self.centralWidget.ax.grid(True)
            self.centralWidget.ax.set_xlabel('Time[s]')
            self.centralWidget.canvas.draw()

            self.status.showMessage('Data loaded')
            
        except FileNotFoundError:
            pass
        except ValueError:
            pass


# Main
if __name__ == "__main__":
    # Qt Application
    app = QApplication(sys.argv)
    # Main Window
    window = MainWindow()
    window.show()
    # Execute application
    sys.exit(app.exec_())