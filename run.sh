MNTPT=/media/user/79BB-BFA7

if ! mount | grep $MNTPT > /dev/null; then
    echo $MNTPT not mounted
    exit 1
fi

if ! cp -a src/. $MNTPT/; then
    echo "Copy failed"
    exit 1
else
    echo "Copy succeeded"
fi