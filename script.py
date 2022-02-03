from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import pylast
import pandas as pd
from pandas.plotting import table
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image
import pythoncom
import traceback
import sys
import os
import qdarktheme
from datetime import datetime
import ctypes

API_KEY = "2334165ad38e100611e01e54ba6df293"
API_SECRET = "86fc1d8d37aefe64cfb77d4e3466c488"

myappid = u'nasspotlight.photogenerator' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

try:
    last_file = open('last.txt','r')
    username=last_file.readline()
    username = username.strip('\n')
    last=last_file.readline()
    last_file.close()
    last=pd.to_datetime(last, format='%d-%m-%Y %H:%M',utc=True)
except:
    last=datetime.today()
    username=''

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        QApplication.setStyle("Fusion")

        self.setWindowTitle('NAS Spotlight Photo Generator')
        self.setStyleSheet(qdarktheme.load_stylesheet())
        self.setWindowIcon(QIcon('images/icon.ico'))
        self.setFixedSize(QSize(520,500))
        self.threadpool = QThreadPool() # Start threads
        
        username_box = QLineEdit()
        username_box.setMaxLength(20)
        username_box.setPlaceholderText("Enter your Last.fm username")
        username_box.setText(username)
        username_box.textEdited.connect(self.text_edited)

        dateEdit = QDateTimeEdit(last)
        dateEdit.setDisplayFormat("dd.MM.yyyy hh:mm")
        dateEdit.setCalendarPopup(True)
        dateEdit.dateTimeChanged.connect(self.dateChanged)

        self.button = QPushButton('&Submit')
        self.button.clicked.connect(self.submit)
        self.button2 = QPushButton('&Open output folder')
        self.button2.clicked.connect(self.open_output)
        
        datetime_label = QLabel('Date and time of the last uploaded track')
        user_label = QLabel('Last.fm username')
        title_label = QLabel('<font size=5>NAS Spotlight Photo Generator</font>')
        self.statusLabel = QLabel('')
        self.remainingLabel = QLabel('')

        # Banner
        pixmap = QPixmap('images/banner.jpg')
        pixmap = pixmap.scaledToWidth(400)
        lbl = QLabel(self)
        lbl.setPixmap(pixmap)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox_user = QVBoxLayout()        
        vbox_user.addWidget(user_label)
        vbox_user.addWidget(username_box)

        vbox_datetime = QVBoxLayout()
        vbox_datetime.addWidget(datetime_label)
        vbox_datetime.addWidget(dateEdit)

        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(self.button)
        hbox_buttons.addWidget(self.button2)
        
        vbox = QVBoxLayout()
        vbox.addWidget(lbl)
        vbox.addWidget(title_label)
        vbox.addLayout(vbox_user)
        vbox.addLayout(vbox_datetime)
        vbox.addLayout(hbox_buttons)
        vbox.addWidget(self.statusLabel)
        vbox.addWidget(self.remainingLabel)
        self.setLayout(vbox)

    def text_edited(self, s):
        global username
        username = s

    def dateChanged(self, s):
        global last
        last=s
        last=QDateTime.toPyDateTime(last)

    def execute_this_fn(self):
        photoCreated=False
        pythoncom.CoInitialize() # arreglar un error
        network = pylast.LastFMNetwork(
        api_key=API_KEY,
        api_secret=API_SECRET,
        username=username,
        )
        user = network.get_user(username)

        # Retrieve the recent tracks
        try:
            user_info=pylast.AuthenticatedUser.get_recent_tracks(user, limit= None, cacheable=True, time_from=int(pd.Timestamp(last).timestamp()))
        except:
            self.statusLabel.setText('<font color="#FF4700">Check your input data</font>')
            self.remainingLabel.setText('')
        # Create dataframe
        song=[]
        artist=[]
        time=[]
        album=[]

        for i in range(0, len(user_info)-1):
            split=str(user_info[i].track).split(" - ")
            artist.append(split[0])
            song.append(split[1])
            time.append(user_info[i].playback_date)
            album.append(user_info[i].album)


        df = pd.DataFrame(
            {'Artist': artist,
            'Song': song,
            'Album': album,
            'Time': time
            })

        df['Time'] = pd.to_datetime(df['Time'], format='%d %b %Y, %H:%M')
        df['Difference'] = 0
        df['Sum'] = 0

        # Calculate the difference in time and the acummulated sum
        sum=0
        for i in range(0, len(df)):
            if i != 0 and i != len(df):
                diff = df['Time'].iloc[i-1]-df['Time'].iloc[i]
                if diff.seconds/60 <= 13:
                    df['Difference'].iloc[i-1] = diff.seconds/60
                else:
                    df['Difference'].iloc[i-1] = 0
                    

        remaining='0'
        photos = 0
        ind=len(df)
        df['Time'] = df['Time'].dt.strftime('%d-%m-%Y %H:%M')

        for i in range(len(df), 0, -1):
            if i != len(df) and i != 0:
                sum = df['Difference'].iloc[i-1] + sum
                df['Sum'].iloc[i-1]=sum
                if sum >= 60:
                    try:
                        # Create target Directory
                        os.mkdir('output')
                    except FileExistsError:
                        print("Directory already exists")
                    photos = photos + 1
                    photoCreated = True
                    sum=0
                    df['Sum'].iloc[i-1]=sum
                    new_last=df['Time'].iloc[i-1]
                    df_1 = df.iloc[i-1:ind,:]
                    df_1.drop("Sum",1, inplace=True)
                    df_1.drop("Difference",1, inplace=True)
                    df_1.reset_index(drop=True, inplace=True)

                    fig, ax = plt.subplots()
                    fig.patch.set_visible(False)
                    ax.axis('off')
                    ax.axis('tight')
                    ax.axis('scaled')

                    tb = ax.table(cellText=df_1.values, colLabels=df_1.columns, loc='center', cellLoc='center')

                    # Bold first row
                    for (row, col), cell in tb.get_celld().items():
                        if (row == 0) or (col == -1):
                            cell.set_text_props(fontproperties=FontProperties(weight='bold'))

                    tb.auto_set_font_size(False)
                    tb.set_fontsize(10)
                    tb.auto_set_column_width(col=list(range(len(df_1.columns))))
                    file_name='output/' + username + ' ' + str(df["Time"].iloc[i]).replace(":","") + '.png'

                    plt.savefig(file_name, dpi=300,bbox_inches='tight')

                    # Crop image
                    im = Image.open(file_name)
                    im = im.crop(im.getbbox())
                    im.save(file_name)

                    ind=i-1
                    del df_1, ax, fig, tb
        try:
            remaining = df['Sum'].iloc[0]
        except:
            remaining = 0
        if photoCreated:
            final_file = open('last.txt','w')
            final_file.write(username + '\n')
            final_file.write(str(new_last))
            final_file.close()
            self.statusLabel.setText('<font color="#20FF00">' + str(photos) +' photos were created successfully')
        else:
            self.statusLabel.setText('<font color="#FF4700">You don\'t have enough listening time</font>')
        self.remainingLabel.setText("You have " + str(remaining) + " minutes accumulated of listening time")
    
    def submit(self):
        self.statusLabel.setText('<font color="#00CEFF">Working...</font>')
        worker = Worker(self.execute_this_fn)
        self.threadpool.start(worker)
    
    def open_output(self):
        try:
            os.mkdir('output')
        except FileExistsError:
            print("Directory already exists")
        os.startfile(r'output')


class Worker(QRunnable):
    '''
    Worker thread
    '''
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(
                *self.args, **self.kwargs
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
        

app = QApplication(sys.argv)
app.setStyleSheet('''
QPushButton{
    font-size: 20px;
}
QLabel{
    font-size: 20px;
}
QDateTimeEdit{
    font-size: 20px;
}
QLineEdit{
    font-size: 20px;
}
  '''  )

window = MyApp()
window.show()
sys.exit(app.exec())
