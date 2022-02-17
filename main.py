import discord
import os
import requests
import random

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from keep_alive import keep_alive
from data import LANES, PATCH, COLOR, QUEUES, FRIENDLY, QUOTES

STORY_LINKS = []

class Scraper:
    def __init__(self, champion, region, lane, queue, opponent):
        self.champion = champion.replace("'", "")
        self.region = region
        self.lane = lane
        self.queue = queue
        self.opponent = opponent
        self.set_url()
        self.runes = {}

    def set_url(self):
        self.url = "https://u.gg/lol/champions/"+self.champion+"/build"
        if self.queue == 'normal_draft_5x5' or self.queue == 'normal_blind_5x5':
          self.url += "?queueType="+self.queue
        else:
          self.url += "?rank="+self.queue
        if self.lane:
            self.url += '&role=' + self.lane

    def get_html(self):
        page = requests.get(self.url)
        self.soup = BeautifulSoup(page.content, "html.parser")

    def get_runes(self):
        # Rune Trees
        trees = self.soup.find_all(class_="perk-style-title")
        self.runes.update({'Primary': trees[0].text})
        self.runes.update({'Secondary': trees[1].text})

        # Keystone Rune
        keystone = self.soup.find(class_="perk keystone perk-active")
        keystone = keystone.find("img").extract()['alt'].replace("The Keystone ", "")
        self.runes.update({'Keystone': keystone})

        # Other Runes
        perks = self.soup.find_all("div", class_="perk perk-active")
        for perk in perks[:5]:
            perks[perks.index(perk)] = (perk.find("img").extract()['alt'].replace("The Rune ", ""))
        self.runes.update({'PrimaryPerks': perks[:3]})
        self.runes.update({'SecondaryPerks': perks[3:5]})

        # Shards
        shards = self.soup.find_all("div", class_="shard shard-active")
        for shard in shards[:3]:
            s = (shard.find("img").extract()['alt'].replace("The ", "").replace(" Shard", ""))
            if s == "Scaling CDR":
                shards[shards.index(shard)] = "Ability Haste"
            elif s == "Scaling Bonus Health":
                shards[shards.index(shard)] = "Health"
            else:
                shards[shards.index(shard)] = s
        self.runes.update({'Shards': shards[:3]})

def get_region(region):
    return 'na1'

def get_data(args, type):
    for arg in args:
        for x in type:
            if arg.lower() in type[x]:
                return [x, arg.lower()]
    return []

def get_lane(args):
    for arg in args:
        for lane in LANES:
            if arg.lower() in LANES[lane]:
                return [lane, arg.lower()]
    return []

if __name__ == "__main__":
    client = discord.Client()

    @client.event
    async def on_ready():
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='type "!t help"'))
        print('We have logged in as {0.user}'.format(client))

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!t'):
            args = message.content.lower().split(' ')
            args.remove('!t')

            if 'help' in args:
                embed = discord.Embed(title="Tibbers Help", description="For all commands: [*mandatory* field], (*optional* field)", color=COLOR)
                embed.add_field(name="Command: runes", value="```!t runes [champion] (lane) (queue_type)```", inline=False)
                embed.add_field(name="Can I see my field options?", value='```!t [field_name]?```', inline=False)
                embed.add_field(name="Still stuck?", value="If Tibbers isn't responding ask @oatmeal if he's asleep", inline=False)
                await message.channel.send(embed=embed)

            elif args == []:
                await message.channel.send('whoops you forgot to add a command')

            elif 'queue_type?' in args:
                embed = discord.Embed(title="Tibbers approved queue types", description=(", ".join(FRIENDLY['queues'])), color=COLOR)
                await message.channel.send(embed=embed)

            elif 'lane?' in args or 'lanes?' in args:
                embed = discord.Embed(title="Tibbers approved lanes", description=(", ".join(FRIENDLY['lanes'])+"\n*You can also shorten to the first letter of the lane*"), color=COLOR)
                await message.channel.send(embed=embed)

            elif 'champion?' in args:
                embed = discord.Embed(title="Do you really need help with this one?", description="Any champ name, just spell it right", color=COLOR)
                await message.channel.send(embed=embed)

            elif 'field_name?' in args:
                embed = discord.Embed(title="Grr", description="queue_type, lane", color=COLOR)
                await message.channel.send(embed=embed)
    
            elif 'runes' in args:
                args.remove('runes')
                lane = get_data(args, LANES)
                if lane != []:
                    args.remove(lane[1])
                    lane = lane[0]
                else: 
                    lane = ''

                queue = get_data(args, QUEUES)
                if queue != []:
                    args.remove(queue[1])
                    queue = queue[0]
                else:
                    queue = 'normal_draft_5x5'
              
                for i in range(len(args)):
                    args[i] = args[i].lower().capitalize()
                 
                scraper = Scraper(("".join(args)), 'na1', lane, queue, '')
              
                scraper.get_html()
                scraper.get_runes()
              
                if scraper.runes == {}:
                    await message.channel.send("whoops that champion doesn't exist")
                else:
                    if scraper.champion in QUOTES:
                      embed = discord.Embed(title=(" ".join(args)) + ' Runes', description="*"+random.choice(QUOTES[scraper.champion])+"*", color=COLOR)
                    else:
                      embed = discord.Embed(title=(" ".join(args)) + ' Runes', color=COLOR)
                    embed.add_field(name='**__'+scraper.runes['Primary']+'__**', value='__'+scraper.runes['Keystone']+'__\n'+'\n'.join(scraper.runes['PrimaryPerks']), inline=False)
                    embed.add_field(name='**__'+scraper.runes['Secondary']+'__**', value='\n'.join(scraper.runes['SecondaryPerks']), inline=False)
                    embed.add_field(name="Shards", value='\n'.join(scraper.runes['Shards']), inline=False)
                    embed.set_thumbnail(url="https://static.u.gg/assets/lol/riot_static/"+PATCH+".1/img/champion/"+("".join(args)).replace("'", "")+".png")
                    await message.channel.send(embed=embed)
                    print('Fetched runes for '+scraper.champion)
            else:
                await message.channel.send('command not recognized')
              
    keep_alive()
    load_dotenv('.env')
    client.run(os.getenv('TOKEN'))