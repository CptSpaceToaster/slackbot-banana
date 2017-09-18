from rtmbot import Plugin
import logging
import sys
import dice


class Item():
    def __init__(self, qty=0):
        self.qty = qty

    def desc(self):
        pass


class Banana(Item):
    def desc(self):
        if (self.qty > 1):
            return 'A bunch of wonderful bananas x{0}'.format(self.qty)
        else:
            return 'A wonderful banana'


class Player():
    def __init__(self, im):
        self.im = im
        self.inventory = {}

    def get_inv(self):
        if len(self.inventory) == 0:
            return "There are no items in your inventory"
        ret = "Your inventory contains:"
        for key, item in self.inventory.items():
            ret += "\n{0}".format(item.desc())
        return ret


class BananaPlugin(Plugin):
    def __init__(self, name=None, slack_client=None, plugin_config=None):
        super().__init__(name, slack_client, plugin_config)
        self.users = {}
        self.players = {}

    def process_hello(self, data):
        logging.info("Hello world")
        # self.register_users()
        logging.info("Done with initialization")

    def register_users(self):
        logging.info("Registering users")
        # this is hella unsafe
        for user in self.slack_client.api_call('users.list')['members']:
            self.users[user['id']] = user
        logging.info("Registered {0} users".format(len(self.users)))

    def process_reaction_added(self, data):
        if (data['reaction'] == 'banana'):
            if (data['user'] != data['item_user']):
                player = self.get_player(data['user'])
                self.add_banana(player)

    def get_player(self, user_id):
        # Register players we haven't seen yet
        if user_id not in self.players:
            logging.info("Registering new player: {0}".format(user_id))
            # super hella unsafe
            response = self.slack_client.api_call('im.open', user=user_id)
            self.players[user_id] = Player(response['channel']['id'])
        return self.players[user_id]

    def process_message(self, data):
        user_id = data.get('user', None)
        if user_id is None:
            logging.info(data)
            return

        # Skip instances where the bot sees itself replying
        if 'reply_to' in data:
            return

        player = self.get_player(data['user'])
        text = data['text']
        user = self.users.get(user_id, None)
        if user is not None:
            logging.info("{0}: {1}".format(user['profile']['real_name'], data['text']))

        # crappy text processing for now
        text = text.lower()
        if text.startswith('!'):
            text = text[1:]
            if text.startswith('help') or text == 'h':
                self.respond(player.im, "Welcome to a banana filled adventure!\nTry to `use`, `move`, and `look` your way through this marvelous journey, and don't be afraid to ask for `help` or check your `inventory`!")
            elif text.startswith('roll '):
                text = text.replace('roll ', '')
                try:
                    outcome = dice.roll(text)
                    self.respond(data['channel'], str(outcome))
                except:
                    self.respond(data['channel'], "I'm not able to roll that sort of dice")
            elif text.startswith('inv') or text == 'i':
                self.respond(player.im, player.get_inv())
            elif text.startswith('look') or text == 'l':
                self.respond(player.im, "Nothing here but us bananas!")
            elif text.startswith('get banana'):
                self.add_banana(player)
                self.respond(player.im, "You picked up a banana!")
            elif text.startswith('use banana'):
                i = player.inventory.get('banana', Banana(qty=0))
                if i.qty == 1:
                    player.inventory.pop('banana')
                    self.respond(player.im, 'You\'ve used all of your bananas!')
                elif i.qty > 0:
                    i.qty -= 1
                    player.inventory['banana'] = i
                    self.respond(player.im, 'You used a banana!')
                else:
                    self.respond(player.im, 'You do not have any bananas to use right now')
            else:
                self.respond(player.im, 'I don\'t understand what you are trying to say.')

    def add_banana(self, player):
        i = player.inventory.get('banana', Banana(qty=0))
        i.qty += 1
        player.inventory['banana'] = i

    def respond(self, room, text):
        self.outputs.append([room, text])
