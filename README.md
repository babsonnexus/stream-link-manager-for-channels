<b>NOTE:</b> This is a placeholder for an upcoming deployment.

---
# Stream Link Manager for Channels
In <b>[Channels DVR](https://getchannels.com/)</b>, users have the ability to add "<b>[Stream Links](https://getchannels.com/docs/channels-dvr-server/how-to/stream-links/)</b>" as local content. These <b>Stream Links</b> appear as normal Movies, TV Shows, and Videos next to recorded and other content but do not play in the Channels app or admin web page directly. Instead, clicking on one of these launches the appropriate app or web page and plays the content there. In order to do this, the process consists of creating ```.strmlnk``` files, putting them in the appropriate location, and running updates in the <b>Channels DVR</b> admin interface to get the programs to appear. As can be imagined, the activity around creation and maintenance is incredibly manual and cumbersome.

Enter <b>Stream Link Manager for Channels</b>!

![image](https://github.com/user-attachments/assets/56f18e08-c1de-4d54-927f-8a5b7afe7e05)

<b>Stream Link Manager for Channels</b> is a background service that sets up a web-based graphical user interface (GUI) for interaction. In the GUI, users can search for any Movie or TV Show and bookmark it. If it cannot be found, manual additions are allowed. Assuming a program is found, the software will parse through a user-derived list of Streaming Services (i.e., Disney+, Hulu, Netflix, Hoopla, Kanopy, etc...) in priority order to determine the appropriate link. After this, the necessary folders and files will be created, along with completing all other administrative tasks. Should a bookmark move from one Streaming Service to another, <b>Stream Link Manager for Channels</b> will automatically update everywhere that is required. But this is just the beginning of its capabilities! To learn more, watch the video here:

| EMBEDDED VIDEO COMING SOON |

<b>NOTE:</b> Some of the visuals seen in the video and in the screen shots below may be out of date as updates to format and functionality have been applied to the program.

---
# Installation
There are several methods to install <b>Stream Link Manager for Channels</b> and only one should be followed. Docker is the preferred route for those who have it as it has the most controlled path. Channels DVR users who have installed [OliveTin for Channels](https://community.getchannels.com/t/37609) and [Project One-Click](https://community.getchannels.com/t/39669) can use those, as well, to simplify the process. If you are unfamiliar with Docker, you can easily [install Docker Desktop as a stand-alone application](https://www.docker.com/products/docker-desktop/). If you are a Windows user, please set up Windows Subsystem for Linux (WSL) first by following [these directions](https://community.getchannels.com/t/espn-fox-sports-with-custom-channels-via-eplustv/31144/591).

As a general note, it does not matter "where" <b>Stream Link Manager for Channels</b> is installed; it could even be placed in the Channels DVR directory. The only requirements are that it must be on a machine and in a location that has directory access to the Channels DVR directory and be able to see the Channels DVR Administrative webpage.

## Docker
If you are not using <i>OliveTin/Project One-Click</i>, it is recommended to install via stack using [Portainer](https://www.portainer.io/) ([Docker Desktop](https://open.docker.com/extensions/marketplace?extensionId=portainer/portainer-docker-extension) | [Docker Standalone](https://docs.portainer.io/start/install-ce/server/docker)). Otherwise, you can use the single command line method as shown below.

### Stack
```
| COMING SOON |
```

### Command Line (Most Cases)
```
docker run -d --restart=unless-stopped --name slm -p [YOUR_PORT_HERE]:5000 -v slm_data:/[TBD] [COMING SOON]:latest
```

### Command Line (Mostly Linux Cases)
```
docker run -d --restart=unless-stopped --name slm --network=host -e PLEX_PORT=[YOUR_PORT_HERE] -v slm_data:/[TBD] [COMING SOON]:latest
```

The default port is 5000, so enter that number if you want to go with that, otherwise use your own preferred value like 7900. It will look something like this:
```
docker run -d --restart=unless-stopped --name slm -p 7900:5000 -v slm_data:/[TBD] [COMING SOON]:latest
docker run -d --restart=unless-stopped --name slm --network=host -e PLEX_PORT=7900 -v slm_data:/[TBD] [COMING SOON]:latest
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

![image](https://github.com/user-attachments/assets/36a4ba44-c30f-437e-9880-b779751e7a96)

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
1. Download the ```slm.sh``` file and place it in the final destination folder. You can also do so by opening a ```Command Prompt```, navigating to that directory, and entering the following command:

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
   
10. You can the see this port as an environment variable (where it can be removed, if necessary):

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
| COMING SOON |

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
| COMING SOON |

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
| COMING SOON |

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

![image](https://github.com/user-attachments/assets/36c44e2d-0227-4ade-a592-5caf37397f7f)
  
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

5. Similarly, in order for the program to work correctly, it needs to be pointed to your Channels DVR folder. During initialization, an attempt was made to find the folder. If it could not be discovered, the directory you installed the program in was used.

![image](https://github.com/user-attachments/assets/0298be2e-bc82-4d31-9d70-d5fb41aec790)

You can navigate up the directory structure or manually type in a path to get where you want.

![image](https://github.com/user-attachments/assets/a2375f58-bab8-43e5-b0b9-8229dd5c491e)

When you get to where you want, use the '''Select``` button to set that directory.

![image](https://github.com/user-attachments/assets/a5f97141-0c3f-453e-a6eb-4e269f87a1b9)

Do note that you need to use the parent Channels DVR directory, not the ```Imports``` or anything similar. If you do not set this correctly or do not have access from the machine you installed <b>Stream Link Manager for Channels</b> on, then you will not be able to generate Stream Links that Channels DVR can see, nor be able to get updates from Channels DVR when programs are watched and deleted.

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

Notice that the ```Search``` and other line buttons are no longer available. You must finish this process by selecting ```Done``` or ```Generate Stream Links```. If you do not generate Stream Links at the time of creation, they will be created (if valid) during the next run of the process as detailed above. You may also want to put in a link of your own to override whatever may be generated, which you optionally have the ability to do. It is not required, so leave it blank if you do not want to put anything there.

![image](https://github.com/user-attachments/assets/2205dad1-7010-4e49-bdda-24b0ebb23134)

Once complete, you can search again. If we select a Show this time, it will have slightly different options:

![image](https://github.com/user-attachments/assets/b90733ae-b34f-436a-9a62-cfba6e46f958)

Per episode, you can uncheck to mark it as watched. Additionally, you have the same Stream Link Override option as a Movie, as well as the ability to put a prefix on the generated file. For instance, by default, a file name will be ```S01E01.strmlnk```. However, as an example, you may want to designate that this is a subtitled episode and that dubbed episodes might become available in the future. For this, a prefix of ```(SUB)``` will result in a file name of ```(SUB) S01E01.strmlnk```.

Sometimes when searching, you might not be able to find the Movie or Show you are looking for. While uncommon (see ```Troubleshooting / FAQ```), it may happen, especially for rare or foreign content. In these cases, you can always create a manual bookmark.

![image](https://github.com/user-attachments/assets/c763e42f-8af8-4e0a-bad7-9e72caff7865)

While Movies are relatively the same as with a search, Shows provide a different setup when clicking ```Add Manual```:

![image](https://github.com/user-attachments/assets/a76be8f9-8ae1-412b-81b2-3414948ec1f5)

![image](https://github.com/user-attachments/assets/ab08b780-1022-46df-83f6-59e5b8c8ba8e)

Note that you will only be allowed to continue once you've correctly put in the number of seasons and episodes per season.

![image](https://github.com/user-attachments/assets/e31c222c-326c-4f9a-9b17-93bd99fe55db)

![image](https://github.com/user-attachments/assets/50bee683-6f8f-46de-8eb4-409d2165385d)

Here you will see the episodes created as designed by the user. It should be highlighted that manual entries require a Stream Link Override to be entered, otherwise they will not generate a Stream Link file.

9. Even if a Movie or Show is added through search or manual selection, that does not mean they are set in stone. You can use the ```Modify Programs``` area to make any update as desired.

![image](https://github.com/user-attachments/assets/a0a4e244-0288-48f8-9a81-26705e034665)

For instance, here is a Show that was created using search, but the search will only link to the subtitled episodes. In order to get dubbed episodes, a number of inputs are needed:

![image](https://github.com/user-attachments/assets/189cc7e6-15f8-4611-907a-e6c42755efe1)

While you can delete an episode, if it is a searched bookmark and not a manual one, the episode will just get re-added as "unwatched". Aside from deleting episodes, there is also the ability to add additional episodes:

![image](https://github.com/user-attachments/assets/3797fb27-4249-42db-b099-78e6332a91e4)

This is also a good area just to check on the status of Movies and Shows.

![image](https://github.com/user-attachments/assets/a0d572d4-3fa9-497d-b72b-ec871eb534ed)

Movies are fairly similar to Shows in the options, including updating the ```Title``` and ```Release Year``` itself if the data is incorrect or not how you want it.

![image](https://github.com/user-attachments/assets/5512fe0c-d5ce-44be-ba16-313c31434314)

10. Aside from these functions, there is not much else a user needs to do. There is the ```Files``` area for viewing the backend data that fuels all of the above, as well as exporting those files for backup and migration purposes.

![image](https://github.com/user-attachments/assets/7396d0c1-8956-407b-b5a8-928ecc7675e2)

You can also completely replace those files, though it is not recommended to do so unless you are directed to do so.

Lastly, there is the ```About``` area to see the latest version information, credits, and other information.

![image](https://github.com/user-attachments/assets/a9e9e9f8-759f-4598-accc-d5952740fb96)

---
# Troubleshooting / FAQ
### My Streaming Service is missing
First, make sure you have selected the correct country code and saved. If that is already done, please make a request for the missing service by filling out [this form](https://forms.gle/APyd1t8qs3nhpKRy9).

Note that JustWatch is responsible for the availability of Streaming Services and <b>Stream Link Manager for Channels</b> is just a downstream consumer.

### The data or links for my program are wrong
JustWatch is the provider for all of the information. If there are any issues, please let them know at feedback@justwatch.com. It is unlikely that they will make an update in a timely manner as they are also dependent upon upstream data, so please take advantage of the manual and override capabilities built into the program.

### Why can't I find the Movie or Show I'm searching for?
<b>Stream Link Manager for Channels</b> is completely dependent upon Movie and Show data from the JustWatch website, which in turn is a consumer of other upstream data. There may be a gap in any of those steps along the way, especially for non-domestic content and independent studios. Sometimes, though, you may even be able to see the content on JustWatch but are unable to find it in this program. There appears to be a small gap of time (usually one or two days) for some content to be completely discoverable by the tools that this program uses.

### I'm able to bookmark a Movie or Show and I know its on a streaming service I've selected, but a Stream Link still won't generate
Go to the JustWatch website and search for it on there. A Movie or Show might be available, but still be missing links to the appropriate streaming service. If it is brand new, it might also take a day or two until they update their data, which is what <b>Stream Link Manager for Channels</b> uses. Should the links be missing on JustWatch, submit a request to feedback@justwatch.com. If you can confirm JustWatch has a working link on there and it still won't show up in this program, please submit an issue request with as much detail as possible. There may be an edge case for how that particular Movie or Show is stored on JustWatch that this software has not accounted for.

### Why do some things play the correct movie/episode automatically and why do other go to a generic landing page for that movie/show?
There are two components that relate to this. First is the quality of the links provided by JustWatch. For instance, with Disney+, JustWatch only has links to generic landing pages and does not have individual episode information like it has for Hulu. There is nothing that can be done aside from requesting that JustWatch updates their data.

The second situation is that even though JustWatch provides links to more generic areas, there may be systematic ways to correct them. As an example, JustWatch provides a link to a movie on Netflix that looks like this: ```http://www.netflix.com/title/81078554```. However, if you replace ```title``` with ```watch```, it will play automatically. This being a “systematic way” to do a replace, it was implemented into <b>Stream Link Manager for Channels</b>. If you have more examples that could be accomplished this way, please put in a request and it will be added.

### | ANOTHER QUESTION |
| MORE COMING SOON |

### Additional questions or issues
Please ask at the [Channels DVR Community Message Board](https://community.getchannels.com/t/39684).

---
# Support

This project and its upkeep is the work of one person. While it is provided free of charge with no expectations of payment, tips are greatly appreciated!

[![image](https://github.com/user-attachments/assets/c2c76924-d4b6-4928-b93f-da958a0c7143)](https://paypal.me/basiljunction)

https://paypal.me/basiljunction
