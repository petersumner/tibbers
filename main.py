import os
import sys
import requests
import json
import re
import discord
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from riotwatcher import LolWatcher

from data import LANES, PATCH, RIOTKEY

class Driver:
    def __init__(self, champion, region, lane, queue):
        self.champion = champion
        self.region = region
        self.lane = lane
        self.queue = queue
        self.url = "https://u.gg/lol/champions/"+self.champ+"/build?queueType="+self.queue
        if self.lane:
            self.url += '&role=' + lane

    def config(self):
        self.watcher = LolWatcher(RIOTKEY)
        if not self.is_champ():
            print('in class')
            return {}

        options = Options()
        options.headless = True
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        driver_path = "chromedriver.exe"
        ser = Service(driver_path)
        self.driver = webdriver.Chrome(options=options, service=ser)
        self.driver.get(self.url)

    def get_runes(self):
        primary_element = self.driver.find_element(By.XPATH, "//div[@class='rune-tree_v2 primary-tree']//div[@class='perk-style-title']")
        secondary_element = self.driver.find_element(By.XPATH, "//div[@class='secondary-tree']//div[@class='perk-style-title']")
        
        keystone_element = primary_element.find_element(By.XPATH, "//div[@class='perks']//div[@class='perk keystone perk-active']/img")
        keystone = keystone_element.get_attribute('alt').replace("The Keystone ", "")

        perk_elements = primary_element.find_elements(By.XPATH, "//div[@class='perk perk-active']/img")
        perks = []
        for perk in perk_elements:
            p = perk.get_attribute("alt").replace("The Rune ", "")
            if p not in perks:
                perks.append(p)

        shard_elements = primary_element.find_elements(By.XPATH, "//div[@class='champion-profile-page']//div[@class='shard shard-active']/img")
        shards = []
        for shard in shard_elements:
            s = shard.get_attribute("alt").replace("The ", "").replace(" Shard", "")
            shards.append(s)

        runes = {
            'Primary': primary_element.text,
            'Secondary': secondary_element.text,
            'Keystone': keystone,
            'PrimaryPerks': perks[:3],
            'SecondaryPerks': perks[3:],
            'Shards': shards[:3]
        }
        
        self.driver.quit()
        return runes

    def is_champ(self):
        versions = self.watcher.data_dragon.versions_for_region(self.region)
        champions_versions = versions['n']['champion']
        current_champion_list = self.watcher.dta_dragon.champions(champions_versions)
        if self.champ.lower().capitalize() not in current_champion_list['data']:
            return False

    def get_lane(self):
        return ""


def scrape(champ, region, lane):
    lol_watcher = LolWatcher(RIOTKEY)
    versions = lol_watcher.data_dragon.versions_for_region(region)
    champions_version = versions['n']['champion']
    current_champ_list = lol_watcher.data_dragon.champions(champions_version)

    if champ not in current_champ_list['data']:
        print("not in class")
        return {}

    options = Options()
    options.headless = True
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    driver_path = "chromedriver.exe"
    ser = Service(driver_path)
    driver = webdriver.Chrome(options=options, service=ser)

    url = "https://u.gg/lol/champions/"+champ+"/build?queueType=normal_draft_5x5"
    if lane:
        url += '&role=' + lane

    driver.get(url)
    runes = get_runes(driver, champ)
    driver.quit()
    return runes

def get_runes(driver, champ):
    primary_element = driver.find_element(By.XPATH, "//div[@class='rune-tree_v2 primary-tree']//div[@class='perk-style-title']")
    secondary_element = driver.find_element(By.XPATH, "//div[@class='secondary-tree']//div[@class='perk-style-title']")
    
    keystone_element = primary_element.find_element(By.XPATH, "//div[@class='perks']//div[@class='perk keystone perk-active']/img")
    keystone = keystone_element.get_attribute('alt').replace("The Keystone ", "")

    perk_elements = primary_element.find_elements(By.XPATH, "//div[@class='perk perk-active']/img")
    perks = []
    for perk in perk_elements:
        p = perk.get_attribute("alt").replace("The Rune ", "")
        if p not in perks:
            perks.append(p)

    shard_elements = primary_element.find_elements(By.XPATH, "//div[@class='champion-profile-page']//div[@class='shard shard-active']/img")
    shards = []
    for shard in shard_elements:
        s = shard.get_attribute("alt").replace("The ", "").replace(" Shard", "")
        shards.append(s)

    runes = {
        'Primary': primary_element.text,
        'Secondary': secondary_element.text,
        'Keystone': keystone,
        'PrimaryPerks': perks[:3],
        'SecondaryPerks': perks[3:],
        'Shards': shards[:3]
    }

    return runes

def get_region(region):
    return 'na1'

def get_lane(args):
    for arg in args:
        for lane in LANES:
            if arg.lower() in LANES[lane]:
                return lane
    return ''

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
                await message.channel.send('help coming soon <3')
            elif args == []:
                await message.channel.send('whoops you forgot to add a command')
            elif 'runes' in args:
                args.remove('runes')
                lane = get_lane(args)
                if lane != '':
                    args.remove(lane)
                for i in range(len(args)):
                    args[i] = args[i].lower().capitalize()
                runes = scrape(("".join(args)), 'na1', lane)
                if runes == {}:
                    await message.channel.send("whoops that champion doesn't exist")
                else:
                    embed = discord.Embed(title=(" ".join(args)) + ' Runes', color=0x2ecfe8)
                    embed.add_field(name='**__'+runes['Primary']+'__**', value='__'+runes['Keystone']+'__\n'+'\n'.join(runes['PrimaryPerks']), inline=False)
                    embed.add_field(name='**__'+runes['Secondary']+'__**', value='\n'.join(runes['SecondaryPerks']), inline=False)
                    embed.add_field(name="Shards", value='\n'.join(runes['Shards']), inline=False)
                    embed.set_thumbnail(url="https://static.u.gg/assets/lol/riot_static/12.3.1/img/champion/"+("".join(args))+".png")
                    await message.channel.send(embed=embed)
            else:
                await message.channel.send('command not recognized')

    load_dotenv('.env')
    client.run(os.getenv('TOKEN'))