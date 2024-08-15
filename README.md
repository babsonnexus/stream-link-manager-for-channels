<b>NOTE:</b> This is a placeholder for an upcoming deployment.

---
# Stream Link Manager for Channels
In <b>[Channels DVR](https://getchannels.com/)</b>, users have the ability to add "<b>[Stream Links](https://getchannels.com/docs/channels-dvr-server/how-to/stream-links/)</b>" as local content. These <b>Stream Links</b> appear as normal Movies, TV Shows, and Videos next to recorded and other content but do not play in the Channels app or admin web page directly. Instead, clicking on one of these launches the appropriate app or web page and plays the content there. In order to do this, the process consists of creating ```.strmlnk``` files, putting them in the appropriate location, and running updates in the <b>Channels DVR</b> admin interface to get the programs to appear. As can be imagined, the activity around creation and maintenance is incredibly manual and cumbersome.

Enter <b>Stream Link Manager for Channels</b>!

![image](https://github.com/user-attachments/assets/56f18e08-c1de-4d54-927f-8a5b7afe7e05)

<b>Stream Link Manager for Channels</b> is a background service that sets up a web-based graphical user interface (GUI) for interaction. In the GUI, users can search for any Movie or TV Show and bookmark it. If it cannot be found, manual additions are allowed. Assuming a program is found, the software will parse through a user-derived list of Streaming Services (i.e., Disney+, Hulu, Netflix, Hoopla, Kanopy, etc...) in priority order to determine the appropriate link. After this, the necessary folders and files will be created, along with completing all other administrative tasks. Should a bookmark move from one Streaming Service to another, <b>Stream Link Manager for Channels</b> will automatically update everywhere that is required. But this is just the beginning of its capabilities! To learn more, watch the video here:

| EMBEDDED VIDEO COMING SOON |

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
docker run -d --restart=unless-stopped --name slm -p [YOUR_PORT_HERE]:5000 [COMING SOON]:latest
```

### Command Line (Mostly Linux Cases)
```
docker run -d --restart=unless-stopped --name slm --network=host -e PLEX_PORT=[YOUR_PORT_HERE] [COMING SOON]:latest
```

The default port is 5000, so enter that number if you want to go with it, otherwise use your own preferred value like 7900. It will look something like this:
```
docker run -d --restart=unless-stopped --name slm -p 7900:5000 [COMING SOON]:latest
docker run -d --restart=unless-stopped --name slm --network=host -e PLEX_PORT=7900 [COMING SOON]:latest
```

## Windows
1. Download the ```slm.bat``` file and place it in the final destination folder.
   
2. Open a ```Command Prompt```, navigate to that directory, and enter the following command:

```
slm.bat install
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

7. You will be prompted to enter a port number of your choice:

![image](https://github.com/user-attachments/assets/b36a3b06-7ba9-4008-a5ac-8c86471bc185)

8. You can also see this port as an environment variable (where it can be removed, if necessary).

![image](https://github.com/user-attachments/assets/36a4ba44-c30f-437e-9880-b779751e7a96)

9. Follow the directions on the screen of closing the current ```Command Prompt``` and opening a new one. In the new ```Command Prompt```, you can confirm that that the port variable is being read correctly by typing:

```
echo %SLM_PORT%
```

10. You should see something similar to this:

![image](https://github.com/user-attachments/assets/18fdab7d-9f11-4890-ad69-9fbe56424601)

11. With all this in place, you are now safe to start the program!

## Linux
| COMING SOON |

## Python
| COMING SOON |

# Upgrade
| COMING SOON |

## Docker
| COMING SOON |

## Windows
| COMING SOON |

## Linux
| COMING SOON |

## Python
| COMING SOON |

# Startup
Since <b>Stream Link Manager for Channels</b> is designed to run as a service that you access through a webpage, it should be set up to run at startup of a system. There may also be reasons to start manually, like after initial installation.

## Docker
1. There is nothing additional to do as Docker will automatically start up.

## Windows
1. In ```Command Prompt```, navigate to your <b>Stream Link Manager for Channels</b> directory and type in the following command:

```
slm.bat startup
```

2. You may get a pop-up asking for permissions. Agree and continue until the process completes and you see something like this:

![image](https://github.com/user-attachments/assets/bf1fee02-bdf0-407e-a625-2b771915e3b0)

3. If you open ```Task Scheduler```, you should now see a task called "Stream Link Manager for Channels":

![image](https://github.com/user-attachments/assets/d2642b2d-d476-4678-af83-d7da3df09dbb)

4. The next time you reboot, <b>Stream Link Manager for Channels</b> will automatically start. Similarly, you can manually start it by either...
   
* Running the process directly in ```Task Scheduler```
* Double clicking on the ```slm.bat``` file
* In ```Command Prompt```, typing in ```slm.bat```

5. No matter the method, it may look like nothing has happened, but if you start ```Task Manager``` you will see a ```slm.exe``` running in the background:

![image](https://github.com/user-attachments/assets/de995caf-d7fc-4d82-b428-a2b1592d0629)

## Linux
| COMING SOON |

## Python
| COMING SOON |

## All

1. The first time you start <b>Stream Link Manager for Channels</b>, it may take a couple of minutes before it is available. This is due to it running many activities during initial setup that are not repeated. In later startups, it should be around 30 seconds depending upon system performance and internet speeds.

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

If you are on a different machine than where <b>Stream Link Manager for Channels</b> is installed, you will need to use the name or IP Address of that machine and make sure the port is open to be accessed.

3. Once at the location, you should see the homepage:

![image](https://github.com/user-attachments/assets/36c44e2d-0227-4ade-a592-5caf37397f7f)
  
4. After this, the program is ready to use!

# Usage
| COMING SOON |

# Troubleshooting / FAQ
### My Streaming Service is missing
First, make sure you have selected the correct country code and saved. If that is already done, please make a request for the missing service by filling out [this form](https://forms.gle/APyd1t8qs3nhpKRy9).

Note that JustWatch is responsible for the availability of Streaming Services and <b>Stream Link Manager for Channels</b> is just a downstream consumer.

### The data or links for my program are wrong
JustWatch is the provider for all of the information. If there are any issues, please let them know at feedback@justwatch.com.

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
