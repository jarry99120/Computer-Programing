# Installation and Setup

## Prerequisites
```
Ubuntu 24.04 LTS
gcc 13.x or above
make 4.x or above
Python 3.8 or above
Flask 3.x or above
```
## Setup
0. Open a WSL Ubuntu Terminal (Windows Users Only).This project must be run inside a Linux (Ubuntu) environment. On Windows, all commands must be executed inside WSL — not in PowerShell or Command Prompt.Run all project commands here.

1. Install System Dependencies
```
sudo apt update
sudo apt install -y build-essential python3 python3-venv python3-pip
```
2. Download ZIP file: Download the zip file, extract it and `cd` into the profect root directory
```
cd team12
```
3. Compile the C Engine: From the project root,run:
```
cd c_engine
make
cp libra_engine.so ../web_server/
cd ..
```
4. Install Python Dependencies (Flask): From the project root, run:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
5. Start the Server: Make sure you are in the project root with the virtual environment active ((venv) prefix), then run:
```
cd web_server
python3 app.py
```
   You should see:
```
 * Running on http://127.0.0.1:8080
Press CTRL+C to quit
```
6. Play the Game: Open a browser and go to : 

> **http://127.0.0.1:8080**

   To stop the server, press`Ctrl + C`in the terminal.

