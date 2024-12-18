![slm_logo_v2](https://github.com/user-attachments/assets/caf56400-1523-4efa-b9be-7306942f9f06)

---
# Streaming Library Manager
Dealing with all the media options available nowadays is a massive pain! For instance, in <b>[Channels DVR](https://getchannels.com/)</b>, users have the ability to add "<b>[Stream Links](https://getchannels.com/docs/channels-dvr-server/how-to/stream-links/)</b>" and "<b>[Stream Files](https://getchannels.com/docs/channels-dvr-server/how-to/stream-files/)</b>" as local content. They can also have additional <b>[custom linear stations](https://getchannels.com/custom-channels/)</b> by integrating streaming m3u playlists. And then there are even more ways to customize the experience! While these tools are powerful, they have limitations that often require a fair bit of maintenance and knowhow. But what if we could make the whole process a little... easier?

Making these tasks a seamless and simple experience is the purpose behind <b>Streaming Library Manager</b> and it's set of custom extensions. At this time, the available program options are:

* **Streaming Library Manager for Channels** [Default]
* **Streaming Library Manager Solo Edition**

<i><b>NOTE:</b> Some of the visuals seen in the videos and in the screen shots below may be out of date as updates to format and functionality have been applied to the program.</i>

# Extensions
**Streaming Library Manager** is a shell application that houses a set of custom extensions. Some are on by default during installation while others must be initiated. Either way, each can be turned on and off at will with minimal concerns or loss of user data. The currently available extensions are...

## Stream Link/File Manager [SLM]
<b>Stream Links/Files</b> appear as normal Movies, TV Shows, and Videos next to recorded and other content. While <b>Stream Files</b> act like regular local media and directly play in the Channels app or admin web page, <b>Stream Links</b> do not. Instead, clicking on one of these launches the appropriate app or web page and plays the content there. In order to do either, the process consists of creating ```.strmlnk``` or ```.strm``` files, putting them in the appropriate location, and running updates in the <b>Channels DVR</b> admin interface to get the content to appear. As can be imagined, the activity around creation and maintenance is incredibly manual and cumbersome.

Enter <b>Stream Link/File Manager</b>!

![image](https://github.com/user-attachments/assets/788cb0a7-4b29-4497-aa8a-4a6c6f8c47f8)

SLM is a background service that sets up a web-based graphical user interface (GUI) for interaction. In the GUI, users can search for any Movie or TV Show and bookmark it. If it cannot be found, manual additions are allowed. Assuming a program is found, for "Stream Links", the software will parse through a user-derived list of Streaming Services (i.e., Disney+, Hulu, Netflix, Hoopla, Kanopy, etc...) in priority order—including setting a preferred service for a particular Movie or Episode as an overarching setting—in order to determine the appropriate link. There is also the ability to input user-derived links, especially when dealing with "Stream Files". After this, the necessary folders and files will be created, along with completing all other administrative tasks. Should a bookmark move from one Streaming Service to another or the user does a manual adjustment, SLM will automatically update everywhere that is required. But this is just the beginning of its capabilities! To learn more, watch the video here:

[![image](https://github.com/user-attachments/assets/0100b998-f9ea-46f8-8baa-59213d398cd3)](https://www.youtube.com/watch?v=5qm_2pU1h1c)

Non-Channels DVR users can still use SLM to keep track of their programs and what services they are available on. See the information below to disable the integration into Channels DVR and switch to "Solo Edition".

## Playlist Manager [PLM]
There are a lot of fantastic methods for integrating [custom linear stations](https://getchannels.com/custom-channels/) into Channels DVR and some other services, especially from FAST and similar providers like [Pluto](https://github.com/jgomez177/pluto-for-channels), [Plex](https://github.com/jgomez177/plex-for-channels), [Tubi](https://github.com/jgomez177/tubi-for-channels), [Samsung TV+](https://github.com/matthuisman/samsung-tvplus-for-channels), [ESPN+, NFL+](https://github.com/m0ngr31/EPlusTV), and [plenty more](https://getchannels.com/community/)! The problem is, they require a fair bit of maintenance. For instance, there are [whole](https://community.getchannels.com/t/changes-in-channel-lineups/36494) [threads](https://community.getchannels.com/t/2024-channel-lineup-changes-non-us-services/41159) and [tools](https://github.com/mjitkop/Channels-DVR-Monitor-Channel-Lineups) dedicated just to keeping track of which stations have been added and removed. And that doesn't even get into the redundancy of when each of these services have the same stations, but you have to decide which one you want to put in your [Channel Collection](https://getchannels.com/docs/channels-dvr-server/how-to/channel-collections) before it inevitably disappears without you knowing it and not realizing you need to put a replacement in its spot.

Enter **Playlist Manager**!

![image](https://github.com/user-attachments/assets/5533fe58-2165-4a49-a530-b855b7444ec1)

From a high-level perspective, PLM works on the same premise as SLM. The idea is that there is some piece of content that can come from multiple sources that you have legal access to and it will "assign" which one to use based upon a priority that you set. With SLM, it takes a movie or an episode of a TV show and parses through all the streaming services you have set, sees if it is there, and assigns the appropriate Stream Link. Similarly, with PLM, it takes a "parent" station that you define and parses through all the playlists that you have set, sees if there is a matching "child" station, and assigns the appropriate info to m3u and EPG files that can be integrated into Channels DVR or any other similar tool. Still, this is just the beginning of its capabilities!

To see a short demonstration, watch the video here:

[![image](https://github.com/user-attachments/assets/58833ffc-c7e5-4c4e-bfca-d054f9339a53)](https://www.youtube.com/watch?v=Cgd7tUIdpHI)

## Media Tools Manager [MTM]
With so many shows, movies, stations, and more available, keeping track and managing them all can be quite difficult. Even using this program can add layers of concerns, considerations, and questions. To resolve this quandary and quagmire is the **Media Tools Manager** extension!

![image](https://github.com/user-attachments/assets/9b5f8a61-0076-4309-a421-f9b90fa71bc8)

Included are a set of activities that can be done to help work with certain datasets, controls, processes, and plenty of other options. This is especially true with functions available within or because of Channels DVR. Details on these instruments are available below.

---
![SpaceX_ASDS_in_position_prior_to_Falcon_9_Flight_17_carrying_CRS-6_(17127808431)_EDITED](https://github.com/user-attachments/assets/c45005cf-081f-4eba-bcb4-fcdccd7ca281)
<i>Image (edited) courtesy of SpaceX, CC0, via Wikimedia Commons.</i>

# Installation
There are several methods to install <b>Streaming Library Manager</b> and only one should be followed. While Docker is the preferred route for those who have it as it is the most controlled path, if you are not comfortable with Docker or are having issues, you can do a straight self-deployment in Windows or Linux, or use Python in any OS type. For those unfamiliar with Docker, you can easily [install Docker Desktop as a stand-alone application](https://www.docker.com/products/docker-desktop/). If you are installing Docker in Windows, please set up Windows Subsystem for Linux (WSL) first by following [these directions](https://community.getchannels.com/t/espn-fox-sports-with-custom-channels-via-eplustv/31144/591). Channels DVR users who have deployed [OliveTin for Channels](https://community.getchannels.com/t/37609) and/or [Project One-Click](https://community.getchannels.com/t/39669) can use those, as well, to simplify the process. Just follow one of these paths throughout the entire installation, doing the step-by-step actions exactly as described.

![SLM Installation Decision Tree v2](https://github.com/user-attachments/assets/0cd52be1-bbe3-45ea-98b3-ecf906d2565f)

You can also follow along in the video here:

[![image](https://github.com/user-attachments/assets/89f8ef22-80bd-42a5-a827-24723f1c4515)](https://www.youtube.com/watch?v=APuUaAvNo-k)
* [00:00:00](https://www.youtube.com/watch?v=APuUaAvNo-k&t=0s) Introduction
* [00:02:14](https://www.youtube.com/watch?v=APuUaAvNo-k&t=134s) Docker Info
* [00:03:19](https://www.youtube.com/watch?v=APuUaAvNo-k&t=199s) Portainer Info
* [00:04:53](https://www.youtube.com/watch?v=APuUaAvNo-k&t=293s) Installation
* [00:10:16](https://www.youtube.com/watch?v=APuUaAvNo-k&t=616s) Installation Verification
* [00:12:36](https://www.youtube.com/watch?v=APuUaAvNo-k&t=756s) First Time Launch
* [00:15:02](https://www.youtube.com/watch?v=APuUaAvNo-k&t=902s) Settings - Channels URL
* [00:16:43](https://www.youtube.com/watch?v=APuUaAvNo-k&t=1003s) Settings - Channels Folder
* [00:18:35](https://www.youtube.com/watch?v=APuUaAvNo-k&t=1115s) Settings - Search Defaults and Streaming Services
* [00:20:50](https://www.youtube.com/watch?v=APuUaAvNo-k&t=1250s) Manage Streaming Services
* [00:27:07](https://www.youtube.com/watch?v=APuUaAvNo-k&t=1627s) Settings - Prune
* [00:28:34](https://www.youtube.com/watch?v=APuUaAvNo-k&t=1714s) Settings - More for Later
* [00:28:51](https://www.youtube.com/watch?v=APuUaAvNo-k&t=1731s) Streaming Services, Files, Notifications, and Logs
* [00:35:40](https://www.youtube.com/watch?v=APuUaAvNo-k&t=2140s) Add Program - Search
* [00:43:27](https://www.youtube.com/watch?v=APuUaAvNo-k&t=2607s) Add Program - Manual
* [00:48:22](https://www.youtube.com/watch?v=APuUaAvNo-k&t=2902s) Modify Programs
* [00:53:07](https://www.youtube.com/watch?v=APuUaAvNo-k&t=3187s) Run Process - Overview and Generate Stream Links
* [00:55:35](https://www.youtube.com/watch?v=APuUaAvNo-k&t=3335s) Stream Link Files
* [00:59:14](https://www.youtube.com/watch?v=APuUaAvNo-k&t=3554s) Run Process - Import Updates from Channels and Modify Episodes
* [01:02:11](https://www.youtube.com/watch?v=APuUaAvNo-k&t=3731s) Delete Episodes and Run Process - Get New Episodes
* [01:04:47](https://www.youtube.com/watch?v=APuUaAvNo-k&t=3887s) Update Media in Channels
* [01:06:08](https://www.youtube.com/watch?v=APuUaAvNo-k&t=3968s) Settings - Scheduler
* [01:08:56](https://www.youtube.com/watch?v=APuUaAvNo-k&t=4136s) Final Thoughts

As a general note, it does not matter "where" <b>Streaming Library Manager</b> is installed; it could even be placed in the Channels DVR directory. The only requirements are that it must be on a machine and in a location that has directory access to the Channels DVR directory and be able to see the Channels DVR Administrative webpage.

## Docker
If you are not using <i>OliveTin/Project One-Click</i>, it is recommended to install via Stack using [Portainer](https://www.portainer.io/) ([Docker Desktop](https://open.docker.com/extensions/marketplace?extensionId=portainer/portainer-docker-extension) | [Docker Standalone](https://docs.portainer.io/start/install-ce/server/docker)). Otherwise, you can use the single command line method as shown below.

### Stack (Docker Compose)
```
services:
  slm:
    image: ghcr.io/babsonnexus/stream-link-manager-for-channels:${TAG:-latest}
    container_name: slm
    ports:
      - "${SLM_PORT:-5000}:5000"
    volumes:
      - ${SLM_HOST_FOLDER:-slm_files}:/app/program_files
      - ${CHANNELS_FOLDER}:/app/channels_folder
    environment:
      - TZ=${TIMEZONE:-UTC}
    restart: unless-stopped

volumes:
  slm_files:
```

Environment variables are included, some required, some optional.

![image](https://github.com/user-attachments/assets/ebb9867e-c619-49f3-a09b-83de5efb6ea3)

* <b>TAG</b> | OPTIONAL | Which version of the program you want. The default is "latest" if you do not add.

* <b>SLM_PORT</b> | OPTIONAL | The port you want to access the program from in the web browser. The default is "5000" if you do not add.

* <b>CHANNELS_FOLDER</b> | REQUIRED | The path to your Channels DVR parent directory (see details in <i>Startup</i> below), i.e., ```/usr/lib/channels-dvr```. You could optionally put in any parent path, so long as the Channels DVR path is accessible somewhere inside. Do know that spaces are fine and you do not have to enclose the path in quotes. In Windows, your slashes should go the opposite of the normal way, i.e., ```C:/Files/Media/Channels DVR```. In MacOS, be sure to include your ```/Volumes``` first, i.e., ```/Volumes/external-hdd/Channels DVR```. Be careful not to put extra characters as your system may then create that directory anyway. In other words, there will be no error as the directory exists, but it is not set to where you want it to be. NOTE: If you are not a Channels DVR user, you can set this to any directory as a placeholder.

* <b>SLM_HOST_FOLDER</b> | OPTIONAL | The path on your local host machine where you would like the program files for **Streaming Library Manager** to reside. As will be discussed in more detail later, these are the files that the application uses to manage the entire solution. The software itself can be replaced at any time, but these files have all of your settings, bookmarks, etc.... As such, you may desire to have them available on your local machine that is hosting Docker in order to back them up. If you do not add this, it will be set to `slm_files` inside the `Volumes` area of Docker Desktop itself.

* <b>TIMEZONE</b> | OPTIONAL | The timezone you want to use. To know what to input, go [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), find your timezone, make sure it is a "Canonical" Type, and use the "TZ identifier". The default is "UTC" if you do not add. Please keep this in mind when using the scheduler function.

### Command Line
Follow the directions above for <b>SLM_PORT</b> in place of ```[YOUR_PORT_HERE]``` (except now it is REQUIRED), <b>CHANNELS_FOLDER</b> in place of ```[PATH_TO_CHANNELS_FOLDER]```, <b>SLM_HOST_FOLDER</b> in place of `[PATH_TO_HOST_SLM_FOLDER]` (except now it is required, too, but you can put in the default value of `slm_files`), and <b>TIMEZONE</b> in place of ```[TIMEZONE]```. Do not leave the ```[``` and ```]``` when putting in your values.

#### Most Cases
```
docker run -d --restart=unless-stopped --name slm -p [YOUR_PORT_HERE]:5000 -v [PATH_TO_HOST_SLM_FOLDER]:/app/program_files -v "[PATH_TO_CHANNELS_FOLDER]":/app/channels_folder -e TZ="[TIMEZONE]" ghcr.io/babsonnexus/stream-link-manager-for-channels:latest
```

#### Some Linux Cases
```
docker run -d --restart=unless-stopped --name slm --network=host -e SLM_PORT=[YOUR_PORT_HERE] -v [PATH_TO_HOST_SLM_FOLDER]:/app/program_files -v "[PATH_TO_CHANNELS_FOLDER]":/app/channels_folder -e TZ="[TIMEZONE]" ghcr.io/babsonnexus/stream-link-manager-for-channels:latest
```

#### Examples
```
docker run -d --restart=unless-stopped --name slm -p 7900:5000 -v "C:/Temp/SLM Host Test":/app/program_files -v "C:/Files/Media/Channels DVR":/app/channels_folder -e TZ="America/New_York" ghcr.io/babsonnexus/stream-link-manager-for-channels:latest
docker run -d --restart=unless-stopped --name slm --network=host -e SLM_PORT=7900 -v slm_files:/app/program_files -v "/somewhere/channels_dvr":/app/channels_folder -e TZ="America/New_York" ghcr.io/babsonnexus/stream-link-manager-for-channels:latest
```

## Windows
1. Download the [slm.bat](https://github.com/babsonnexus/stream-link-manager-for-channels/blob/main/executables/slm.bat) file and place it in the final destination folder.

![image](https://github.com/user-attachments/assets/49a843e6-3819-4a3a-9513-a8c6768d269f)

2. Open a ```Command Prompt```, navigate to that directory, and enter the following command:

```
slm.bat install
```

If using PowerShell, type in:

```
.\slm.bat install
```

3. You will be given one last chance to decide if you want to do the installation. Note that an installation will remove any previous instance of <b>Streaming Library Manager</b> at that location. This is unlike the "upgrade" below which will maintain all your files and settings.

![image](https://github.com/user-attachments/assets/a93612b4-2159-47ae-8ccb-d959078bea8b)

4. The process will then run normally until complete. You should see something similar to this when done:

![image](https://github.com/user-attachments/assets/fc8cd8bc-8f0a-4670-ae76-2d46b5d88190)
  
5. In your folder, you should now have this:

![image](https://github.com/user-attachments/assets/8cbdac78-5dba-469d-ad58-93459bdf6056)
   
6. OPTIONAL: By default, <b>Streaming Library Manager</b> runs on port 5000. You can change this to another port by typing in this command:

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
1. Download the [slm.sh](https://github.com/babsonnexus/stream-link-manager-for-channels/blob/main/executables/slm.sh) file and place it in the final destination folder.

![image](https://github.com/user-attachments/assets/49a843e6-3819-4a3a-9513-a8c6768d269f)

You can also do so by opening a terminal, navigating to that directory, and entering the following command:

```
wget -q -O "slm.sh" 'https://raw.githubusercontent.com/babsonnexus/stream-link-manager-for-channels/main/executables/slm.sh'
```
   
2. Either way, once there, change the security level on the ```slm.sh``` file:

```
chmod +x "slm.sh"
```

3. Execute the installation with this command:

```
./slm.sh install
```

4. You will be given one last chance to decide if you want to do the installation. Note that an installation will remove any previous instance of <b>Streaming Library Manager</b> at that location. This is unlike the "upgrade" below which will maintain all your files and settings.

![image](https://github.com/user-attachments/assets/53160f56-0c47-4b07-be7b-dfc9bd4cfd03)

5. The process will then run normally until complete. You should see something similar to this when done:

![image](https://github.com/user-attachments/assets/964fe66b-ff01-485d-8751-5797945082d8)

... a whole lot of lines related to installing requirements and building the executable...

![image](https://github.com/user-attachments/assets/0d3d5f52-cb55-45de-917e-ec0618c81f58)

6. In your folder, you should now have this:

![image](https://github.com/user-attachments/assets/9b3e34e1-7da2-4001-866e-292df7bf52ae)

7. OPTIONAL: By default, <b>Streaming Library Manager</b> runs on port 5000. You can change this to another port by typing in this command:

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

1. Download the [slm_python.zip](https://www.dropbox.com/scl/fi/b5loo1yndyfasqgek1vv3/slm_python.zip?rlkey=g1wcyl22kewg05cu55nqssbt7&dl=1) file and place it in the final destination folder.
   
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

6. OPTIONAL: You can change the port for <b>Streaming Library Manager</b> by creating a permanent Environment Variable called ```SLM_PORT``` (case sensitive) and giving it a value of the port you want to use. If you don't, the program will run on port 5000. You may also need to open the port up to bypass firewalls or other such settings.

---
# Upgrade
As with any program, there may be a need to update the code for stability, bug fixes, or general upgades. When a new version is released, you will see notes in the header next to the current version and in the `Notifications` area:

![image](https://github.com/user-attachments/assets/1a302de2-83e1-48a1-956b-98107c0e36ac)

![image](https://github.com/user-attachments/assets/046d0188-02a8-4d00-919a-4023316ae948)

Additionally, the program will also check for updates at regular intervals that you can control in the `Settings` area:

![image](https://github.com/user-attachments/assets/2b5e682a-5c1a-4b3c-afb7-55ef7a9786b5)

By default, it is set to be 'On', run every 24 hours, and run at the time it was created. You can modify and control all of these settings, however a check will still be run when the program starts up no matter what.

Further, you can run a check at any time in the 'Run Processes' area:

![image](https://github.com/user-attachments/assets/8b62ca68-22cc-4b8c-b342-820d8f2d8a63)

Do note that you will not see anything there, but will see the other indicators as highlighted above.

Beyond the internal options, you can set up a watch on this Github repo.

![bbae83c81a2ddd80776fe1b443bbf2c8bbc3d412](https://github.com/user-attachments/assets/42411117-e081-402b-9ffe-703c48172158)

This way, you'll get an email whenever a new version is released, plus you can see exactly what has changed.

No matter the method, you can easily upgrade using the directions below. The key item to consider is that during an upgrade, the ```program_files``` directory is protected.

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
1. In ```Command Prompt```, navigate to your <b>Streaming Library Manager</b> directory and type in the following command:

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
1. In a terminal, navigate to your <b>Streaming Library Manager</b> directory and type in the following command:

```
./slm.sh upgrade
```

2. As the process runs, you should see something like this:

![image](https://github.com/user-attachments/assets/0338a0be-d516-43df-9132-cbd9047269de)

... a whole lot of lines related to installing requirements and building the executable...

![image](https://github.com/user-attachments/assets/2c036863-41ad-46bb-b236-96d68787a003)

3. The most important thing is that the ```/slm``` application was terminated or not running, allowing the upgrade to take place. After the upgrade, you will need to restart the program manually or with a reboot. See <b>Startup</b> below.

## Python
1. Make sure <b>Streaming Library Manager</b> is closed and is not running in the background.

2. Copy the ```program_files``` directory under ```_internal``` to a safe location.

3. Completely delete <i>all</i> the files and subfolders.

4. Follow the directions for installation and replace the entire file content that were deleted in the prior step. If you have built an executable, you will have to redo those steps, as well.
   
5. Move the ```program_files``` directory you saved earlier back under the ```_internal``` directory.

6. Restart the program and everything should work the same as before.

---
# Startup
Since <b>Streaming Library Manager</b> is designed to run as a service that you access through a webpage, it should be set up to launch at system startup. There may also be reasons to start manually, like after initial installation or an upgrade.

## Docker
1. There is nothing additional to do as Docker will automatically start up.

## Windows
1. In ```Command Prompt```, navigate to your <b>Streaming Library Manager</b> directory and type in the following command:

```
slm.bat startup
```

If using PowerShell, type in:

```
.\slm.bat startup
```

2. You may get a pop-up asking for permissions. Agree and continue until the process completes and you see something like this:

![image](https://github.com/user-attachments/assets/53d24b29-8701-4cb1-96e5-9c7f93c48d73)

3. If you open ```Task Scheduler```, you should now see a task called "Streaming Library Manager":

![image](https://github.com/user-attachments/assets/c909fde6-3ca5-4b73-9ff5-09f65c945f32)

4. The next time you reboot, <b>Streaming Library Manager</b> will automatically start. Similarly, you can manually start it by either...
   
* Running the process directly in ```Task Scheduler```
* Double clicking on the ```slm.bat``` file
* In ```Command Prompt```, typing in ```slm.bat```

5. No matter the method, it may look like nothing has happened, but if you start ```Task Manager``` you will see a ```slm.exe``` running in the background:

![image](https://github.com/user-attachments/assets/de995caf-d7fc-4d82-b428-a2b1592d0629)

## Linux
1. In a terminal, navigate to your <b>Streaming Library Manager</b> directory and type in the following command:

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

4. The next time you reboot, <b>Streaming Library Manager</b> will automatically start. Similarly, you can manually start it by entering:
   
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
You have the option for how you want to handle this. Since <b>Streaming Library Manager</b> is designed to be a background service, just running the program like this...

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

1. The first time you start <b>Streaming Library Manager</b>, it may take a couple of minutes before it is available. This is due to it running many activities during initial setup that are not repeated. In later startups, it should be just a few seconds depending upon system performance and internet speeds. If you watch the logs or are in an interactive window, you may see something like this:

![image](https://github.com/user-attachments/assets/c94b5031-94af-4741-9d0c-3a7e1ee38fc2)

While the Initialization process attempts to find all the necessary values—even noting when it has to use a substitute value—do not worry if any of the searches faulter. There are various levels of safety checks and automatic timeouts that will move the process along. More so, you can always make adjustments in the ```Settings``` later. To be clear, any "error" or the like shown are not failures and are expected behavior. Everything directly related to <b>Streaming Library Manager</b> is managed from the ```Settings``` area as discussed below.

Also worth highlighting: if you are using Docker, you may still see it says it starts on port 5000. There are no concerns about this as it is being mapped correctly so long as you gave a port value.

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

If you are on a different machine than where <b>Streaming Library Manager</b> is installed, you will need to use the name or IP Address of that machine in place of ```localhost``` and make sure the port is open (as discussed in the installation directions) to be accessed.

3. Once at the location, you should see the homepage:

![image](https://github.com/user-attachments/assets/84da1206-eb4d-4c94-b23c-363cd64601f5)
  
4. After this, the program is ready to use!

---
# Usage
With the program running, there are a number of activities you should do before getting underway. Also, as a personal preference, if you click on the palette button...

![image](https://github.com/user-attachments/assets/3e6b1823-47cd-4fea-a03f-67523f5c5a11)

... you can change to "Dark Mode":

![image](https://github.com/user-attachments/assets/8ef5d208-c671-4bc0-85c7-b57a42505eeb)

Aside from the visuals, everything will function exactly the same.

## General
### Settings: Introduction

1. Navigate to the ```Settings``` area. You should see something like this:

![image](https://github.com/user-attachments/assets/e981d21f-36f7-4136-9686-d1166949675c)

### Settings: Advanced / Experimental

2. Under ```Advanced / Experimental```, you will find some tools to manage the program and your results.

![image](https://github.com/user-attachments/assets/ddb19693-c241-4fa1-8628-ad3f58b09b48)

* `Channels DVR Integration` is on by default. You have the option to turn it off if you are not a Channels DVR user or have a special use case where it makes sense not to have it on. It will hide everything related to Channels DVR (including mentions of it in text and logos), turning the program into **Streaming Library Manager Solo Edition**. Further, any actions that try to connect to Channels are disabled. You can also ignore any of the settings related to Channels below.
* `Use Stream Link/File Manager` is on by default. You have the option to turn it off if you are not using those tools. It will then hide everything related to SLM.
* `Use Playlist Manager` is off by default. This is discussed in detail below.
* ```Run 'Prune' function in Channels``` is on by default, which means that the program will initiate a delete in Channels DVR for any missing personal media, not just Stream Links. You may decide that you do not want this to run automatically.

### Settings: Channels URL

3. Next, make sure the Channels URL is correct.

![image](https://github.com/user-attachments/assets/b24ac2e4-2dd3-4319-acb0-35763f18582e)

During Initialization, an attempt was made at determining the correct link. However, that may not have succeeded or the selection may not be the case for you. Modify if necessary and click the ```Test``` button to confirm that <b>Streaming Library Manager</b> can attach to Channels DVR.

![image](https://github.com/user-attachments/assets/2b1c427e-f6f0-4b4d-9d0c-3a2c1139281f)

You also have the option to let <b>Streaming Library Manager</b> attempt to determine the link again by clicking the ```Scan``` button:

![image](https://github.com/user-attachments/assets/1a945756-a29d-478d-a6fa-711823f8ab48)

In Docker, you may not be able to see local DNS. If that is the case, you can use this:

```
http://host.docker.internal:8089
```

![image](https://github.com/user-attachments/assets/b6129807-849b-48a5-9c53-ec8ee6374f32)

### Settings: Channels Directory

4. Similarly, in order for many of the program functions to work correctly, it needs to be pointed to your Channels DVR folder. During initialization, an attempt was made to find the folder. If it could not be discovered, the directory you installed the program in was used.

![image](https://github.com/user-attachments/assets/0298be2e-bc82-4d31-9d70-d5fb41aec790)

You can navigate up the directory structure or manually type in a path to get where you want.

![image](https://github.com/user-attachments/assets/a2375f58-bab8-43e5-b0b9-8229dd5c491e)

When you get to where you want, use the ```Select``` button to set that directory.

![image](https://github.com/user-attachments/assets/a5f97141-0c3f-453e-a6eb-4e269f87a1b9)

If you are using Docker, you should literally have a directory named "channels_folder" right underneath ```/app```.

![image](https://github.com/user-attachments/assets/604166a7-eaa9-4e81-a8c4-61b5bf16874d)

This is the folder you set during installation and should be what you are using. It will look something like this:

![image](https://github.com/user-attachments/assets/7e555c41-41e4-40b2-8e0b-2aad7d48a355)

Do note that you <i>must</i> use the parent Channels DVR directory, not the ```Imports``` or anything similar. If you do not set this correctly or do not have access from the machine you installed <b>Streaming Library Manager</b> on, then you will not be able to do many things, such as generate Stream Links that Channels DVR can see or be able to get updates from Channels DVR when programs are watched and deleted.

### Settings: Scheduler + Run Processes and Logs

5. Finally, there is the ```Scheduler```.

![image](https://github.com/user-attachments/assets/ee84c754-a47b-4169-9e8d-b56527fbfe19)

Depending upon your choices above, there will be several automations that you can set timing, frequency, and other details for. For intstance, in the ```Stream Links/Files: End-to-End Process```, several steps are taken. These can all be seen and initiated manually in the ```Run Processes``` area.

![image](https://github.com/user-attachments/assets/ff2ce43c-892d-44b7-ad31-372904f5c43f)

These tasks are:

* Update the Streaming Services for any new or removed providers
* Check for new episodes of bookmarked shows
* Import from Channels DVR any Movies and Episodes that have been watched and deleted, marking them as "watched" in SLM
* Find and assign valid Stream Links to bookmarked Movies and Episodes
* In Channels DVR, initiate several steps to make new programs appear, have deleted ones be removed, and update specific files to use revised links

![image](https://github.com/user-attachments/assets/89958211-b692-4e94-82c0-b4a89282dfe7)

While these can all be done manually, it is recommended to set a schedule to run automatically at some point during the day. Note that this can take a significant amount of time, depending upon the number of Movies and Episodes that you have bookmarked. Also, the clock shown should match your system and locale settings. After a process is complete, you can see pertinent notifications in the ```Home``` area (newest on top), such as if there are changes to Streaming Services or new episodes were added.

![image](https://github.com/user-attachments/assets/d3dea0dc-edf6-40eb-bd6c-0d573deafd1f)

If you are looking for additional detail as to what transpired, the ```Logs``` area contains more information.

![image](https://github.com/user-attachments/assets/a5467c2e-8a06-4c3b-b9cc-c51250aa7908)

Unlike the notifications and live process trackers, the log is in order of action.

## Stream Link/File Manager

### Settings: Search Defaults

1. Before doing anything, you must set your country correctly (if it was not found or set incorrectly during initialization). This determines which streaming services are available to you:

![image](https://github.com/user-attachments/assets/f8f279fc-d04a-4fec-9cfa-2dae775694d1)

Note for instance the difference between a US and GB list:

![image](https://github.com/user-attachments/assets/46a30da8-a02d-4ecd-8777-dc0c056dd7fe)

![image](https://github.com/user-attachments/assets/673f17fc-daa6-457a-b937-620f210eba56)

Click ```Save``` after you have selected your country, preferred language, default number of programs to come up when you search, and if you want to hide previously bookmarked programs from search. Please be advised that only certain country/language combinations are valid. A non-exhaustive list is available [here](https://apis.justwatch.com/docs/api/#locales).

### Settings: Streaming Services

2. With that done, you can select your streaming services and prioritize them. You can select multiple at a time for any of the actions.

![image](https://github.com/user-attachments/assets/8ba75968-061b-4267-aa84-633edad18fce)

![image](https://github.com/user-attachments/assets/c65bdf1b-cd90-4379-b4dd-28412c45f4f9)

Remember to click ```Save``` when complete.

![image](https://github.com/user-attachments/assets/f47f4621-9139-4dc0-9ef8-64a6f082a5a7)

Be sure to keep this up-to-date as you subscribe, unsubscribe, and change preferences. This list is what determines which Stream Links you will get.

### Settings: Stream Link Mappings

3. SLM uses JustWatch as the source for the final generated Stream Links. While a process is undertaken to "clean" the links of any tracking information, some may still be imperfect or have ways to work better with a "mapping". You have the ability to activate and/or create/delete those mappings:

![image](https://github.com/user-attachments/assets/78ff1c44-11a6-4023-be21-de7b798cdb22)

Out-of-the-box, several are included that are all functional as well as informative:

* Changing ```hulu.com/watch``` to ```disneyplus.com/play``` allows Hulu content to play within in the Disney+ app. This is off by default, but can be activated by clicking the checkbox and saving. It should be noted that not all Hulu content is available within Disney+. To work around this, ```Stream Link Overrides``` may be used as discussed below.
  
* All Netflix Movies and Shows come from JustWatch with a link that contains ```netflix.com/title```, which goes to the landing page of that content. However, if you change ```title``` to ```watch```, it will play automatically. However, that only works for Movies, hence why that is in the dropdown selection ```For Object Type```. This is on be default.
  
* While JustWatch does provide Amazon links directly for Movies and Shows, the links that are given do not work in all situations, notably on Apple TV and the web. To get around this, the links can be converted with the string ```watch.amazon.com/detail?gti=``` being replaced with ```www.amazon.com/gp/video/detail/```. This is on by default. 

* At the time of this program's launch, ```Vudu``` had changed its name to ```Fandango at Home``` and created a newly named app, but did not fix the app to accept ```Vudu``` links that it was still using. Since deep linking directly is not possible, this mapping says to replace any link that contains ```vudu.com``` in its entirety with a link that will just launch their app generically. This is off by default.

It is not required to set these immediately; they can be added, deleted, or modified at any time.

### Search and Add Movies and Shows

4. With this all in place, you can now navigate to ```Add Programs```.

![image](https://github.com/user-attachments/assets/7ac9c760-3b69-446c-b953-8ae694fe3f6d)

Here, you can search for a program you want to bookmark.

![image](https://github.com/user-attachments/assets/e6e42d72-4d9c-46e9-95d8-6ef645e7bdbf)

The default order is by best-match / popularity, but you can also choose to have the results re-display in alphabetical order and/or filter only for Movies or Shows.

![image](https://github.com/user-attachments/assets/b9b5ed84-4430-4eb4-af6a-631880a28909)

Another option for searching is to see what has been ```New & Updated``` on the Streaming Services you selected in the ```Settings``` above. This will give you a list of Movies and Shows that have been added or updated on those services.

![image](https://github.com/user-attachments/assets/6c188e4e-ee57-4e14-b109-01b57e389f17)

The list is limited to a single day and 100 entries, displayed alphabetically. Clicking ```Today``` will give you that list for this day. On the other hand, you can select any date and click ```New & Updated``` to get the Movies and Shows from that day.

![image](https://github.com/user-attachments/assets/00bd77ad-edc1-43de-90c7-962f040d8df8)

![image](https://github.com/user-attachments/assets/811af5d8-3221-4d59-8f96-3f8a0bedda80)

No matter the search method, clicking on a Movie will get you something like this:

![image](https://github.com/user-attachments/assets/86499e3f-2e3a-44be-97d3-a7d0dc2e05ec)

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

![image](https://github.com/user-attachments/assets/534fa1d0-bf7d-48a0-b880-a68b52826cba)

Per episode, season, or for the entire show (or a Movie if bookmarking that), you can uncheck to mark it as ```Watched```. It is important to note that in SLM, the term ```Watched``` does not mean that you have ever seen the Episode or Movie. Marking something as ```Watched``` means that you are finished with it and do not want to generate a Stream Link/File for it. It is the equivalent of deleting an Episode or Movie from within Channels DVR. As discussed above, during the ```Import Updates from Channels``` process, this program checks to see if a generated Stream Link/File file has been deleted. If it has been, it will be marked as ```Watched``` and will no longer generate a Stream Link/File in the future. This is why it is equally important for users to not modify or delete the files that are generated by this program. Doing so could make Movies and Shows become erroneously marked as ```Watched```. Only this program should modify anything in the created ```slm``` directories.

Aside from these considerations, per episode, you have the same ```Stream Link Override``` option as a Movie, as well as the ability to put a prefix on the generated file. For instance, by default, a file name will be ```S01E01.strmlnk```. However, as an example, you may want to designate that this is a subtitled episode and that dubbed episodes might become available in the future. For this, a prefix of ```(SUB)``` will result in a file name of ```(SUB) S01E01.strmlnk```. More so, there is a selection called ```Special Action``` that can also be propagated down to the individual episodes from the entire show or per season perspective:

![image](https://github.com/user-attachments/assets/db039128-8fd1-4a2c-aa3b-1d7c8d8cb4c8)

In most cases, users will leave this as ```None```, but there are situations when it will necessary to take advantage of these functions. For instance, if your Movie or Show is available on multiple Streaming Services but you prefer it to be on one with a lower priority, you can make that assignment. Another situation might be that you have a link to the media directly and, thus, would want to create a "Stream File" instead of "Stream Link". In this case, you would select ```Make STRM```.

While searching, you may come across programs you are not interested in. In these cases, you can always hit the ```Hide``` button to the right of the program so that it never appears again.

![image](https://github.com/user-attachments/assets/8637f48e-e64a-42b9-b300-ea9b86784d35)

For Shows in particular, it may be an older title that is no longer putting out episodes. In these cases, it is not worth the time and resources to have SLM continue to search for new episodes. As such, there is the ability under ```Bookmark Action``` to ```Disable Get New Episodes```. Note that this is also where the "Hide" option is, the same as just shown from the button above. In most cases, though, this too will be left as ```None```.

![image](https://github.com/user-attachments/assets/167cd956-c9a3-47f0-93dd-9fffbc4790a7)

There is also the option to select multiple results and do an action on all of them at once.

![386863080-48a9664a-0962-49a2-b3c4-a39cb748c675](https://github.com/user-attachments/assets/8f0b917e-af35-4f78-9998-7f21d19a4398)

Checking off one or multiple programs will make buttons for `Bookmark All Selected` and `Hide All Selected` appear. Hiding will then do exactly that while bookmarking will give you a final screen for each of the programs you have selected. Otherwise, the activities are exactly the same as going one-by-one.

Sometimes when searching, you still might not be able to find the Movie or Show you are looking for. While uncommon (see ```Troubleshooting / FAQ```), it may happen, especially for rare or foreign content. In these cases, you can always create a manual bookmark.

![image](https://github.com/user-attachments/assets/c763e42f-8af8-4e0a-bad7-9e72caff7865)

While Movies are relatively the same as with a search, Shows provide a different setup when clicking ```Add Manual```:

![image](https://github.com/user-attachments/assets/a76be8f9-8ae1-412b-81b2-3414948ec1f5)

![image](https://github.com/user-attachments/assets/ab08b780-1022-46df-83f6-59e5b8c8ba8e)

Note that you will only be allowed to continue once you've correctly put in the number of seasons and episodes per season.

![image](https://github.com/user-attachments/assets/e31c222c-326c-4f9a-9b17-93bd99fe55db)

![image](https://github.com/user-attachments/assets/a4532884-85c5-4f9a-9be7-39069abde5e1)

Here you will see the episodes created as designed by the user. It should be highlighted that manual entries require a ```Stream Link Override``` to be entered, otherwise they will not generate a Stream Link file.

### Modify Programs

5. Even if a Movie or Show is added through search or manual selection, that does not mean they are set in stone. You can use the ```Modify Programs``` area to make any update as desired.

![image](https://github.com/user-attachments/assets/a0a4e244-0288-48f8-9a81-26705e034665)

For instance, here is a Show that was created using search, but the search will only link to the subtitled episodes. In order to get dubbed episodes, a number of inputs are needed:

![image](https://github.com/user-attachments/assets/189cc7e6-15f8-4611-907a-e6c42755efe1)

While you can delete an episode, if it is a searched bookmark and not a manual one, the episode will just get re-added as "unwatched". Aside from deleting episodes, there is also the ability to add additional episodes:

![image](https://github.com/user-attachments/assets/3797fb27-4249-42db-b099-78e6332a91e4)

This is also a good area just to check on the status of Movies and Shows.

![image](https://github.com/user-attachments/assets/a0d572d4-3fa9-497d-b72b-ec871eb534ed)

Note that the ```Current Stream Link``` field will always be greyed out and unable to be modified. If it is blank, this is an indication that no Stream Link was generated. If you want to change the Stream Link, give it one when none was generated, or input something for a Stream File, that is what the ```Stream Link Override``` field is for. After regenerating Stream Links/Files through any method discussed thus far or below, you should see something like this:

![e172001b269677d537a74807fb36538a7d8be685-1](https://github.com/user-attachments/assets/70fa7901-8163-4565-b7b0-f58581dc7b03)

![image](https://github.com/user-attachments/assets/8fa9c358-e442-4de3-b266-f53dd95fc5ba)

The ```Current Stream Link``` field having the ```skipped_for_override``` or ```strm_must_use_override``` value lets you know a Stream Link/File file was creating using the ```Stream Link Override``` value that was input.

Movies are fairly similar to Shows in the options, including updating the ```Title``` and ```Release Year``` itself if the data is incorrect or not how you want it.

![image](https://github.com/user-attachments/assets/5512fe0c-d5ce-44be-ba16-313c31434314)

Programs that were previously hidden are not show in the list by default. However, you can select the ```Show Hidden``` button and they will then be in the list.

![image](https://github.com/user-attachments/assets/9f1baf57-3da4-4954-960a-c9afd313780e)

At this point, you can edit them and make them not hidden by changing their ```Bookmark Status``` to "None".

## Playlist Manager

### Installation
1. Go to ```Settings``` and scroll down to ```Advanced / Experimental```.

![b3ae8a7666bb3fa0fe028f1567cb36f5db453d3b](https://github.com/user-attachments/assets/e0d7d3a2-c3e6-4c56-921f-7b15afc52258)

2. Check the box for ```Use Playlist Manager``` and click save. When you do so, a lot of things will become available both in the front-end and the back-end. Most notably, you will now see ```Playlists``` in the navigation pane.

![cbaa23e3a34a18b5dd9f00ac7ee5b85518645d7b](https://github.com/user-attachments/assets/52d924a4-b6dd-4fb6-b144-7c8c4305a3a0)

### Initialization

3. Navigating to the ```Playlists``` area, you will see something like this:

![image](https://github.com/user-attachments/assets/9216dd27-1d67-4542-a393-5d934aa40bf2)

4. In the navigation pane, select ```Manage Playlists```. Scrolling towards the bottom, you should see the ```Enter Playlists``` section, appearing somewhat like this:

![image](https://github.com/user-attachments/assets/4884c3e4-b6d6-4181-aa3b-ee878a8f5123)

5. Here you can add links to your m3u(s) and corresponding Electronic Program Guide(s) [EPG(s)], giving each one a unique name. Be sure the correct "Stream Format" is selected for dealing with different types of interpretation engines.

![image](https://github.com/user-attachments/assets/74f2b66c-3d51-45ae-8efd-35ed803dfbd1)

6. You can always modify these after the fact, too, including renaming or removing them with little to no repercussions. However, if you remove all Playlists, it is considered a complete reset of the tool. Additionally, instead of removing, you can just make the playlist "inactive" by unchecking the appropriate box. Note that when you do so, the playlist will be hidden from prioritization and its child stations will also not be visible for parent assignment (both of which are discussed below). Otherwise, as shown in the example image, you can add ones with only a m3u and no EPG, especially those that already have Gracenote IDs for guide data. You can even pull the m3u(s) from built-in Channels DVR lists like the ones for HDHR and TVE. Since some stations are both in either of those and on FAST providers, this gives a way to match them together, if desired.

![e3581e7eadd6f020fdd63b662a40469816592e3a](https://github.com/user-attachments/assets/b3880f05-4fd4-4164-900c-0fd0df06771c)

7. As another option, you can upload your own playlists and guide files.

![image](https://github.com/user-attachments/assets/0f314a1b-3c4d-43fe-a88f-12654134b51d)

8. When you upload a file, it is given a link that you can use in the ```Enter Playlists``` area above.

![image](https://github.com/user-attachments/assets/a601ad03-1226-4c92-8424-682719ed38a3)

9. As you add each source, they are given a priority. You adjust that value in the ```Prioritize Playlists``` section. In the end, PLM will parse through each of these sources in priority order (excluding inactive playlists) to find the matches for individual stations, and this sequence will determine which one to use. For instance, *CBS News* is available on many providers, but based upon the order shown below, in this example it will take the one from Channels (TVE) over the ones on Plex, Pluto, etc...

![31a0a4916609bf4c678658bdedfcbb2867934f05](https://github.com/user-attachments/assets/c5fb201b-1aea-4661-98c1-6b79814fd688)

10. Back on the ```Main Page```, there is a button called ```Update Station List```. Pressing this will then read through each of the m3u playlists and gather all the stations for your assignment.

![a4ceabc270ea0fb923a608dbf46342026816a893](https://github.com/user-attachments/assets/7fbe62bb-65c9-4aea-a75a-b2b52bf7f002)

11. In a later step, we will discuss automating this to get updates on a daily basis. In the meantime, you should now have a complete list of available stations to work with.

![db663d71a1c6de53f69fff5c475b1d7b2200af02](https://github.com/user-attachments/assets/6f03a8fa-c91b-4d6c-9814-8c2aa5184223)

### Regular Activity
As shown at the top, PLM will give you the status for each of the stations it finds in the provided m3u(s). "Unassigned" stations are ones that need to be given a "Parent". The Parents themselves are a grouping of the stations that came from the m3u sources.

12. Navigating to ```Unassigned Stations``` and clicking the ```Expand / Collapse``` button will show you all the stations (in alphabetical order) that are looking to have a Parent assignment. The only way a station becomes available is if it has been assigned to a Parent. There is no penalty for not assigning a station aside from not being able to see what's new.

![61319a5dd6c4add232bb800b8d90ecb557443b02](https://github.com/user-attachments/assets/9d882890-d405-4852-8b06-3092bdcdf5d5)

13. To the far right, there is a button called ```Make Parent```. Clicking this will create a new Parent that has the same name as that station and assigns that station as a "Child" to that "Parent". For instance, if we click ```Make Parent``` for *00s Replay*, we will end up with a new Parent like this in the ```Parent Stations``` area:

![image](https://github.com/user-attachments/assets/38307393-08e3-49d6-8c41-d5b10d71ea07)

14. You also have the option to create and edit parents directly. This can be especially useful when the names provided by the m3u are not clear or specific enough and you want to easily see what they are.

![ac9a0dbf9eeb74b23c4414e6643246e05706d4b4](https://github.com/user-attachments/assets/a83f4467-0a95-4e21-9ef8-34c9a85af2f7)

15. There are also several optional fields to override what may be provided by the child stations. For instance, you may have a Gracenote ID for guide data that was not provided and can plug that in here.

![db5992139e909c7e580a171e6122e62eb4203add](https://github.com/user-attachments/assets/adda03d3-72b1-425c-8bad-d30dc9912287)

16. You can even override the default priority order of the Playlists if you have a use case to make a specific source for one particular station be the first choice.

![739952044ed62f8951e9a4b75f8f08920b143be9](https://github.com/user-attachments/assets/e4fa1027-ec5a-4b8a-99ef-4aa822a4f567)

17. As you add Parents through either method or en masse as described below, they become available for direct assignment. For instance, if we take the first *21 Jump Street* and click ```Make Parent```, the second one will now have that new Parent as an option for selection.

![b9ca3de36b2aa5565aa0b0ca3822563b410b7d2b](https://github.com/user-attachments/assets/9f17791e-601e-41bd-bf26-a07e19f38ccc)

18. After doing so, click the ```Set Parent``` button to save this selection. The same activity can also be done with the "Ignore" option. This is like the "Hidden" choice in Channels to make a station not available in the final product.

![8a41e4f7e4e08fa0ba3c2a6ee64b48bff8d88bc8](https://github.com/user-attachments/assets/156b582c-2ae0-4168-bf61-78e6e310e993)

19. You can also make multiple selections at a time and then click the floating ```Save All``` button to set each of them. This includes the "Make Parent" option so you can push multiple stations into new Parents all at once.

![eb7cf5e9c730cb3bfb37e6192b104e538cf42a8b](https://github.com/user-attachments/assets/2f4049b7-cb23-4b6c-bb8a-713bb816360c)

20. Conversely, you can set the Parent for everything visible on the screen at once using the `Set Visible` button.

![385899452-9cf8da42-a639-443f-a6ed-f2b87a516bea](https://github.com/user-attachments/assets/1448813e-7894-47a3-a946-7668cfdec093)

This works with both scrolling downward to get more or all available stations, or using the filter functionality.

21. Everything that is set for a station can always be changed and even undone in the ```Modify Assigned Stations``` section:

![image](https://github.com/user-attachments/assets/7909d3d0-108c-4f6c-8b7f-c77ca8dc8ad8)

22. As you make your assignments, the chart on top of the ```Main Page``` updates to let you know the status of your stations. "Assigned to Parent" means that a Parent has at least one child and will create a unique station. "Redundant" means that a Parent has additional children (i.e., repeating/same stations) and that they are available if the higher priority option goes away for any reason.

![7f176279fe9fa3788090d2d1a9b458cf5a6ab46b](https://github.com/user-attachments/assets/940e11f0-b7ec-44c5-8302-236a5285b4b3)

23. At any time, you can also click the ```Update m3u(s) and XML EPG(s)```. This is the process that will parse through all of these parent-child assignments and create the playlists and guide links that you will load into Channels DVR or other tools. It should be noted that when PLM processes a station, if a certain field does not have a value in the higher priority playlist, it will take that field from a lower priority one. For instance, if your preferred playlist does not have a "description", but a lower priority one does, it will get that "description" and make it available in the final output.

![e3ba0b4c08c7abceba0f1f7e10c04bdacc010572](https://github.com/user-attachments/assets/8a931bb1-da96-4ac7-988b-ff0c1b1ceb41)

24. As before, this process can be automated and is discussed later. At this point, though, you will now have fully active m3u and EPG files that you can integrate. The links will be visible at the top of the page:

![ecb35db14a4e60ba4eca7d72d322b2d1147cb004](https://github.com/user-attachments/assets/0f8a4331-3243-4b56-9707-0c9916a452e1)

25. "Gracenote" m3u files do not have XML EPG data because the guide information comes from the loaded Gracenote ID. On the other hand, all the "Non-Gracenote" m3u(s) do require their own corresponding XML EPG. Either way, each is split between "HLS" and "MPEG-TS" options since those are interpreted by Channels DVR differently. Also, depending on circumstances described below, you may end up with multiple of these lists.

![7d29a9e78fb4a76389438800549f02a6ff5f67ea](https://github.com/user-attachments/assets/0b122137-be06-4262-b106-07a132a9103d)

26. At this point, you have everything you need and can continue using PLM as a regular function. However, there are several settings and automated routines to consider before proceeding.

### Settings and Automation
27. Back in the ```Settings``` area under ```Advanced / Experimental```, at the spot where you turned on PLM, there are two additional inputs. One is the station number you would like to start at, with a default of ```10000```. Each new Parent that is added will increase this value by one.

![bc46bb2060f475b904d04176ab173352bb2dcd95](https://github.com/user-attachments/assets/7ced31ed-9352-49a7-8925-ebaf83266727)

28. The other choice is the ```Max Stations per m3u```, with a default of ```750```. This is the number of stations that will be in an m3u file before it splits into a new file, 750 being the maximum Channels DVR allows at the time of this writing. This can be set to any positive integer. It should be noted the XML EPG data is split by the same stations in the end-result m3u(s).

29. Further up under the ```Scheduler``` section are two more things for you to set. The first is the equivalent of the ```Update Station List``` button. Turning this on will run a process once per day at the time you set to update the station list, thus giving you an automated way to handle changes and get new selections in the ```Unassigned Stations``` section.

![936126de4bb11635dc6f575b548c8f63f93c8ca1](https://github.com/user-attachments/assets/2f9ac1d2-8991-40bb-811d-556fc9c02dd0)

30. When stations are updated, there are notices that are also made available in the ```Notifications``` pane in the ```Home``` area. You will get info on "Added", "Removed", and "Modified" stations, the latter meaning there has been a change in at least one field of provided data.

![ceb602109eadd02f18f731e8246ff6ce6aff2a1f](https://github.com/user-attachments/assets/3c2ddb87-e24b-43ad-94c7-a4ec29112caf)

31. In the same vein, you can also turn on the process to update the m3u and EPG files at regular intervals.

![62eff4d47820765cfaf4accecb3a928ff0666318](https://github.com/user-attachments/assets/9853492b-17b5-4352-969b-ad69c9e2d6a6)

32. Unlike the updating the station list, this one allows you to make a selection to how frequently you want the action to happen based upon a starting time. For instance, if we leave the time at ```02:01 PM``` and select ```Every 6 hours```, it will run at ```02:01 PM```, ```08:01 PM```, ```02:01 AM```, and ```08:01 AM```.

![1a5fe30027fe5e5072079da26e0e3aa1006799cf](https://github.com/user-attachments/assets/a70e379b-6b4f-4b50-b5d8-5d71c5bf2f9f)

33. As with the previous automation, this one will also give you notifications. In all cases, there is additional detail available in the ```Logs``` area.

![d06f0c709256037b1995f6ca47e10cff68e7084f](https://github.com/user-attachments/assets/499a632b-fd2c-47ce-b19b-d40232770091)

34. With these in place and set, the process will take care of itself and you should be good to go!

## Media Tools Manager

### Installation and Setup

MTM is on by default, although the functions that are available are limited by which other extensions are also active. You also have the option of disabling MTM at any time in the `Settings` area:

![image](https://github.com/user-attachments/assets/8f387492-117b-4d55-bf05-6f3b49dda82a)

### Reports & Queries
In order to streamline answers to some questions you may have, certain reports and queries have been made available in the same named area:

![image](https://github.com/user-attachments/assets/bbe0be58-9c25-4536-aa00-1528b8d73e31)

To navigate the data, there are several functions such as number of results per page...

![image](https://github.com/user-attachments/assets/3a735041-a960-4f67-bdec-291f5bb93c59)

... number of entries being show out of how many...

![image](https://github.com/user-attachments/assets/8a989fc0-e3c0-42a7-94cd-dad556a01fb3)

... page navigation between those entries...

![image](https://github.com/user-attachments/assets/dcfd5a71-bdbf-4b67-87ba-42e7931c4cd8)

... and the ability to filter both by a general search...

![image](https://github.com/user-attachments/assets/2ca0a342-75d4-4b7e-84a1-ad800c44cc83)

... and on individual columns:

![image](https://github.com/user-attachments/assets/5ff9add2-2837-4e3f-ba20-aaf41a603b62)

### Gracenote Search
**Gracenote Search** is a tool used to find the correct `Gracenote ID` for a station, something very useful for getting guide data when using extensions like PLM. While there are other solutions available for this in various locations like **OliveTin for Channels**, the MTM approach is to have the visual interaction be at the forefront. Please note that an active subscription to Channels DVR is required for this to function.

First, users should expand the top panel to reveal a frame linked to the *Zap2It* website, which uses the Gracenote guide data. After selecting a guide location and type, the list of stations is made available. Most importantly is the short code below each station. For instance, the code for "NFL Network" is "NFLHD".

![image](https://github.com/user-attachments/assets/e6a49db1-722f-4d8a-b670-54829f6327bf)

Copying this code into the search field makes it easy to find the expected result instead of guessing what it might be.

![image](https://github.com/user-attachments/assets/fb11f1dc-1f08-4c57-a4b9-b73890bb8e9a)

However, you can still put whatever you want in search, including things like a call sign.

![image](https://github.com/user-attachments/assets/2865a8eb-b975-4825-9bab-f0b614e81a09)

Once you identify the correct station, you can copy the `Gracenote ID` from the first column and use it elsewhere.

### CSV Explorer

**CSV Explorer** is a tool to effortlessly look through data provided by web csv files, most notably what is available from the *Channels DVR API & Feed Explorer*. Due to the close interaction between these concepts, an active subscription to Channels DVR is required for this to function. 

![image](https://github.com/user-attachments/assets/7fdff2f2-e234-4401-a1e2-644e1fdfa594)

Much like **Gracenote Search**, this requires the user to provide a value of what they would like to explore. In this case, it is a link that is created by the Channels DVR API & Feed Explorer.

![image](https://github.com/user-attachments/assets/4dd9b60e-0164-4080-b095-b3715a5bcbe9)

You should expand the frame to enter `API & Feed Explorer` and make the appropriate selections to get what you are looking for. You must select "CSV" as the output option.

![image](https://github.com/user-attachments/assets/61db1e95-b283-43a6-aef5-0b457329cd1c)

It is recommended to be cognizant of how large the data set is. The bigger, the longer it will take to render. This is especially true when there are images involved. Either way, once you have made your selection, copy the link that is created into the field below and click the `Load` button. This will create a table of the results that you can then filter and explore through.

![image](https://github.com/user-attachments/assets/6da1ea12-1043-4ba3-baeb-e2aced6f45f3)

### Automation

**Automation** allows users to execute specialized tasks to run various steps to help manage their media or deal with specific issues/use cases. All current and future automation options are `Off` by default with a time of whenever they are added. It is up to the user to decide if they want to schedule, run only demand, or not use at all.

![image](https://github.com/user-attachments/assets/7b1d87a8-5f07-4ade-9386-4a7c7ce68836)

For example, there is the **Automation** for `Reset Channels DVR Passes`.

![image](https://github.com/user-attachments/assets/1540269d-d616-4904-ac3d-f0c4b8378950)

As the description shows, this will pause and resume all active passes in Channels DVR (hence the `Channels DVR Interface` is required to be on to have this available). This specific sequence was created to resolve an issue where sometimes a lower priority pass is used for scheduling a future recording and—when the guide updates—the lower priority is maintained instead of shifting to the higher priority. When this runs, all scheduled recordings are reset to their expected settings.

# Administrative Functions

### Files
Aside from the function covered above, there is not much else a user needs to do. There is the ```Files``` area for viewing the backend data that fuels all of the above, as well as exporting those files for backup and migration purposes.

![image](https://github.com/user-attachments/assets/632b69a6-5562-48bc-b1db-a1448ff75661)

You can also completely replace those files, though it is not recommended to do so unless you are specifically directed.

### About
Lastly, there is the ```About``` area to see the latest version information, credits, and other information.

![image](https://github.com/user-attachments/assets/4214ae67-76de-41d2-b63d-64d8d2eeebdc)

When an upgrade is available, you can check here to see the details.

---
# Troubleshooting / FAQ
### [SLM] My Streaming Service is missing
First, make sure you have selected the correct country code and saved. If that is already done, please make a request for the missing service by filling out [this form](https://forms.gle/APyd1t8qs3nhpKRy9). Note that JustWatch is responsible for the availability of Streaming Services and SLM is just a downstream consumer.

### [SLM] What is the difference between Streaming Services with similar names (i.e., Apple TV vs. Apple TV Plus or Amazon Video vs. Amazon Prime Video)? Should I select both, or is it redundant?
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

### [SLM] My Streaming Service suddenly disappeared and ruined my Stream Links!
While new Streaming Services are brought online and shut down on a regular basis, they also sometimes just change names. Any name change will result in the "old name" being removed and the "new name" being added. If this happens to you, all you need to do is return to the ```Setttings``` area, add the "new name", and prioritize it. The next time you generate your Stream Links, any missing Movies and Shows that were removed will be recreated. Remember, there is a difference between "bookmarking" a Movie or Show and having Stream Links for it.

### [SLM] The data or links for my program are wrong
JustWatch is the provider for all of the information. If there are any issues, please let them know by filling out [this form](https://support.justwatch.com/hc/en-us/requests/new) or emailing them at feedback@justwatch.com. It is unlikely that they will make an update in a timely manner as they are also dependent upon upstream data, so please take advantage of the manual and override capabilities built into the program, or using mapping if possible.

### [SLM] Why can't I find the Movie or Show I'm searching for?
SLM is completely dependent upon Movie and Show data from the JustWatch website, which in turn is a consumer of other upstream data. There may be a gap in any of those steps along the way, especially for non-domestic content and independent studios. Sometimes, though, you may even be able to see the content on JustWatch but are unable to find it in this program. There appears to be a small gap of time (usually one or two days) for some content to be completely discoverable by the tools that this program uses.

### [SLM] I'm able to bookmark a Movie or Show and I know it's on a streaming service I've selected, but a Stream Link still won't generate
Go to the JustWatch website and search for it on there. A Movie or Show might be available, but still be missing links to the appropriate streaming service. If it is brand new, it might also take a day or two until they update their data, which is what SLM uses. Should the links be missing on JustWatch, submit a request by filling out [this form](https://support.justwatch.com/hc/en-us/requests/new) or sending an e-mail to feedback@justwatch.com. If you can confirm JustWatch has a working link on there and it still won't show up in this program, please submit an issue request with as much detail as possible. There may be an edge case for how that particular Movie or Show is stored on JustWatch that this software has not accounted for.

### [SLM] I generated my Stream Links when I bookmarked my Movie/Show, but it didn't show up in Channels
Generating the Stream Link(s) is not enough; you need to update personal media from within Channels so that it appears inside that interface. There are several ways to deal with this. First and foremost, within this software, under ```Run Processes```, is a button that will do all the necessary steps:

![image](https://github.com/user-attachments/assets/7163353d-9e95-42b9-9bf3-2c942f2aa490)

However, it is worth noting that there is a setting in Channels for how often it scans for personal media:

![image](https://github.com/user-attachments/assets/f68c4f56-c124-4f6b-bf5c-99dce7c38d1f)

As such, you could just wait for that to run if you have it set for a particular interval.

### [SLM] A Stream Link generated and the Movie or Show is available in Channels, but when I click to launch it, I get an error. It works in the web, though. | The Stream Link works on one platform like iPad OS but does not work in another like tvOS.
There are two main potential situations. The most likely one is that the Streaming Service's app itself is written incorrectly and cannot accept "deep links". Without this, nothing can be done. You can request the app developers to update their program. In a similar vein, they may have programmed it to accept "deep links", but only in a certain way. If there is a systematic method to do a replacement in the generated link, then it could be added to SLM in the ```Stream Link Mappings``` setting. For instance, JustWatch provides a link for Amazon content like ```watch.amazon.com/detail?gti=``` and, by default, this program replaces it with ```www.amazon.com/gp/video/detail/```. If this is the case, please add a new mapping. Further, do let the community know about your mapping and, if it is useful for many people, it will be added to the default list that comes with a new installation.

There is also the possibility that the link cleaning and replacement process that this program is doing is overzealous. Please also put in a request for those situations and examples of working Stream Links.

### [SLM] Why do some things play the correct movie/episode automatically and why do others go to a generic landing page for that movie/show?
There are two components that relate to this. First is the quality of the links provided by JustWatch. For instance, with Disney+, JustWatch only has links to generic landing pages and does not have individual episode information like it has for Hulu. There is nothing that can be done aside from requesting that JustWatch updates their data.

The second situation is that even though JustWatch provides links to more generic areas, there may be systematic ways to correct them. As an example, JustWatch provides a link to a movie on Netflix that looks like this: ```http://www.netflix.com/title/81078554```. However, if you replace ```title``` with ```watch```, it will play automatically. This being a “systematic way” to do a replace, it was included in the ```Stream Link Mappings``` settings as highlighted above. If you have more examples that could be accomplished this way, please let the community know. If they are deemed benefitial for other users, they will be added to the default list that comes with a new installation.

### [PLM] Is Playlist Manager a complete replacement for all my sources in Channels?
There is no "right way" to approach this; PLM is a tool to use as you please, with thousands of possibilities on what you might want to do. While one user might desire to have PLM playlists be the only sources in Channels, others will not choose to go down that path. For instance, there is no great replacement for how Channels handles TVE (unless you have Frndly or use ADBTuner or CC4C for every station), so a user who wants those stations would have to keep that as a source no matter what, just at a lower priority so it is not used by default.

In the end, it's totally up to the end user how far they want to take this. Give it a try, play around, and see what happens. There's no danger in just starting PLM up!

### [PLM] I do want all my stations to come from Playlist Manager. How do I get rid of everything else?
There are too many potential sources to answer that question. Most available m3u playlists can be imported directly, so that is one-for-one. For something like the HDHR, you could do this:

```
http://hdhomerun.local/lineup.m3u

or...

http://[IP_ADDRESS_OF_HDHR]/lineup.m3u
```

However, if you do that, you must set your `Gracenote ID` at the Parent level correctly. Similarly, you could use tools like [ADBTuner](https://community.getchannels.com/t/36822) or [Chrome Capture for Channels](https://community.getchannels.com/t/36667/130) for getting more "traditional" cable/TVE stations into Channels. PLM will accept playlists for both of those and plenty of other tools discussed elsewhere.

### [PLM] None of my m3u/XML links work and I see errors like `WARNING: m3u URL not found for '[MY_M3U_OR_XML]'. Skipping...`
First, make sure your link is `http` instead of `https` as that latter may not be able to be read. Next, there may be an issue with how the program is trying to talk to certain location, especially if that location is in-network and/or you are using Docker; most especially if you are going container-to-container. In either case, the potential solutions are, instead of `http://localhost:[PORT]`, try:

* `http://[COMPUTER_NAME].local:[PORT]`
* `http://[IP_ADDRESS]:[PORT]`
* `http://host.docker.internal:[PORT]`

Also, you can test these in the `Channels URL` section of `Settings`, making sure you get a positive response. Just be sure not to save!

### [PLM] I set custom logos and they show up in the web, but they don't appear in the Channels app
If you see a situation like this...

![Missing Station Logos](https://github.com/user-attachments/assets/b632a80d-2c33-4707-b19e-e71f2e078694)

... the most likely culprit is the file type for the images. The Channels DVR apps require images to be either `.png` or `.jpg`, unlike the web which can accept about anything.

### [GEN] I set the scheduler for a certain time and it is running hours earlier/later. | The time showing in the logs is wrong.
Follow the directions related to "TIMEZONE" in the installation steps above.

### [GEN] I never see anything in the "Live Process Log (While Running)" block
This block is just an indicator to let you know nothing is stuck and that things are still running in the background. For actions that last less than a couple of seconds, not enough time will pass to begin to fill it in. For anything longer, you will see information fill up to the top, but it will all clear out when the process finishes running. However, there are some issues with certain browsers like Safari where it seems incapable of displaying what is happening. Rest assured that although the background process is running as expected, you can always verify in the logs if desired.

### Additional questions or issues
For general **Streaming Library Manager** support, please visit the [Channels Community Message Board](https://community.getchannels.com/t/42369) or open a question under `Issues` above. Otherwise, for specific extension questions, see:

* **[SLM](https://community.getchannels.com/t/39684)**
* **[PLM](https://community.getchannels.com/t/41719)**
* **[MTM](https://community.getchannels.com/t/42368)**

![SpaceX_ASDS_moving_into_position_for_CRS-7_launch_(18610429514)_EDITED](https://github.com/user-attachments/assets/ab32ab8c-3acd-4c72-b047-8c2bad7ef7d9)
<i>Image (edited) courtesy of SpaceX, CC0, via Wikimedia Commons.</i>

---
# Support

This project and its upkeep is the work of one person. While it is provided free of charge with no expectations of payment, tips are greatly appreciated!

[![image](https://github.com/user-attachments/assets/c2c76924-d4b6-4928-b93f-da958a0c7143)](https://paypal.me/basiljunction)

https://paypal.me/basiljunction
