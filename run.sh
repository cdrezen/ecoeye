source .env

LSBLK_DEV_LINE=$(lsblk --noheadings --raw -o NAME,MOUNTPOINT | grep $DEV_NAME)

if [ -z "$LSBLK_DEV_LINE" ]; then
    echo $DEV_NAME device not found
    exit 1
fi

MOUNTPOINT=$(echo $LSBLK_DEV_LINE | awk '{print $2}')
echo "Mountpoint: $MOUNTPOINT"

if [ -z "$MOUNTPOINT" ]; then
    echo $DEV_NAME not mounted: mounting device...
    MOUNTPOINT=$(udisksctl mount -b /dev/$DEV_NAME | awk '{print $4}')
    if [ -z "$MOUNTPOINT" ]; then
        echo "Mounting failed"
        exit 1
    else
        echo "Mounted at $MOUNTPOINT"
    fi
fi

if ! cp -a src/. $MOUNTPOINT/; then
    echo "Copy failed"
    exit 1
else
    echo "Copy succeeded"
fi

SETTINGS_FILEPATH="$MOUNTPOINT/config/settings.py"
VARNAME="START_DATETIME"
DATE=$(date +'(%4Y,%-m,%-d,%w,%-H,%-M,%-S,0)')

REGEX="s/$VARNAME.*$/$VARNAME=$DATE/g"
echo "Updating settings.py with $VARNAME=$DATE, regex: $REGEX"

sed -i $REGEX $SETTINGS_FILEPATH