#!/usr/bin/env bash

set -x
set -e

PRIMEGEN=$PREFIX/lib/libprimegen.so

if [ -e $PRIMEGEN ];
then
    echo "Assuming $PRIMEGEN is ok, not rebuilding primegen"
    exit 0;
else
    echo "Building primegen"
fi

MY_PREFIX=tmp
rm -rf $MY_PREFIX
echo "Beginning Install"
for f in `ls -d *.tar.bz2 2>/dev/null`; do
    bunzip2 -c $f | tar xf -
done
for f in `ls -d *.tgz *.tar.gz 2>/dev/null`; do
    gunzip -c $f | tar xf -
done
cd primegen-0.97
make primegen.h
# Original provided by Brent Gregersen - unpacks and builds a 
# minimal object set and test program
patch -b -p1 < ../patch.0.97.gregersen
gcc -O2 -Wall -Werror -pedantic -fPIC -c \
    primegen.c \
    primegen_skip.c \
    primegen_next.c \
    primegen_init.c \
    test_primes.c
gcc -O2 -Wall -Werror -pedantic  *.o -o test_primes
echo; echo 'Testing primegen'
./test_primes > gen1000.dat
diff gen1000.dat list1000.dat || (echo 'mismatch!' && exit 1) # desres_die make check failed with CHECK=strict.  Bye.
echo 'OK'
gcc -shared -Wl,-soname,libprimegen.so -o libprimegen.so \
    primegen.o \
    primegen_init.o \
    primegen_next.o \
    primegen_skip.o  

# We don't want to use the program's default install because it
# will install the unpatched header file.  So we install by hand
mkdir -p ${MY_PREFIX}/include \
    ${MY_PREFIX}/lib

install -m 0755 libprimegen.so ${MY_PREFIX}/lib
install primegen.h ${MY_PREFIX}/include
# Restore the unpatched files and build the test binaries
cp primegen.h.orig primegen.h
cp primegen.c.orig primegen.c
echo ${MY_PREFIX} > conf-home
make prog

echo "rsync $MY_PREFIX/ --> $PREFIX"
rsync -av --update $MY_PREFIX/ $PREFIX
