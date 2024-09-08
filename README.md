<b>NOTE:</b> This is a placeholder for an upcoming deployment.

![slm_logo](https://github.com/user-attachments/assets/cb501b0c-8fd7-4468-a37a-f72e43347609)

---
# Stream Link Manager for Channels
In <b>[Channels DVR](https://getchannels.com/)</b>, users have the ability to add "<b>[Stream Links](https://getchannels.com/docs/channels-dvr-server/how-to/stream-links/)</b>" as local content. These <b>Stream Links</b> appear as normal Movies, TV Shows, and Videos next to recorded and other content but do not play in the Channels app or admin web page directly. Instead, clicking on one of these launches the appropriate app or web page and plays the content there. In order to do this, the process consists of creating ```.strmlnk``` files, putting them in the appropriate location, and running updates in the <b>Channels DVR</b> admin interface to get the programs to appear. As can be imagined, the activity around creation and maintenance is incredibly manual and cumbersome.

Enter <b>Stream Link Manager for Channels</b>!

![image](https://github.com/user-attachments/assets/56f18e08-c1de-4d54-927f-8a5b7afe7e05)

<b>Stream Link Manager for Channels</b> is a background service that sets up a web-based graphical user interface (GUI) for interaction. In the GUI, users can search for any Movie or TV Show and bookmark it. If it cannot be found, manual additions are allowed. Assuming a program is found, the software will parse through a user-derived list of Streaming Services (i.e., Disney+, Hulu, Netflix, Hoopla, Kanopy, etc...) in priority order to determine the appropriate link. After this, the necessary folders and files will be created, along with completing all other administrative tasks. Should a bookmark move from one Streaming Service to another, <b>Stream Link Manager for Channels</b> will automatically update everywhere that is required. But this is just the beginning of its capabilities! To learn more, watch the video here:

[![image](https://github.com/user-attachments/assets/89f8ef22-80bd-42a5-a827-24723f1c4515)](https://www.youtube.com/watch?v=APuUaAvNo-k)

<b>NOTE:</b> Some of the visuals seen in the video and in the screen shots below may be out of date as updates to format and functionality have been applied to the program.

---
![SpaceX_ASDS_in_position_prior_to_Falcon_9_Flight_17_carrying_CRS-6_(17127808431)_EDITED](https://github.com/user-attachments/assets/c45005cf-081f-4eba-bcb4-fcdccd7ca281)
<i>Image (edited) courtesy of SpaceX, CC0, via Wikimedia Commons.</i>

# Installation
There are several methods to install <b>Stream Link Manager for Channels</b> and only one should be followed. While Docker is the preferred route for those who have it as it is the most controlled path, if you are not comfortable with Docker or are having issues, you can do a straight self-deployment in Windows or Linux, or use Python in any OS type. For those unfamiliar with Docker, you can easily [install Docker Desktop as a stand-alone application](https://www.docker.com/products/docker-desktop/). If you are installing Docker in Windows, please set up Windows Subsystem for Linux (WSL) first by following [these directions](https://community.getchannels.com/t/espn-fox-sports-with-custom-channels-via-eplustv/31144/591). Channels DVR users who have deployed [OliveTin for Channels](https://community.getchannels.com/t/37609) and/or [Project One-Click](https://community.getchannels.com/t/39669) can use those, as well, to simplify the process.

As a general note, it does not matter "where" <b>Stream Link Manager for Channels</b> is installed; it could even be placed in the Channels DVR directory. The only requirements are that it must be on a machine and in a location that has directory access to the Channels DVR directory and be able to see the Channels DVR Administrative webpage.

## Docker
If you are not using <i>OliveTin/Project One-Click</i>, it is recommended to install via Stack using [Portainer](https://www.portainer.io/) ([Docker Desktop](https://open.docker.com/extensions/marketplace?extensionId=portainer/portainer-docker-extension) | [Docker Standalone](https://docs.portainer.io/start/install-ce/server/docker)). Otherwise, you can use the single command line method as shown below.

### Stack (Docker Compose)
```
version: '3.9'

services:
  slm:
    image: COMING_SOON:${TAG:-latest}
    container_name: slm
    ports:
      - "${SLM_PORT:-5000}:5000"
    volumes:
      - slm_files:/app/program_files
      - ${CHANNELS_FOLDER}:/app/channels_folder
    environment:
      - TZ=${TIMEZONE:-UTC}
    restart: unless-stopped

volumes:
  slm_files:
```

Environment variables are included, some required, some optional.

![image](https://github.com/user-attachments/assets/fafa4c3f-23b8-4830-8830-7b4c08a6f71c)

* <b>TAG</b> | OPTIONAL | Which version of the program you want. The default is "latest" if you do not add.

* <b>SLM_PORT</b> | OPTIONAL | The port you want to access the program from in the web browser. The default is "5000" if you do not add.

* <b>CHANNELS_FOLDER</b> | REQUIRED | The path to your Channels DVR parent directory (see details in <i>Startup</i> below), i.e., ```/usr/lib/channels-dvr```. You could optionally put in any parent path, so long as the Channels DVR path is accessible somewhere inside. Note that spaces are fine and you do not have to enclose the path in quotes. In Windows, your slashes should go the opposite of the normal way, i.e., ```C:/Files/Media/Channels DVR```. In MacOS, be sure to include your ```/Volumes``` first, i.e., ```/Volumes/external-hdd/Channels DVR```. Be careful not to put extra characters as your system may then create that directory anyway. In other words, there will be no error as the directory exists, but it is not set to where you want it to be.

* <b>TIMEZONE</b> | OPTIONAL | The timezone you want to use. To know what to input, go [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), find your timezone, make sure it is a "Canonical" Type, and use the "TZ identifier". The default is "UTC" if you do not add. Please keep this in mind when using the scheduler function.

### Command Line
Follow the directions above for <b>SLM_PORT</b> in place of ```[YOUR_PORT_HERE]``` (except now it is REQUIRED), <b>CHANNELS_FOLDER</b> in place of ```[PATH_TO_CHANNELS_FOLDER]```, and <b>TIMEZONE</b> in place of ```[TIMEZONE]```. Do not leave the ```[``` and ```]``` when putting in your values.

#### Most Cases
```
docker run -d --restart=unless-stopped --name slm -p [YOUR_PORT_HERE]:5000 -v slm_files:/app/program_files -v "[PATH_TO_CHANNELS_FOLDER]":/app/channels_folder -e TZ="[TIMEZONE]" [COMING_SOON]:latest
```

#### Some Linux Cases
```
docker run -d --restart=unless-stopped --name slm --network=host -e SLM_PORT=[YOUR_PORT_HERE] -v slm_files:/app/program_files -v "[PATH_TO_CHANNELS_FOLDER]":/app/channels_folder -e TZ="[TIMEZONE]" [COMING_SOON]:latest
```

#### Examples
```
docker run -d --restart=unless-stopped --name slm -p 7900:5000 -v slm_files:/app/program_files -v "C:/Files/Media/Channels DVR":/app/channels_folder -e TZ="America/New_York" [COMING_SOON]:latest
docker run -d --restart=unless-stopped --name slm --network=host -e SLM_PORT=7900 -v slm_files:/app/program_files -v "/somewhere/channels_dvr":/app/channels_folder -e TZ="America/New_York" [COMING_SOON]:latest
```

## Windows
1. Download the ```slm.bat``` file and place it in the final destination folder.
   
2. Open a ```Command Prompt```, navigate to that directory, and enter the following command:

```
slm.bat install
```

If using PowerShell, type in:

```
.\slm.bat install
```

3. You will be given one last chance to decide if you want to do the installation. Note that an installation will remove any previous instance of <b>Stream Link Manager for Channels</b> at that location. This is unlike the "upgrade" below which will maintain all your files and settings.

![image](https://github.com/user-attachments/assets/a93612b4-2159-47ae-8ccb-d959078bea8b)

4. The process will then run normally until complete. You should see something similar to this when done:

![image](https://github.com/user-attachments/assets/fc8cd8bc-8f0a-4670-ae76-2d46b5d88190)
  
5. In your folder, you should now have this:

![image](https://github.com/user-attachments/assets/8cbdac78-5dba-469d-ad58-93459bdf6056)
   
6. OPTIONAL: By default, <b>Stream Link Manager for Channels</b> runs on port 5000. You can change this to another port by typing in this command:

```
slm.bat port
```

If using PowerShell, type in:

```
.\slm.bat port
```

Note that this will also open the port in the Windows firewall as a safety measure. Even if you want the default port of 5000, this is recommended to be run if you want to access the program on another machine.

7. You will be prompted to enter a port number of your choice:

![image](https://github.com/user-attachments/assets/8a5f10dc-4ddb-4eb1-a8c5-20be498dc3a1)

During the process, you may receive a popup asking for permission to run. Accept and continue.

8. Once complete, you can see this port as an environment variable (where it can be removed, if necessary).

![image](https://github.com/user-attachments/assets/13fb0dc4-a547-4ab9-9c63-83cdb68f6970)

Additionally, in the Windows Firewall rules:

![image](https://github.com/user-attachments/assets/00175939-5e8b-45c6-b744-431be3f98f4b)

9. Follow the directions on the screen of closing the current ```Command Prompt``` and opening a new one. In the new ```Command Prompt```, you can confirm that that the port variable is being read correctly by typing:

```
echo %SLM_PORT%
```

If using PowerShell, type in:

```
$env:SLM_PORT
```

10. You should see something similar to this:

![image](https://github.com/user-attachments/assets/18fdab7d-9f11-4890-ad69-9fbe56424601)   ![image](https://github.com/user-attachments/assets/96c67fdf-4e89-4e55-b0ea-c48ead8bee48)

11. With all this in place, you are now safe to start the program!

## Linux
1. Download the ```slm.sh``` file and place it in the final destination folder. You can also do so by opening a terminal, navigating to that directory, and entering the following command:

```
wget -q -O "slm.sh" 'https://[LINK_COMING_SOON]'
```
   
2. Either way, once there, change the security level on the ```slm.sh``` file:

```
chmod +x "slm.sh"
```

3. Execute the installation with this command:

```
./slm.sh install
```

4. You will be given one last chance to decide if you want to do the installation. Note that an installation will remove any previous instance of <b>Stream Link Manager for Channels</b> at that location. This is unlike the "upgrade" below which will maintain all your files and settings.

![image](https://github.com/user-attachments/assets/53160f56-0c47-4b07-be7b-dfc9bd4cfd03)

5. The process will then run normally until complete. You should see something similar to this when done:

![image](https://github.com/user-attachments/assets/964fe66b-ff01-485d-8751-5797945082d8)

... a whole lot of lines related to installing requirements and building the executable...

![image](https://github.com/user-attachments/assets/0d3d5f52-cb55-45de-917e-ec0618c81f58)

6. In your folder, you should now have this:

![image](https://github.com/user-attachments/assets/9b3e34e1-7da2-4001-866e-292df7bf52ae)

7. OPTIONAL: By default, <b>Stream Link Manager for Channels</b> runs on port 5000. You can change this to another port by typing in this command:

```
./slm.sh port
```

Note that this will also open the port in the firewall as a safety measure. Even if you want the default port of 5000, this is recommended to be run if you want to access the program on another machine.

8. You will be prompted to enter a port number of your choice:

![image](https://github.com/user-attachments/assets/9c5c2fda-45c2-4435-84ec-aa376e46cce3)

9. Once complete, do the requested command to make the port available in the current session:

```
source ~/.bashrc
```
   
10. You can then see this port as an environment variable (where it can be removed, if necessary):

```
printenv SLM_PORT
```

![image](https://github.com/user-attachments/assets/4dc5af1b-44f8-483e-8eb2-75d8272896ef)

11. With all this in place, you are now safe to start the program!

## Python
Using Python directly is not recommended, however it is available as an option. As this is highly technical, only limited support is provided. It is expected that you are fairly familiar with [Python](https://www.python.org/downloads/) and have [pip](https://pip.pypa.io/en/stable/installation/) installed.

1. Download the ```slm_python.zip``` file and place it in the final destination folder.
   
2. Navigate to that directory and extract the contents. Make sure you have not created another subdirectory. When complete, remove the ```slm_python.zip```. It should now look something like this:

![image](https://github.com/user-attachments/assets/8aa83dc3-c7cc-4b0f-b96c-b0046c85748d)

3. Open a command prompt and navigate to the folder that you created. Type in the following command:

```
pip install -r requirements.txt
```

4. OPTIONAL: It is possible to generate an executable from the Python file directly. The only caveat is that in order to make one that works for that system type (say MacOS) your actions have to be run on that type of system. That means if you want to create an executable for an unsupported system type, you can do so with the following command:

```
pyinstaller --noconfirm --onedir --console --add-data "requirements.txt;." --add-data "static;static/" --add-data "templates;templates/"  "slm.py"
```

Or...

```
pyinstaller --noconfirm --onedir --console --add-data "requirements.txt:." --add-data "static:static/" --add-data "templates:templates/"  "slm.py"
```

Or...

```
pyinstaller --noconfirm --onedir --console --add-data="requirements.txt:." --add-data="static:static/" --add-data="templates:templates/"  "slm.py"
```

5. You will end up with some additional folders and files:
   
![image](https://github.com/user-attachments/assets/52f2ada4-a816-4bc8-9820-e0c7451caa80)

* You are free to remove ```build``` and ```slm.spec```.
* ```dist``` contains the entire executable program. You can leave it in its current location, rename it, and/or move it somewhere else.
* With that, you no longer need the original content that was unzipped and you can delete it if you want.

6. OPTIONAL: You can change the port for <b>Stream Link Manager for Channels</b> by creating a permanent Environment Variable called ```SLM_PORT``` (case sensitive) and giving it a value of the port you want to use. If you don't, the program will run on port 5000. You may also need to open the port up to bypass firewalls or other such settings.

---
# Upgrade
As with any program, there may be a need to update the code for stability, bug fixes, or general upgades. When a new version becomes available, you can easily upgrade using the directions below. To know when a new version is released, set up a watch on this Github repo.

![bbae83c81a2ddd80776fe1b443bbf2c8bbc3d412](https://github.com/user-attachments/assets/42411117-e081-402b-9ffe-703c48172158)

This way, you'll get an email whenever a new version is released, plus you can see exactly what has changed.

During an upgrade, the ```program_files``` directory is protected.

![image](https://github.com/user-attachments/assets/cda6bc66-4b7e-4819-bc6f-783afcf76ec9)

This is the most important directory as it contains all the settings, bookmarks, logs, backups, and other crucial information. As a best-practice, you may want to make a manual backup of this folder in case anything goes wrong during an upgrade. With this directory, even a fresh install can be restored with your details.

## Docker
1. Repull the Image and rebuild the Container. The ```program_files``` will be protected, so there should be no concerns about losing your settings and critical files.

If you are using ```Portainer```, you can use the ```Recreate``` button:

![image](https://github.com/user-attachments/assets/f16eccd8-2539-4678-80c8-22c1e4bbf94e)

When the option comes up, make sure "Re-pull image" is selected.

![1fa26d390178259e861b4788a7b731aab16bd0cc](https://github.com/user-attachments/assets/eb8ae961-3fa0-4902-9031-43b5d44b8077)

It then rebuilds the Image and the Container with all the original command lines. Remember to delete the old, unused Image afterwards.

## Windows
1. In ```Command Prompt```, navigate to your <b>Stream Link Manager for Channels</b> directory and type in the following command:

```
slm.bat upgrade
```

If using PowerShell, type in:

```
.\slm.bat upgrade
```

2. You may get a pop-up asking for permissions. Agree and continue until the process completes and you see something like this:

![image](https://github.com/user-attachments/assets/a4196964-74c4-453a-b4e8-ecb54f37ce98)

3. The most important thing is that ```slm.exe``` was terminated or not running, allowing the upgrade to take place. After the upgrade, you will need to restart the program manually or with a reboot. See <b>Startup</b> below.

## Linux
1. In a terminal, navigate to your <b>Stream Link Manager for Channels</b> directory and type in the following command:

```
./slm.sh upgrade
```

2. As the process runs, you should see something like this:

![image](https://github.com/user-attachments/assets/0338a0be-d516-43df-9132-cbd9047269de)

... a whole lot of lines related to installing requirements and building the executable...

![image](https://github.com/user-attachments/assets/2c036863-41ad-46bb-b236-96d68787a003)

3. The most important thing is that the ```/slm``` application was terminated or not running, allowing the upgrade to take place. After the upgrade, you will need to restart the program manually or with a reboot. See <b>Startup</b> below.

## Python
1. Make sure <b>Stream Link Manager for Channels</b> is closed and is not running in the background.

2. Copy the ```program_files``` directory under ```_internal``` to a safe location.

3. Completely delete <i>all</i> the files and subfolders.

4. Follow the directions for installation and replace the entire file content that were deleted in the prior step. If you have built an executable, you will have to redo those steps, as well.
   
5. Move the ```program_files``` directory you saved earlier back under the ```_internal``` directory.

6. Restart the program and everything should work the same as before.

---
# Startup
Since <b>Stream Link Manager for Channels</b> is designed to run as a service that you access through a webpage, it should be set up to launch at system startup. There may also be reasons to start manually, like after initial installation or an upgrade.

## Docker
1. There is nothing additional to do as Docker will automatically start up.

## Windows
1. In ```Command Prompt```, navigate to your <b>Stream Link Manager for Channels</b> directory and type in the following command:

```
slm.bat startup
```

If using PowerShell, type in:

```
.\slm.bat startup
```

2. You may get a pop-up asking for permissions. Agree and continue until the process completes and you see something like this:

![image](https://github.com/user-attachments/assets/53d24b29-8701-4cb1-96e5-9c7f93c48d73)

3. If you open ```Task Scheduler```, you should now see a task called "Stream Link Manager for Channels":

![image](https://github.com/user-attachments/assets/c909fde6-3ca5-4b73-9ff5-09f65c945f32)

4. The next time you reboot, <b>Stream Link Manager for Channels</b> will automatically start. Similarly, you can manually start it by either...
   
* Running the process directly in ```Task Scheduler```
* Double clicking on the ```slm.bat``` file
* In ```Command Prompt```, typing in ```slm.bat```

5. No matter the method, it may look like nothing has happened, but if you start ```Task Manager``` you will see a ```slm.exe``` running in the background:

![image](https://github.com/user-attachments/assets/de995caf-d7fc-4d82-b428-a2b1592d0629)

## Linux
1. In a terminal, navigate to your <b>Stream Link Manager for Channels</b> directory and type in the following command:

```
./slm.sh startup
```

2. As the process completes, you will see something like this:

![image](https://github.com/user-attachments/assets/288223eb-1f16-4617-8ca4-e0b73f2e4e42)

3. To check if the task is scheduled to run at startup, enter:

```
ls /etc/init.d               # For Debian/Ubuntu/Mint
ls /etc/systemd/system       # For RedHat/CentOS/Fedora/Arch/Manjaro/OpenSUSE
ls /usr/local/etc/rc.d       # For Synology
```

You should see a file named ```slm_startup.sh```:

![image](https://github.com/user-attachments/assets/0518f462-d077-427d-94d1-8e94600686c3)

4. The next time you reboot, <b>Stream Link Manager for Channels</b> will automatically start. Similarly, you can manually start it by entering:
   
```
./slm.sh
```

5. It may look like nothing has happened, but if you type in this command:

```
ps aux
```

You should see ```./slm``` running in the background. If you want to only look for that process, type:

```
ps aux | grep [s]lm
```

In either case, you should see something similar to this:

![image](https://github.com/user-attachments/assets/3428ac17-5e1e-4ac2-a9d2-6ff82ff601c8)

## Python
You have the option for how you want to handle this. Since <b>Stream Link Manager for Channels</b> is designed to be a background service, just running the program like this...

```
python slm.py
```

... or with the executable you generated will result in a window sitting there like this:

![image](https://github.com/user-attachments/assets/fb277770-52dc-4ddf-b554-48e6e534041d)

If that does not bother you, you should be fine. However, it is recommended to build an automation script that will start the process in the background and make it start upon login/bootup. For instance, if you wanted to do this in MacOS, you would:

1. Make a new file called ```slm.app``` in the directory you created earlier, open it in Script Editor, and enter the following AppleScript code:

```
do shell script "nohup /usr/local/bin/python3 /[YOUR_SLM_DIRECTORY]/slm.py &> /dev/null &"
```

Replace ```[YOUR_SLM_DIRECTORY]``` with the path you created earlier and save the file.

2. Set the ```slm.app``` to run at startup:

* Open ```System Preferences``` > ```Users & Groups```.
* Select your user account and go to the ```Login Items``` tab.
* Click the ```+``` button and add the ```slm.app``` you created.

## All

1. The first time you start <b>Stream Link Manager for Channels</b>, it may take a couple of minutes before it is available. This is due to it running many activities during initial setup that are not repeated. In later startups, it should be just a few seconds depending upon system performance and internet speeds. If you watch the logs or are in an interactive window, you may see something like this:

![image](https://github.com/user-attachments/assets/d0c7222c-f78d-4ae0-b0e9-6afb04831aa3)

Do not worry if you do not respond to any prompt or the searches fail; there are automatic timeouts that will move the process along and you can make adjustments in the ```Settings``` later.

Also, if you are using Docker, you may still see it says it starts on port 5000. There are no concerns about this as it is being mapped correctly.

2. With the startup complete, you can navigate to the webpage:

```
https://localhost:[YOUR_PORT_HERE]
```

i.e.,

```
Default...
https://localhost:5000

Example Mapped...
https://localhost:7900
```

If you are on a different machine than where <b>Stream Link Manager for Channels</b> is installed, you will need to use the name or IP Address of that machine in place of ```localhost``` and make sure the port is open (as discussed in the installation directions) to be accessed.

3. Once at the location, you should see the homepage:

![image](https://github.com/user-attachments/assets/fce55e3e-f516-4368-b9cc-feb47a5fce31)
  
4. After this, the program is ready to use!

---
# Usage
With the program running, there are a number of activities you should do before getting underway. Also, as a personal preference, if you click on the palette button...

![image](https://github.com/user-attachments/assets/3e6b1823-47cd-4fea-a03f-67523f5c5a11)

... you can change to "Dark Mode":

![image](https://github.com/user-attachments/assets/505aa89b-b63f-4b5e-b4ec-1b22b5da4c08)

Aside from the visuals, everything will function exactly the same.

1. Navigate to the ```Settings``` area. You should see something like this:

![image](https://github.com/user-attachments/assets/e981d21f-36f7-4136-9686-d1166949675c)
   
2. Before doing anything, you must set your country correctly (if it was not found or set incorrectly during initialization). This determines which streaming services are available to you:

![image](https://github.com/user-attachments/assets/61c98f07-8f22-457d-b830-2b80b1c2a5b3)

Note for instance the difference between a US and GB list:

![image](https://github.com/user-attachments/assets/46a30da8-a02d-4ecd-8777-dc0c056dd7fe)

![image](https://github.com/user-attachments/assets/673f17fc-daa6-457a-b937-620f210eba56)

Click ```Save``` after you have selected your country, preferred language, and default number of programs to come up when you search. Please be advised that only certain country/language combinations are valid. A non-exhaustive list is available [here](https://apis.justwatch.com/docs/api/#locales).

![image](https://github.com/user-attachments/assets/0e02c967-6a20-4718-a4be-8b0cf0e26338)

3. With that done, you can select your streaming services and prioritize them. You can select multiple at a time for any of the actions.

![image](https://github.com/user-attachments/assets/8ba75968-061b-4267-aa84-633edad18fce)

![image](https://github.com/user-attachments/assets/c65bdf1b-cd90-4379-b4dd-28412c45f4f9)

Remember to click ```Save``` when complete.

![image](https://github.com/user-attachments/assets/f47f4621-9139-4dc0-9ef8-64a6f082a5a7)

Be sure to keep this up-to-date as you subscribe, unsubscribe, and change preferences. This list is what determines which Stream Links you will get.

4. Next, make sure the Channels URL is correct.

![image](https://github.com/user-attachments/assets/92cd55ac-da0d-4c4e-b2ca-38c70ef267c0)

During initialization, the name of the machine was chosen, however that may not be the case for you. Modify if necessary and click the ```Test``` button to confirm that <b>Stream Link Manager for Channels</b> can attach to Channels DVR.

![image](https://github.com/user-attachments/assets/2168f959-b1af-4923-a049-9e6b746bf157)

In Docker, you may not be able to see local DNS. If that is the case, you can use this:

```
http://host.docker.internal:8089
```

![image](https://github.com/user-attachments/assets/b6129807-849b-48a5-9c53-ec8ee6374f32)

5. Similarly, in order for the program to work correctly, it needs to be pointed to your Channels DVR folder. During initialization, an attempt was made to find the folder. If it could not be discovered, the directory you installed the program in was used.

![image](https://github.com/user-attachments/assets/0298be2e-bc82-4d31-9d70-d5fb41aec790)

You can navigate up the directory structure or manually type in a path to get where you want.

![image](https://github.com/user-attachments/assets/a2375f58-bab8-43e5-b0b9-8229dd5c491e)

When you get to where you want, use the ```Select``` button to set that directory.

![image](https://github.com/user-attachments/assets/a5f97141-0c3f-453e-a6eb-4e269f87a1b9)

If you are using Docker, you should literally have a directory named "channels_folder" right underneath ```/app```.

![image](https://github.com/user-attachments/assets/604166a7-eaa9-4e81-a8c4-61b5bf16874d)

This is the folder you set during installation and should be what you are using. It will look something like this:

![image](https://github.com/user-attachments/assets/7e555c41-41e4-40b2-8e0b-2aad7d48a355)

Do note that you <i>must</i> use the parent Channels DVR directory, not the ```Imports``` or anything similar. If you do not set this correctly or do not have access from the machine you installed <b>Stream Link Manager for Channels</b> on, then you will not be able to generate Stream Links that Channels DVR can see, nor be able to get updates from Channels DVR when programs are watched and deleted.

6. Under ```Advanced / Experimental```, you will find some tools to manage the program and your results.

![image](https://github.com/user-attachments/assets/ecffd3c9-5136-4d5d-91bd-22a5a3e2d7f8)

```Convert Hulu to Disney+``` will take Streak Links for Hulu and make them Disney+ links instead. Note that by my own testing, around 85% of Hulu content is on Disney+, so you may end up with an invalid link. There are workarounds to this that will be discussed later.

![image](https://github.com/user-attachments/assets/ee0c303d-d9c5-40b1-8108-bec8296b15c8)

```Run 'Prune' function in Channels``` is on by default, which means that the program will initiate a delete in Channels DVR for any missing personal media, not just Stream Links. You may decide that you do not want this to run automatically.

7. Finally, there is the ```Scheduler```.

![image](https://github.com/user-attachments/assets/524ab628-705d-48af-8cc5-69e47373e166)

In the ```End-to-End Process```, several steps are taken. These can all be seen and initiated manually in the ```Run Processes``` area.

![image](https://github.com/user-attachments/assets/f9c5ecec-0fef-46f1-97f2-e7dc000ec575)

These tasks are:

* Do a backup
* Update the Streaming Services for any new or removed providers
* Check for new episodes of bookmarked shows
* Import from Channels DVR any Movies and Episodes that have been watched and deleted, marking them as "watched" in <b>Stream Link Manager for Channels</b>
* Find and assign valid Stream Links to bookmarked Movies and Episodes
* In Channels DVR, initiate several steps to make new programs appear, have deleted ones be removed, and update specific files to use revised links

![image](https://github.com/user-attachments/assets/89958211-b692-4e94-82c0-b4a89282dfe7)

While these can all be done manually, it is recommended to set a schedule to run automatically at some point during the day.

![image](https://github.com/user-attachments/assets/698b0151-b64e-413c-89ac-00b2ca70550b)

Note that this can take a significant amount of time, depending upon the number of Movies and Episodes that you have bookmarked. Also, the clock shown should match your system and locale settings. After a process is complete, you can see pertinent notifications in the ```Home``` area (newest on top), such as if there are changes to Streaming Services or new episodes were added.

![image](https://github.com/user-attachments/assets/d3dea0dc-edf6-40eb-bd6c-0d573deafd1f)

If you are looking for additional detail as to what transpired, the ```Logs``` area contains more information.

![image](https://github.com/user-attachments/assets/a5467c2e-8a06-4c3b-b9cc-c51250aa7908)

Unlike the notifications and live process trackers, the log is in order of action.

8. With this all in place, you can now navigate to ```Add Programs```.

![image](https://github.com/user-attachments/assets/a17661c4-cb67-4e20-bf37-5401501bff8f)

Here, you can search for a program you want to bookmark.

![image](https://github.com/user-attachments/assets/08f4b452-5b81-45dd-ba8d-b83ffd6e71c8)

Clicking on a Movie will get you something like this:

![image](https://github.com/user-attachments/assets/e746b77a-0212-41a6-b4cf-3e029096b0d8)

Notice that the ```Search``` and other line buttons are no longer available. You must finish this process by selecting ```Done``` or ```Generate Stream Links```. If you do not generate Stream Links at the time of creation, they will be created (if valid) during the next run of the process as detailed above. Although it is not necessary, if you review the logs, you can generally see a successfully generated Stream Link appear as so:

```
    10 Buildings That Changed America (2013) assigned Stream Link: https://www.kanopy.com/product/10-buildings-changed-america
```

On the other hand, if a Stream Link could not be generated, a reason will be given:

```
    12 Angry Men (1957) assigned Stream Link: None due to 'Watched' status
    Amélie (2001) assigned Stream Link: None due to not found on your selected streaming services
```

In order for a Stream Link to be generated, the Movie or Episode must first have an ```Unwatched``` status, and then be available on one of the Streaming Services that were selected during ```Settings```. The ```Watched / Unwatched``` status applies even if you put in a link of your own to override whatever may or may not be generated. This completely optional feature is not required, so leave it blank if you do not want to put anything there.

![image](https://github.com/user-attachments/assets/2205dad1-7010-4e49-bdda-24b0ebb23134)

Once an add has been complete, you can search again. If we select a Show this time, it will have slightly different options:

![image](https://github.com/user-attachments/assets/4777b509-55ec-400a-8064-0e82f3c37018)

Per episode, season, or for the entire show, you can uncheck to mark it as ```Watched```. It is important to note that in <b>Stream Link Manager for Channels</b>, the term ```Watched``` does not mean that you have ever seen the Episode or Movie. Marking something as ```Watched``` means that you are finished with it and do not want to generate a Stream Link for it. It is the equivalent of deleting an Episode or Movie from within Channels DVR. As discussed above, during the ```Import Updates from Channels``` process, this program checks to see if a generated Stream Link file has been deleted. If it has been, it will be marked as ```Watched``` and will no longer generate a Stream Link in the future. This is why it is equally important for users to not modify or delete the files that are generated by this program. Doing so could make Movies and Shows become erroneously marked as ```Watched```. Only this program should modify anything in the created ```slm``` directories.

Aside from these considerations, per episode, you have the same ```Stream Link Override``` option as a Movie, as well as the ability to put a prefix on the generated file. For instance, by default, a file name will be ```S01E01.strmlnk```. However, as an example, you may want to designate that this is a subtitled episode and that dubbed episodes might become available in the future. For this, a prefix of ```(SUB)``` will result in a file name of ```(SUB) S01E01.strmlnk```.

Sometimes when searching, you might not be able to find the Movie or Show you are looking for. While uncommon (see ```Troubleshooting / FAQ```), it may happen, especially for rare or foreign content. In these cases, you can always create a manual bookmark.

![image](https://github.com/user-attachments/assets/c763e42f-8af8-4e0a-bad7-9e72caff7865)

While Movies are relatively the same as with a search, Shows provide a different setup when clicking ```Add Manual```:

![image](https://github.com/user-attachments/assets/a76be8f9-8ae1-412b-81b2-3414948ec1f5)

![image](https://github.com/user-attachments/assets/ab08b780-1022-46df-83f6-59e5b8c8ba8e)

Note that you will only be allowed to continue once you've correctly put in the number of seasons and episodes per season.

![image](https://github.com/user-attachments/assets/e31c222c-326c-4f9a-9b17-93bd99fe55db)

![image](https://github.com/user-attachments/assets/a4532884-85c5-4f9a-9be7-39069abde5e1)

Here you will see the episodes created as designed by the user. It should be highlighted that manual entries require a ```Stream Link Override``` to be entered, otherwise they will not generate a Stream Link file.

9. Even if a Movie or Show is added through search or manual selection, that does not mean they are set in stone. You can use the ```Modify Programs``` area to make any update as desired.

![image](https://github.com/user-attachments/assets/a0a4e244-0288-48f8-9a81-26705e034665)

For instance, here is a Show that was created using search, but the search will only link to the subtitled episodes. In order to get dubbed episodes, a number of inputs are needed:

![image](https://github.com/user-attachments/assets/189cc7e6-15f8-4611-907a-e6c42755efe1)

While you can delete an episode, if it is a searched bookmark and not a manual one, the episode will just get re-added as "unwatched". Aside from deleting episodes, there is also the ability to add additional episodes:

![image](https://github.com/user-attachments/assets/3797fb27-4249-42db-b099-78e6332a91e4)

This is also a good area just to check on the status of Movies and Shows.

![image](https://github.com/user-attachments/assets/a0d572d4-3fa9-497d-b72b-ec871eb534ed)

Note that the ```Current Stream Link``` field will always be greyed out and unable to be modified. If it is blank, this is an indication that no Stream Link was generated. If you want to change the Stream Link or give it one when none was generated, that is what the ```Stream Link Override``` field is for. After regenerating Stream Links through any method discussed thus far or below, you should see something like this:

![e172001b269677d537a74807fb36538a7d8be685-1](https://github.com/user-attachments/assets/70fa7901-8163-4565-b7b0-f58581dc7b03)

The ```Current Stream Link``` field having the ```skipped_for_override``` value lets you know a Stream Link file was creating using the input ```Stream Link Override``` value that was entered.

Movies are fairly similar to Shows in the options, including updating the ```Title``` and ```Release Year``` itself if the data is incorrect or not how you want it.

![image](https://github.com/user-attachments/assets/5512fe0c-d5ce-44be-ba16-313c31434314)

10. Aside from these functions, there is not much else a user needs to do. There is the ```Files``` area for viewing the backend data that fuels all of the above, as well as exporting those files for backup and migration purposes.

![image](https://github.com/user-attachments/assets/7396d0c1-8956-407b-b5a8-928ecc7675e2)

You can also completely replace those files, though it is not recommended to do so unless you are specifically directed.

Lastly, there is the ```About``` area to see the latest version information, credits, and other information.

![image](https://github.com/user-attachments/assets/a9e9e9f8-759f-4598-accc-d5952740fb96)

---
# Troubleshooting / FAQ
### My Streaming Service is missing
First, make sure you have selected the correct country code and saved. If that is already done, please make a request for the missing service by filling out [this form](https://forms.gle/APyd1t8qs3nhpKRy9). Note that JustWatch is responsible for the availability of Streaming Services and <b>Stream Link Manager for Channels</b> is just a downstream consumer.

### What is the difference between Streaming Services with similar names (i.e., Apple TV vs. Apple TV Plus or Amazon Video vs. Amazon Prime Video)? Should I select both, or is it redundant?
JustWatch is responsible for the list of Streaming Services and their definitions, as such there is no specific guidance from the perspective of this program. However, it is most likely a question of content. For instance, "Apple TV" is Apple's generic name for all streaming content available for purchase and/or rent, just as "Amazon Video" is for Amazon. Each have exclusive content available for paying subscribers, hence "Apple TV Plus" and "Amazon Prime Video". Notably, in these highlighted examples, if you make your settings to have either the basic tier or the subscription tier as the top priority, the Stream Links that are generated will be exactly the same, therefore they will launch the same apps on your device. Due to this, if you have access to the subscription tier, then it may be redundant to have both. Nevertheless, that might not be the case for these or other services with multiple tiers and/or separate apps.

For example, say your Streaming Services were this:

![97d2644b32522dcc850f5a4608838a95bff3796b](https://github.com/user-attachments/assets/4e743963-26f3-4fa5-8c4b-40475a908ffb)

Then, if you add ```About Schmidt```, it will end up with an Amazon link:

![c9eab1a1394f3bcb7d056f3a129b7f3cb343d380](https://github.com/user-attachments/assets/8de2516d-7040-41fd-8324-0b4bfc5ed701)

But if you do this:

![f4d40157aa01c5935903302f7cca492a5e7b4787](https://github.com/user-attachments/assets/29274dff-240d-4598-9e94-7377fd3909e0)

You will end up with Apple links:

![71a9003b70371941fb3bc4c070db70427f05535c](https://github.com/user-attachments/assets/8bb83003-fdf9-4227-b132-39ddb0a514ff)

Yet, if you do this:

![fe08bbfb780da6d40c79e36ecd2bf6321e068cf8](https://github.com/user-attachments/assets/4f956c86-5d97-480e-81f0-675eae5b667f)

You end up with no Stream Link:

![d18818ed755378cf3d0d6d44b06e7179e4ab15c3](https://github.com/user-attachments/assets/48f7318f-7157-41b7-894c-32f98441e2b3)

It is all a function of what services you have selected and the data on JustWatch. As such, it is up to you to manage your services and find the best combination that works for your particular use case.

### My Streaming Service suddenly disappeared and ruined my Stream Links!
While new Streaming Services are brought online and shut down on a regular basis, they also sometimes just change names. Any name change will result in the "old name" being removed and the "new name" being added. If this happens to you, all you need to do is return to the ```Setttings``` area, add the "new name", and prioritize it. The next time you generate your Stream Links, any missing Movies and Shows that were removed will be recreated. Remember, there is a difference between "bookmarking" a Movie or Show and having Stream Links for it.

### The data or links for my program are wrong
JustWatch is the provider for all of the information. If there are any issues, please let them know at feedback@justwatch.com. It is unlikely that they will make an update in a timely manner as they are also dependent upon upstream data, so please take advantage of the manual and override capabilities built into the program.

### Why can't I find the Movie or Show I'm searching for?
<b>Stream Link Manager for Channels</b> is completely dependent upon Movie and Show data from the JustWatch website, which in turn is a consumer of other upstream data. There may be a gap in any of those steps along the way, especially for non-domestic content and independent studios. Sometimes, though, you may even be able to see the content on JustWatch but are unable to find it in this program. There appears to be a small gap of time (usually one or two days) for some content to be completely discoverable by the tools that this program uses.

### I'm able to bookmark a Movie or Show and I know it's on a streaming service I've selected, but a Stream Link still won't generate
Go to the JustWatch website and search for it on there. A Movie or Show might be available, but still be missing links to the appropriate streaming service. If it is brand new, it might also take a day or two until they update their data, which is what <b>Stream Link Manager for Channels</b> uses. Should the links be missing on JustWatch, submit a request to feedback@justwatch.com. If you can confirm JustWatch has a working link on there and it still won't show up in this program, please submit an issue request with as much detail as possible. There may be an edge case for how that particular Movie or Show is stored on JustWatch that this software has not accounted for.

### I generated my Stream Links when I bookmarked my Movie/Show, but it didn't show up in Channels
Generating the Stream Link(s) is not enough; you need to update personal media from within Channels so that it appears inside that interface. There are several ways to deal with this. First and foremost, within this software, under ```Run Processes```, is a button that will do all the necessary steps:

![image](https://github.com/user-attachments/assets/7163353d-9e95-42b9-9bf3-2c942f2aa490)

However, it is worth noting that there is a setting in Channels for how often it scans for personal media:

![image](https://github.com/user-attachments/assets/f68c4f56-c124-4f6b-bf5c-99dce7c38d1f)

As such, you could just wait for that to run if you have it set for a particular interval.

### A Stream Link generated and the Movie or Show is available in Channels, but when I click to launch it, I get an error. It works in the web, though. | The Stream Link works on one platform like iPad OS but does not work in another like tvOS.
There are two main potential situations. The most likely one is that the Streaming Service's app itself is written incorrectly and cannot accept "deep links". Without this, nothing can be done. You can request the app developers to update their program. In a similar vein, they may have programmed it to accept "deep links", but only in a certain way. If there is a systematic method to do a replacement in the generated link, then it could be added to <b>Stream Link Manager for Channels</b>. For instance, JustWatch provides a link for Amazon content like ```watch.amazon.com/detail?gti=``` and this program replaces it with ```www.amazon.com/gp/video/detail/```. If this is the case, please put in a request with exact details like this and it will be added.

There is also the possibility that the link cleaning and replacement process that this program is doing is overzealous. Please also put in a request for those situations and examples of working Stream Links.

### Why do some things play the correct movie/episode automatically and why do others go to a generic landing page for that movie/show?
There are two components that relate to this. First is the quality of the links provided by JustWatch. For instance, with Disney+, JustWatch only has links to generic landing pages and does not have individual episode information like it has for Hulu. There is nothing that can be done aside from requesting that JustWatch updates their data.

The second situation is that even though JustWatch provides links to more generic areas, there may be systematic ways to correct them. As an example, JustWatch provides a link to a movie on Netflix that looks like this: ```http://www.netflix.com/title/81078554```. However, if you replace ```title``` with ```watch```, it will play automatically. This being a “systematic way” to do a replace, it was implemented into <b>Stream Link Manager for Channels</b>. If you have more examples that could be accomplished this way, please put in a request and it will be added.

### I set the scheduler for a certain time and it is running hours earlier/later. | The time showing in the logs is wrong.
Follow the directions related to "TIMEZONE" in the installation steps above.

### I never see anything in the "Live Process Log (While Running)" block
This block is just an indicator to let you know nothing is stuck and that things are still running in the background. For actions that last less than a couple of seconds, not enough time will pass to begin to fill it in. For anything longer, you will see information fill up to the top, but it will all clear out when the process finishes running. However, there are some issues with certain browsers like Safari where it seems incapable of displaying what is happening. Rest assured that although the background process is running as expected, you can always verify in the logs if desired.

### Additional questions or issues
Please ask at the [Channels DVR Community Message Board](https://community.getchannels.com/t/39684).

![SpaceX_ASDS_moving_into_position_for_CRS-7_launch_(18610429514)_EDITED](https://github.com/user-attachments/assets/ab32ab8c-3acd-4c72-b047-8c2bad7ef7d9)
<i>Image (edited) courtesy of SpaceX, CC0, via Wikimedia Commons.</i>

---
# Support

This project and its upkeep is the work of one person. While it is provided free of charge with no expectations of payment, tips are greatly appreciated!

[![image](https://github.com/user-attachments/assets/c2c76924-d4b6-4928-b93f-da958a0c7143)](https://paypal.me/basiljunction)

https://paypal.me/basiljunction
