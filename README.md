# OBS Media Triggers
[![deploy](https://github.com/shift-devs/obs-media-triggers/actions/workflows/actions.yml/badge.svg)](https://github.com/shift-devs/obs-media-triggers/actions/workflows/actions.yml)

An alternative to StreamLabs. Web Application for controlling local media in OBS based on Twitch events.

&nbsp;

***

## Web Application Quick Start

See the [Usage](./USAGE.md) page for in-depth instructions for the web-app itself.

&nbsp;

***

## Development and Contribution

### Quick Start

&nbsp;

#### Pre Requisites

* `python >= 3.8`
* `python-pip >= 24.0`
* `docker >= 26.1.4`
* `docker-compose >= 2.27.1`

&nbsp;

#### Install Dependencies

* `pip install -e .[testing]`

&nbsp;

#### Start Web App

##### As Local Python Module

* `python -m src/obs_media_triggers`

##### As Docker Container

* `python -m build --wheel`
* `mv dist/*.whl docker`
* `docker-compose --project-directory docker build`
* `docker-compose --project-directory docker up -d`

##### With Docker-Compose

```docker
services:
  obs-media-triggers:
    build: .
    image: obs-media-triggers
    container_name: obs-media-triggers
    ports:
      - 7064:7064
    volumes:
      - omt_data_dir:/srv/omt
    environment:
      - OMT_APP_SECRET=$OMT_APP_SECRET

volumes:
  omt_data_dir:
```

The web-app should be available at: http://localhost:7064

&nbsp;

#### Get App Command Line Args

* `python -m src/obs_media_triggers --help`

#### Run Unit Tests

* `python -m unittest test`