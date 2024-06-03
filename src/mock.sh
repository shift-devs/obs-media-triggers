#!/usr/bin/env bash

# Start Mock API
#twitch mock-api start &

# Start Twitch Bot
python \
	-m obs_media_triggers \
		-vv \
		--obs-ws-passwd $OBS_WS_PASSWD \
		--twitch-app-id $MOCK_OMT_CLIENT_ID \
		--twitch-app-secret $MOCK_OMT_CLIENT_SECRET \
		--twitch-app-url $OMT_APP_URL
