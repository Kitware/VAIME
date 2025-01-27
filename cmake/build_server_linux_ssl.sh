#! /bin/bash

# Fletch, VIAME, CMAKE system deps
wget https://github.com/openssl/openssl/releases/download/openssl-3.4.0/openssl-3.4.0.tar.gz
tar -xzvf openssl-3.4.0.tar.gz
cd openssl-3.4.0
./config --prefix=/usr --openssldir=/etc/ssl --libdir=lib no-shared zlib-dynamic
make -j$(nproc)
make install
cd /
rm -rf openssl-3.4.0.tar.gz openssl-3.4.0
