# Web Application Usage

Instructions on how to setup and use the web-app

&nbsp;

***

## Pre-Requisites:

* Docker Desktop *([official site](https://www.docker.com/products/docker-desktop/))*
* OBS *(vers >= 28)*

&nbsp;

***

## Setup

1. Pull the latest version of the web app:

[!img](./imgs/001.png)

2. Tune the container's resources:

[!img](./imgs/002.png)

3. Start the container:

[!img](./imgs/003.png)

4. Access the application in a web-browser

* `http://<pc-host>:7064`
  * Typically found at [localhost](http://localhost:7064)
  * If the web-app is hosted on a machine separate from the computer running OBS, use the local IP address of the machine when accessing the web-app

## Usage

1. Set up-desired templates in OBS

> **NOTES:** Templates can be any media source, however, non-standard source types (i.e. browser sources from custom OBS plugins) are not guarenteed to work.

2. Enable WebSocket server in OBS

> **NOTES:** As long as the version of OBS is `28.0` or greater, no additional plugins are needed as WebSocket Server shipped with this and later versions of OBS.

  a. Tools / Websocket Server Settings

  b. Check Options Accordingly: 

  [!img](./imgs/004.png)

  c. Click `Generate Password`

  d. Click `Show Connection Info`

3. Log Into Twitch via the web-app

4. Add a new OBS Client

  a. Using the detail from the OBS Websocket Connection Info Window, copy the host and password over to the web-app form then `Submit`

  b. Click `Connect` next to the new OBS Client Entry (green play button)