#!/bin/bash
echo "Building cortex-client from master"

set -e

cd `dirname $0`
cd ..

git checkout master
git pull

NAME="cortex-client"
VERSION=`git describe --long --match "release*dev" | awk -F"-" '{print $2}'`
RELEASE=`git describe --long --match "release*dev" | awk -F"-" '{print $3}'`

./scripts/build-rpm.sh
deploy-trunk /var/lib/mock/epel-6-i386/result/${NAME}-${VERSION}-${RELEASE}.noarch.rpm
deploy-trunk /var/lib/mock/fedora-15-i386/result/${NAME}-${VERSION}-${RELEASE}.noarch.rpm
deploy-trunk /var/lib/mock/fedora-16-i386/result/${NAME}-${VERSION}-${RELEASE}.noarch.rpm
updaterepo
