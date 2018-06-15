#!/usr/bin/python

import threading
import logging
import etcd
from urllib3.exceptions import ReadTimeoutError


# Basic logging capability
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class Subscriber():
    """A subscriber object does not know nothing about the publisher,
    but is interested in doing things when an etcd key will change
    """
    def __init__(self, name):
        """Initialization
        """
        self.name = name

    def do_things(self, key, value):
        """Things to do when a etcd key will change
        @key: Key where a change happened
        @value: Current value for this key
        """
        print("Subscriber: %s: Changes in '%s', the value has "
              "changed to '%s'" % (self.name, key, value))

class Watcher():
    """Watcher component

    This component allows clients(subscribers) to subscribe to the change
     in etcd keys.
    Programs making changes in the etcd keys are the publishers.
    Publishers are not aware about how many subscribers are interested in
    certain key.

    Watcher has a dict of keys each one with a dict with the subscribers
    interested in the key.
    The value of each item in the dict of subscribers is the callback
    function to execute when the etcd key changes
    """

    def __init__(self):
        """Initialization
        """
        self.client = etcd.Client()
        self.keys = {}

    def get_subscribers(self, key):
        """Provides a list of subscriber to one key
        @key: the key where we search subscribers
        """
        if key in self.keys.keys():
            return self.keys[key]
        else:
            return []

    def register(self, key, who, what):
        """Register a subscriber to one key
        @key: The key to subscribe
        @who: A subscriber object
        @what: The callback function to execute when the key will change
        """

        # Add the key
        if key not in self.keys.keys():
            self.add_key(key)

        # Store the callback function
        self.keys[key][who.name] = getattr(who, what)
        logger.info("'%s' subscribed to key '%s' with callback '%s'",
                    who, key, what)


    def unregister(self, key, who):
        """To use when a subscriber is not interested anymore in a key
        @key: The key to unsubscribe
        @who: The subscriber
        """

        # Remove the subscriber from the list of this key
        if who.name in self.keys[key]:
            del self.keys[key][who.name]
            logger.info("'%s' unsubscribed to key '%s'", who, key)

        # If nobody interested in this key, avoid to have a thread
        # watching the key
        if not self.keys[key].keys():
            del self.keys[key]
            logger.info("Key '%s' without subscribers removed", key)



    def add_key(self, key):
        """Start to watch one key. No subscribers needed.
        @key: etcd key to watch
        """
        # Only new keys are added
        if key in self.keys.keys():
            return

        # Add the key to the keys dict
        self.keys[key] = dict()

        # Start the thread to watch this key.
        try:
            threading.Thread(target=self.watch, args=(key,)).start()
            logger.info("Key '%s' added to watcher", key)
        except Exception as ex:
            logger.error("unexpected error adding key '%s' to watcher: %s", key, ex)

    def remove_key(self, key):
        """Remove a key from being watched. This will affect also subscribers
        because if the key change they won't be warned
        @key: etcd key that we want do not watch anymore
        """
        # Removing the key from the dict the watch thread will die
        # in the next timeout
        if key in self.keys.keys():
            del self.keys[key]
            logger.info("Key '%s' removed from watcher", key)

    def dispatch(self, key, value):
        """Warn all the subscribers about an etcd key changed.
        The callback function of each subscriber will be called
        @key: etcd key changed
        @value: current value in the key
        """

        # Loop over the subscribers doing callbacks
        for subscriber, callback in self.keys[key].items():
            try:
                callback(key, value)
                logger.info("calling back '%s:%s' for change in '%s' with value '%s'",
                            subscriber, callback, key, value)

            # Who knows what extrange things can try to do the subscriber
            except Exception as ex:
                logger.error("%s: key(%s).Unexpected error in callback to '%s':%s",
                             subscriber, key, callback, ex)


    def watch(self, key):
        """Watch a key while somebody interested in it
        @key: etcd key to watch
        """

        while True:
            try:
                # We watch only keys with interested subscribers
                if key in self.keys.keys():
                    result = self.client.watch(key)
                    self.dispatch(key, result.value)
                # If nobody interested in this key, we do not watch the key
                else:
                    break

            # An etcd default timeout will arise while watching a key
            except ReadTimeoutError:
                # Doing nothing we relaunch the watch of this key
                pass
            # Other horrible an unexpected things can happen,
            # but we will continue trying to watch this key
            except Exception as ex:
                logger.error("Watching key: %s. Unexpected error: %s", key, ex)
