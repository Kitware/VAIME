#! /bin/bash

# Fletch, VIAME, CMAKE system deps
wget https://cmake.org/files/v3.23/cmake-3.23.1.tar.gz
tar zxvf cmake-3.*
cd cmake-3.23.1
./bootstrap --prefix=/usr/local --system-curl
make -j$(nproc)
make install
cd /
rm -rf cmake-3.23.1.tar.gz cmake-3.23.1
