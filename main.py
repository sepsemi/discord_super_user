import os
import json
import argparse
import requests
from datetime import datetime

class DiscordRelationship:
    __slots__= ('id', 'type', 'nickname', 'username', 'discriminator', 'avatar', 'flags')

    def __init__(self, data):
        self.id = int(data['id'])
        self.type = int(data['type'])
        self.nickname = data['nickname']
        self.username = data['user']['username']
        self.discriminator = data['user']['discriminator']
        self.avatar = data['user']['avatar']
        self.flags = int(data['user']['public_flags'])

    @property
    def name(self):
        return "{}#{}".format(self.username, self.discriminator)

class DiscordRequests:
    API_VERSION = 9
    URI = 'https://discord.com/api/v{}'.format(API_VERSION)
    
    def __init__(self, token):
        self.token = token
        self._session = requests.Session()
        self._guilds = set()
        self._relationships = set()

        # Set the base header this is used everywhere 'application/json' is not.
        self.headers = {
            'authorization': self.token,
            # Lets just set a generic useragent
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36'
        }

    def _get_relationships(self):
        headers = self.headers.copy()
        headers['content-type'] = 'application/json'

        url = 'https://discord.com/api/v9/users/@me/relationships'
        resp = self._session.get(headers=self.headers,url=url)
        
        # Check before we do anything
        if resp.status_code == 200:
            for data in resp.json():
                # append relationstips to the set
                self._relationships.add(DiscordRelationship(data))

    def _get_guilds(self):
        pass

    def send_friend_request(self, user_id):
        headers = self.headers.copy()
        headers['content-type'] = 'application/json'

        url = self.URI + '/users/@me/relationships/{}'.format(user_id)
        self._session.put(headers=headers, url=url, json={})

    @property
    def relationships(self):
        # Fetch the relationships
        self._get_relationships()
        return self._relationships


class DiscordSuperuser:
    def __init__(self, requester, description):
        self._parser = argparse.ArgumentParser(requester, description)
        self._parser.add_argument('--backup', metavar='filename.json', type=str, help='Backup client\'s relationships into a json formated file')
        self._parser.add_argument('--import', metavar='filename.json', type=str, dest='import_from_backup', help='import client\'s relationships from a file by sending friend requests')
        self._parser.add_argument('--mute-guilds', action='store_true', help='Mutes all guilds client belongs to')
        self._parser.add_argument('--list-relationships', action='store_true', help='Lists client\'s relationships')

        # Compile all the args into a Namespace
        self._arguments = self._parser.parse_args()
        print(self._arguments)
        self._requester = requester

    def backup_relationships(self, path):
        if os.path.exists(path):
            # We should never overwrite a file because the user may accidentally overwirte a backup
            raise FileExistsError('The backup file ({}) already exists delete it before continuing'.format(path))

        # Write relationships to specified path in json format
        serialized_relationships = []
        with open(path, 'w') as fp:
            for relationship in self._requester.relationships:
                serialized_relationships.append({
                    'id': relationship.id,
                    'type': relationship.type,
                    'fullname': relationship.name
                })

            # write the list of serialized relationships
            fp.write(json.dumps(serialized_relationships, ensure_ascii=False, indent=4))

            print('[{}][backup_relationships] sucessfully backed up ({}) relationships)'.format(datetime.now(), len(serialized_relationships)))
    
    def import_from_backup(self, path):
        # Check if the file exists
        if not os.path.exists(path):
            raise FileNotFoundError('The backup file ({}) to import from was not found'.format(path))
        
        relationships = []
        with open(path, 'r') as fp:
            json_data = json.load(fp)

            for relationship in json_data:
                # This is unsafe this assumes no one is added and will likely trigger a ban.
                print('[{}][import_from_backup] sending friend request to user known as ({}, {})'.format(
                    datetime.now(), relationship['id'], relationship['fullname'])
                )
                self._requester.send_friend_request(relationship['id'])
        
    def mute_guilds(self):
        raise NotImplementedError('mute_guilds is not availible in this version yet')
    
    def list_relationships(self):
        for relationship in self._requester.relationships:
            print("{}, {}".format(relationship.id, relationship.name)) 

    def run(self):
        # run the base magic here
        if self._arguments.backup:

          self.backup_relationships(self._arguments.backup)
        
        if self._arguments.import_from_backup:
            self.import_from_backup(self._arguments.import_from_backup)

        if self._arguments.mute_guilds:
            self.mute_guilds()

        if self._arguments.list_relationships:
            self.list_relationships()


token = os.environ.get('TOKEN')
if not token:
    # TOKEN is not set we have no reason to run at all
    raise KeyError('environment variable TOKEN is not set')

requester = DiscordRequests(token)
super_user = DiscordSuperuser(requester, "Discord superuser commands and tools")
super_user.run()
