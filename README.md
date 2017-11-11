Ledslie
-------

Content and control of a community led-display

The code behind the https://wiki.techinc.nl/index.php/Ledslie
 
Testing 
-------
To test, use vagrant.

$ cd deploy; vagrant up

To update the vagrant once installed

$ cd deploy; vagrant provision

To deploy to the machine (only works when in the space)

$ cd deploy; ansible-playbook -i techinc ledslie-install.yml 
