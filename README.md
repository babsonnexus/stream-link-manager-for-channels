<b>NOTE:</b> This is a placeholder for an upcoming deployment.

---
# Stream Link Manager for Channels
In <b>[Channels DVR](https://getchannels.com/)</b>, users have the ability to add "<b>[Stream Links](https://getchannels.com/docs/channels-dvr-server/how-to/stream-links/)</b>" as local content. These <b>Stream Links</b> appear as normal Movies, TV Shows, and Videos next to recorded and other content but do not play in the Channels app or admin web page directly. Instead, clicking on one of these launches the appropriate app or web page and plays the content there. In order to do this, the process consists of creating ```.strmlnk``` files, putting them in the appropriate location, and running updates in the <b>Channels DVR</b> admin interface to get the programs to appear. As can be imagined, the activity around creation and maintenance is incredibly manual and cumbersome.

Enter <b>Stream Link Manager for Channels</b>!

![862fba89413cdec9184d6ed89eaa129d47630df0](https://github.com/user-attachments/assets/7a2e0b95-1574-4db5-910f-277a2a4e13f1)

<b>Stream Link Manager for Channels</b> is a background service that sets up a web-based graphical user interface (GUI) for interaction. In the GUI, users can search for any Movie or TV Show and bookmark it. If it cannot be found, manual additions are allowed. Assuming a program is found, the software will parse through a user-derived list of Streaming Services (i.e., Disney+, Hulu, Netflix, Hoopla, Kanopy, etc...) in priority order to determine the appropriate link. After this, the necessary folders and files will be created, along with completing all other administrative tasks. Should a bookmark move from one Streaming Service to another, <b>Stream Link Manager for Channels</b> will automatically update everywhere that is required. But this is just the beginning of its capabilities! To learn more, watch the video here:

| EMBEDDED VIDEO COMING SOON |

# Installation
| COMING SOON |

## Docker
| COMING SOON |

## Windows
| COMING SOON |

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
| COMING SOON |

## Docker
| COMING SOON |

## Windows
| COMING SOON |

## Linux
| COMING SOON |

## Python
| COMING SOON |

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
