import pylast
import pandas as pd
from pandas.plotting import table
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib
from PIL import Image
import sys
import os
import subprocess

matplotlib.pyplot.switch_backend('Agg')

API_KEY = "2334165ad38e100611e01e54ba6df293"
API_SECRET = "86fc1d8d37aefe64cfb77d4e3466c488"

try:
    os.mkdir('output')
except FileExistsError:
    pass

try:
    last_file = open('last.txt','r')
    username=last_file.readline()
    username = username.strip('\n')
    last=last_file.readline()
    last_file.close()
    print('Your current saved data is: \nUsername: ' + username + '\nDate and time: ' + str(last))
    change=input('Do you want to change it? (y/n): ')
    while True:
        if change == 'y':
            while True:
                username=input('Enter Last.fm username: ')
                if username=='':
                    username=input('Enter Last.fm username: ')
                else:
                    break
            while True:
                last=input('Enter date of last track uploaded (Format: dd-mm-yyyy hh:mm, UTC Time): ')
                if last=='':
                    last=input('Enter date of last track uploaded (Format: dd-mm-yyyy hh:mm, UTC Time): ')
                else:
                    break
            break
        else:
            if change == 'n':
                break
            else:
                change=input('Enter a valid input (y/n): ')  
except:
    username=input('Enter Last.fm username: ')
    last=input('Enter date of last track uploaded (Format: dd-mm-yyyy hh:mm, UTC Time): ')

last=pd.to_datetime(last, format='%d-%m-%Y %H:%M',utc=True)
photoCreated=False
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
    print('Check your input data')
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
    print('\n' + str(photos) +' images were created successfully')
else:
    print('\nYou don\'t have enough listening time')
print("You have " + str(remaining) + " minutes accumulated of listening time")

output_answer=input('Do you want to open the output folder? (y/n): ')
while True:
    if output_answer == 'y':
        subprocess.call(["open", r'output'])
        break
    else:
        if output_answer == 'n':
            break
        else:
            output_answer=input('Enter a valid input (y/n): ')

sys.exit()
