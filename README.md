# etcd_watcher

A basic Publisher/Subscriptor pattern implementation using etcd clients as publishers. The publisher is any kind of client able to write keys in the etcd database.
Subscriptors, should use the api provided by the watcher object in order to be warned about changes in the keys which are interesting for the subscriber.  


## Example of use:
```python
from watcher import Subscriber, Watcher

# Create a watcher
the_watcher = Watcher()

# Create a few subscribers
luis = Subscriber('Luis')
antonio = Subscriber('Antonio')
juan = Subscriber('Juan')

# Luis is interested in 'nokia' and 'redhat' news
the_watcher.register("nokia", luis, 'do_things')
the_watcher.register("redhat", luis, 'do_things')

# Antonio is interested in 'google' news
the_watcher.register("google", antonio, 'do_things')

# Juan is interested in 'redhat' and 'nokia' news
the_watcher.register("redhat", juan, 'do_things')
the_watcher.register("nokia", juan, 'do_things')

# Who is subscribed to 'nokia' news?
the_watcher.get_subscribers('nokia')

# Luis is not interested anymore in 'nokia' news
the_watcher.unregister('nokia',luis)

# Who is subcribed now to 'nokia' news?
the_watcher.get_subscribers('nokia')

# Possibly we will get people interested in "amazon" news
the_watcher.add_key('amazon')

# Juan is interested in 'amazon' news
the_watcher.register("amazon", juan, 'do_things')

# What people are interested in 'amazon'
the_watcher.get_subscribers('amazon')
```

## Changes in keys can be produced by any kind of client supported by etcd database.

for example:

curl http://localhost:2379/v2/keys/google -XPUT -d value="google news 1"

curl http://localhost:2379/v2/keys/google -XPUT -d value="google news 2"

