from rtree import index
from os import environ as env
import redis

class IndexFactory():
    def __init__(self):
        self.idx = index.Index()

    def add_box_to_index(self, subscription_id, view):
        self.idx.insert(id=subscription_id, bounds=(view[0], view[1], view[2], view[3]))

    def get_current_subscriptions(self):
        r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
        all_subscriptions = r.keys(pattern='sub-*')

        subscription_id = all_subscriptions.split('-')[1]

        for subscription in all_subscriptions:
            subscription_view = r.get(subscription)
            view = [float(i) for i in subscription_view.split(",")]
            self.add_box_to_index(subscription_id = subscription_id, view = view)

        return self.idx
    