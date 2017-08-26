This program was written with the intent to fix damages done by incomplete cryptolocker decryptions.

A friend of the programmer's had his company hit by the virus and, even though they paid the ransom
some of their files were missed. This was because the drive letter mapping had changed between when
the files were encrypted and when they were decrypted. The programmer studied the virus extensively
within the bounds of his capability and wrote this program. I, the programmer, would like to remain
relatively anonymous so as to not become a potential target for the cryptolocker authors. Those bastards

There is no warrenty guranteed or implied through the use of this program. This program is written to NOT
overwrite the files it reads from, but just to be sure make sure that any files placed in the "Encrypted Files"
folder aren't your only copy of them in case something goes wrong

Again, there is no warrenty guranteed or implied and the use of this program is entirely of your own volition.
Using this program constitutes your agreement to not hold the author liable for any damages caused by it.

If you need reassurance of this program's function ask someone you know who programs to look over
it's code and verify it is not malicious.

Your friend, Mo


This program requires python to run. I'm not sure which version is required, but it was programmed and
has shown to work with python 3.3 so that should be the one to use.

Pycrypto is required for running this script. Download pycrypto installers downloaded from here:

https://github.com/appurify/appurify-python/tree/master/pycrypto



Update V1.1.1: Program is now able to use registry keys as the RSA key instead of only being able to use .bin
binary blobs. To do this export the private key from the registry as a .reg file and place it in the same
directory as Crypto-Unlocker-Run.py. You don't need to remove all the other entires from the .reg file, just
make sure the private key entry is in there.

Update V1.1.5: Added two checks to make sure the file being decrypted is actually encrypted.
If the file is not you will be alerted and the file will be skipped. There are 14 bytes of data that must
match if a file is to be considered encrypted to prevent accidentally decrypting something into garbage.