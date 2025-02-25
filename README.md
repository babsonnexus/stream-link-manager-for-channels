![slm_logo_v2](https://github.com/user-attachments/assets/caf56400-1523-4efa-b9be-7306942f9f06)

---
# Program Overview
Dealing with all the media options available nowadays is a massive pain! For instance, in <b>[Channels DVR](https://getchannels.com/)</b>, users have the ability to add movies and TV show episodes from "<b>[Stream Links](https://getchannels.com/docs/channels-dvr-server/how-to/stream-links/)</b>" and "<b>[Stream Files](https://getchannels.com/docs/channels-dvr-server/how-to/stream-files/)</b>" that are housed alongside all other sources (recordings, local files, etc...). They can also have additional <b>[custom linear stations](https://getchannels.com/custom-channels/)</b> by integrating streaming m3u playlists. And then there are even more ways to customize the experience! While these tools are powerful, they have limitations that often require a fair bit of maintenance and know-how. But what if we could make the whole process a little... easier?

Making these tasks a seamless and simple experience is the purpose behind <b>Streaming Library Manager</b> and it's set of custom extensions. At this time, the available program options are:

* **Streaming Library Manager for Channels** [Default]
* **Streaming Library Manager Solo Edition**

<i><b>NOTE:</b> Some of the visuals seen in the videos and in the screen shots below and throughout this site may be out of date as updates to format and functionality have been applied to the program.</i>

# Extensions
**Streaming Library Manager** is a shell application that houses a set of custom extensions. Some are on by default during installation while others must be initiated. Either way, each can be turned on and off at will with minimal concerns or loss of user data. The currently available extensions are...

## Stream Link/File Manager [SLM]
<details>

<summary><b>Stream Links/Files</b> appear as normal Movies, TV Shows, and Videos...</summary>

... next to recorded and other content. While <b>Stream Files</b> act like regular local media and directly play in the Channels app or admin web page, <b>Stream Links</b> do not. Instead, clicking on one of these launches the appropriate app or web page and plays the content there. In order to do either, the process consists of creating ```.strmlnk``` or ```.strm``` files, putting them in the appropriate location, and running updates in the <b>Channels DVR</b> admin interface to get the content to appear. As can be imagined, the activity around creation and maintenance is incredibly manual and cumbersome.

Enter <b>Stream Link/File Manager</b>!

![image](https://github.com/user-attachments/assets/788cb0a7-4b29-4497-aa8a-4a6c6f8c47f8)

SLM is a background service that sets up a web-based graphical user interface (GUI) for interaction. In the GUI, users can search for any Movie or TV Show and bookmark it. If it cannot be found, manual additions are allowed. Assuming a program is found, for "Stream Links", the software will parse through a user-derived list of Streaming Services (i.e., Disney+, Hulu, Netflix, Hoopla, Kanopy, etc...) in priority order—including setting a preferred service for a particular Movie or Episode as an overarching setting—in order to determine the appropriate link. There is also the ability to input user-derived links, especially when dealing with "Stream Files". After this, the necessary folders and files will be created, along with completing all other administrative tasks. Should a bookmark move from one Streaming Service to another or the user does a manual adjustment, SLM will automatically update everywhere that is required. But this is just the beginning of its capabilities! To learn more, watch the video here:

[![image](https://github.com/user-attachments/assets/0100b998-f9ea-46f8-8baa-59213d398cd3)](https://www.youtube.com/watch?v=5qm_2pU1h1c)

Non-Channels DVR users can still use SLM to keep track of their programs and what services they are available on. See the information below to disable the integration into Channels DVR and switch to "Solo Edition".

</details>

## Playlist Manager [PLM]
<details>

<summary>There are a lot of fantastic methods for...</summary>

... integrating [custom linear stations](https://getchannels.com/custom-channels/) into Channels DVR and some other services, especially from FAST and similar providers like [Pluto](https://github.com/jgomez177/pluto-for-channels), [Plex](https://github.com/jgomez177/plex-for-channels), [Tubi](https://github.com/jgomez177/tubi-for-channels), [Samsung TV+](https://github.com/matthuisman/samsung-tvplus-for-channels), [ESPN+, NFL+](https://github.com/m0ngr31/EPlusTV), and [plenty more](https://getchannels.com/community/)! The problem is, they require a fair bit of maintenance. For instance, there are [whole](https://community.getchannels.com/t/changes-in-channel-lineups/36494) [threads](https://community.getchannels.com/t/2024-channel-lineup-changes-non-us-services/41159) and [tools](https://github.com/mjitkop/Channels-DVR-Monitor-Channel-Lineups) dedicated just to keeping track of which stations have been added and removed. And that doesn't even get into the redundancy of when each of these services have the same stations, but you have to decide which one you want to put in your [Channel Collection](https://getchannels.com/docs/channels-dvr-server/how-to/channel-collections) before it inevitably disappears without you knowing it and not realizing you need to put a replacement in its spot.

Enter **Playlist Manager**!

![image](https://github.com/user-attachments/assets/5533fe58-2165-4a49-a530-b855b7444ec1)

From a high-level perspective, PLM works on the same premise as SLM. The idea is that there is some piece of content that can come from multiple sources that you have legal access to and it will "assign" which one to use based upon a priority that you set. With SLM, it takes a movie or an episode of a TV show and parses through all the streaming services you have set, sees if it is there, and assigns the appropriate Stream Link. Similarly, with PLM, it takes a "parent" station that you define and parses through all the playlists that you have set, sees if there is a matching "child" station, and assigns the appropriate info to m3u and EPG files that can be integrated into Channels DVR or any other similar tool. Still, this is just the beginning of its capabilities!

To see a short demonstration, watch the video here:

[![image](https://github.com/user-attachments/assets/58833ffc-c7e5-4c4e-bfca-d054f9339a53)](https://www.youtube.com/watch?v=Cgd7tUIdpHI)

</details>

## Media Tools Manager [MTM]
<details>
  
<summary>With so many shows, movies, stations, and more available...</summary>

... keeping track and managing them all can be quite difficult. Even using this program can add layers of concerns, considerations, and questions. To resolve this quandary and quagmire is the **Media Tools Manager** extension!

![image](https://github.com/user-attachments/assets/9b5f8a61-0076-4309-a421-f9b90fa71bc8)

Included are a set of activities that can be done to help work with certain datasets, controls, processes, and plenty of other options. This is especially true with functions available within or because of Channels DVR. Details on these instruments are available [in the Wiki](https://github.com/babsonnexus/stream-link-manager-for-channels/wiki).

</details>

---

# Installation, Setup, Management, and Usage

Full details of installation, setup, management, usage, and other concerns are available [in the Wiki](https://github.com/babsonnexus/stream-link-manager-for-channels/wiki).

---
# Support

This project and its upkeep is the work of one person. While it is provided free of charge with no expectations of payment, tips are greatly appreciated!

[![image](https://github.com/user-attachments/assets/c2c76924-d4b6-4928-b93f-da958a0c7143)](https://paypal.me/basiljunction)

https://paypal.me/basiljunction

-
