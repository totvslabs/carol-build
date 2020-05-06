#!/bin/sh -l

exec python /build_image.py --gittoken $1 --tenant $2 --org $3 --appname $4 --connectorid $5 --apikey $6 --manifestpath $7