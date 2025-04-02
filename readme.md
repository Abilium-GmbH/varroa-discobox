
## Setup your Allied Vision Mako Camera:

1. Install Vimba X:
    1. download the [Vimba X SDK](https://www.alliedvision.com/en/products/software/vimba-x-sdk/)
    1. extract content to desired location
    1. go to `./VimbaX_Setup-2024-1-Linux64/VimbaX_2024-1/cti` and execute `Install_GenTL_Path.sh` using sudo:\
    `sudo ./Install_GenTL_Path.sh`
    1. reboot your PC
1. Find the IPv4 address of your camera:
    - using `ifconfig`:\
    [ifconfig](./imgs/ifconfig.png)
    - using `ping -b 255.255.255.255` (turn off your WiFi connection):\
    [ping](./imgs/ping.png)
1. Setup Network configuration
    1. go to `Settings > Network > PCI Ethernet`\
    [settings](./imgs/settings.png)
    1. click on `Add Ethernet Connection`
    1. go to tab `IPv4`
    1. set the `IPv4 Method` to manual
    1. add a line in Addresses with the IP Address of your camera in `Address` and `Gateway` and set the `Netmask` to `255.255.255.0`\
    [connection](./imgs/connection.png)
    1. click on apply and select the created connection
1. Start Vimba Viewer:
    1. launch Vimba Viewer from `./VimbaX_Setup-2024-1-Linux64/VimbaX_2024-1/bin/VimbaXViewer`
    1. if your camera is not detected automatically:
        1. click on `Action > Open Camera by IP`
        1. enter the IP address of your camera and click on `OK`

## Develop using the Python API

1. Create a virtual environment:
    ```terminal
    python3 -m venv venv
    source ./venv/bin/activate
    pip install './VimbaX_Setup-2024-1-Linux64/VimbaX_2024-1/api/python/vmbpy-1.0.5-py3-none-any.whl[numpy,opencv]'
    ```
1. Run some examples:
    1. list all connected cameras:
        ```terminal
        python3 ./VimbaX_Setup-2024-1-Linux64/VimbaX_2024-1/api/examples/VmbPy/list_cameras.py
        ```
    1. test if you camera connection works:
        ```terminal
        python3 ./VimbaX_Setup-2024-1-Linux64/VimbaX_2024-1/api/examples/VmbPy/asynchronous_grab_opencv.py
        ```

## Execute the Discobox app

1. Install `tkinter`:
    ```terminal
    sudo apt update
    sudo apt install python3-tk
    ```
1. Setup environment:
    ```terminal
    ./setup-python-env.sh
    source venv/bin/activate
    pip install '../VimbaX_Setup-2024-1-Linux64/VimbaX_2024-1/api/python/vmbpy-1.0.5-py3-none-any.whl[numpy,opencv]'
    ```
    Make sure to enter the correct path to your VimbaX installation in the last command.
1. Run the python script:
    - Run the `discobox.py` script:
        ```terminal
        python3 discobox.py
        ```
        The app will automatically connect to one of the connected cameras
    - Print help information:
        ```terminal
        python3 discobox.py -h
        ```
        Prints help information about this script to the console.
    - List all connected cameras:
        ```terminal
        python3 discobox.py -l
        ```
        Lists all cameras your machine is connected with.
    - Run the `discobox.py` script with a specific camera:
        ```terminal
        python3 discobox.py <Camera ID>
        ```


