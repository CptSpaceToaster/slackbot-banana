from rtmbot import Plugin
import dice


class DicePlugin(Plugin):
    def __init__(self, name=None, slack_client=None, plugin_config=None):
        super().__init__(name, slack_client, plugin_config)

    def process_message(self, data):
        # Skip instances where the bot sees itself replying
        if 'reply_to' in data:
            return

        text = data.get('text', None)
        if (text is None):
            return

        if (text.startswith('!')):
            text = text[1:].lower()
            if (text.startswith('roll ')):
                text = text.replace('roll ', '')
                try:
                    outcome = dice.roll(text)
                    self.respond(data['channel'], str(outcome))
                except:
                    self.respond(data['channel'], "I'm not able to roll that sort of dice")

    def respond(self, room, text):
        self.outputs.append([room, text])
