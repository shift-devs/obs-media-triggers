FROM python:latest

ENV OPT_DIR "/opt/obs_media_triggers"

COPY ./src/obs_media_triggers ${OPT_DIR}

WORKDIR ${OPT_DIR}

RUN python -m pip install .

CMD ["obs-media-triggers", "-"]