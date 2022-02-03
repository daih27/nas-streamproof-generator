# nas-photogenerator
A photo generator for New Artist Spotlight using the scrobbles from Last.fm.

## Usage

The user must input a Last.fm username and the date and time of the last scrobbled track at your last uploaded photo, in the UTC timezone. The script will automatically generate the photos for every 1 hour of listening time, and then it'll remember the date and time for you the next time you run the script.

## Setup
To run this project, grab the Windows executable file in the release page, or use the python script directly.

To create a virtual environment in the folder you are at:

```
python -m venv venv
```
Activate it:

```
.\venv\Scripts\activate.bat
```

Install the required modules using the requirements.txt file:

```
pip install -r requirements.txt
```

Finally, run the python script:

```
python -m script.py
```
