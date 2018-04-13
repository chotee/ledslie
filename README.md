# Ledslie

A community information display. Ledslie is designed to be open and accessible to all that want to display information 
to a shared space.

* The Project page is https://wiki.techinc.nl/index.php/Ledslie 
* Code is kept at https://github.com/techinc/ledslie


## Components
Ledslie is based around the MQTT broker framework. 

It consists of various processes that do one particular job.

* [Site](ledslie/interface/site.py) is a website based on [Flask](http://flask.pocoo.org/) that users can interact with directly
* [Serializer](ledslie/processors/serializer.py) receives raw frame-types and sends them to the display.
* [Sequencer](ledslie/processors/scheduler.py) maintains a queue of frames and sends the next to Serializer.
* [Typesetter](ledslie/processors/typesetter.py) takes a text and generates the frame to be displayed. 

Ledslie has various dependencies on other projects.
* [Mosquitto](http://mosquitto.org/) is the MQTT broker. 
* [Nginx](http://nginx.org/) does the webserver work.
* [Ansible](https://www.ansible.com/) does the Deployment from the [deploy](deploy/) directory. 
* [Pillow](https://python-pillow.org/) is used for image processing.

## Deploying
To test, use [vagrant](https://www.vagrantup.com/) to run a VM that has all the system running (except, likely, the display)

`$ cd deploy; vagrant up`

To update the vagrant once installed

`$ cd deploy; vagrant provision`

To deploy to the machine (only works when in the space)

`$ cd deploy; ansible-playbook -i techinc ledslie-install.yml`

For a faster deploy when only existing programs are being updated there's

`--tags update`


## Testing

There are unittests in [tests](ledslie/tests). The test runner is [pytest](https://docs.pytest.org/en/latest/)
