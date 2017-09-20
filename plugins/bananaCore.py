from rtmbot import Plugin
import logging
import os


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
        self.op = False

    def get_inv(self):
        if len(self.inventory) == 0:
            return "There are no items in your inventory"
        ret = "Your inventory contains: ```"
        for key, item in self.inventory.items():
            ret += "\n{0}".format(item.desc())
        ret += '```'
        return ret


class BananaPlugin(Plugin):
    def __init__(self, name=None, slack_client=None, plugin_config=None):
        super().__init__(name, slack_client, plugin_config)
        self.users = {}
        self.players = {}
        self.ops = {}

    def process_hello(self, data):
        logging.info("Registering Ops")
        banana_ops = os.getenv('BANANA_OPS')
        if (banana_ops):
            for user_id in banana_ops.split(','):
                self.op(user_id)

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
            user_id = data.get('item_user', None)
            if (user_id and user_id != data['user']):
                player = self.get_player(data['item_user'])
                self.add_banana(player)

    def get_player(self, user_id):
        # Register players we haven't seen yet
        if user_id not in self.players:
            # super hella unsafe
            response = self.slack_client.api_call('im.open', user=user_id)
            channel_response = (response.get('channel', None))
            if (channel_response):
                logging.info("Registering new player: {0}".format(user_id))
                self.players[user_id] = Player(channel_response['id'])
        return self.players.get(user_id, None)

    def process_message(self, data):
        print(data)
        user_id = data.get('user', None)
        if user_id is None:
            logging.info(data)
            return

        # Skip instances where the bot sees itself replying
        if 'reply_to' in data:
            return

        player = self.get_player(user_id)
        if (player.im != data['channel']):
            return

        text = data.get('text', None)
        if (text is None):
            return

        user = self.users.get(user_id, None)
        if user is not None:
            logging.info("{0}: {1}".format(user['profile']['real_name'], data['text']))

        # crappy text processing for now
        if text.startswith('help') or text == 'h':
            self.respond(player.im, "Welcome to a banana filled adventure!")
        elif text.startswith('inv') or text == 'i':
            self.respond(player.im, player.get_inv())
        elif text.startswith('look') or text == 'l':
            self.respond(player.im, "Nothing here but us bananas!")
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
        elif text.startswith('grant'):
            if (player.op):
                self.grant(player, text)
            else:
                self.respond(player.im, 'You do not have permission to use this command')
        elif text.startswith('op'):
            if (player.op):
                tokens = text.split(' ')
                target_id = tokens[1].strip('<@>')
                self.op(target_id)
                self.respond(player.im, "Opped {0}".format(tokens[1]))
            else:
                self.respond(player.im, 'You do not have permission to use this command')
        elif text.startswith('deop'):
            if (player.op):
                tokens = text.split(' ')
                target_id = tokens[1].strip('<@>')
                self.deop(target_id)
                self.respond(player.im, "Deopped {0}".format(tokens[1]))
            else:
                self.respond(player.im, 'You do not have permission to use this command')
        else:
            self.respond(player.im, 'I don\'t understand what you are trying to say.')

    def add_banana(self, player, num=1):
        i = player.inventory.get('banana', Banana(qty=0))
        i.qty += num
        player.inventory['banana'] = i
        if (i.qty <= 0):
            player.inventory.pop('banana')

    def grant(self, player, text):
        tokens = text.split(' ')
        target_id = tokens[1].strip('<@>')
        target_player = self.get_player(target_id)
        if (target_player is None):
            return

        token_qty = tokens[2].lstrip('+-')
        if (not token_qty.isdigit()):
            return

        if ("-" in tokens[2]):
            banana_qty = -int(token_qty)
        else:
            banana_qty = int(token_qty)

        self.add_banana(target_player, banana_qty)

        msg = "Successfully "
        if (banana_qty > 0):
            msg += "added "
        elif (banana_qty < 0):
            msg += "removed "

        msg += str(abs(banana_qty))
        msg += " banana"
        if abs(banana_qty) > 1:
            msg += "s"

        if (banana_qty > 0):
            msg += " to"
        elif (banana_qty < 0):
            msg += " from"

        msg += tokens[1]

        self.respond(player.im, msg)

    def op(self, user_id):
        player = self.get_player(user_id)
        if (player):
            logging.info("Opping: {0}".format(user_id))
            player.op = True
        else:
            logging.info("{0} could not be OP'd".format(user_id))

    def deop(self, user_id):
        player = self.get_player(user_id)
        if (player):
            logging.info("Deopping: {0}".format(user_id))
            player.op = False
        else:
            logging.info("{0} could not be Deop'd".format(user_id))

    def respond(self, room, text):
        self.outputs.append([room, text])
