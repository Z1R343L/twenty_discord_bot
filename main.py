import logging
from os import getenv, name
from urllib.parse import urlencode

import disnake
import uvloop
from aiohttp import ClientSession
from disnake.ext import commands
from disnake.ui import Button

uvloop.install()
logging.basicConfig(level=logging.INFO)

baseurl = "http://twenty_api:8000/twenty/"

btn_rows = [["exit", "up", "none_0", "name"], ["left", "down", "right", "score"]]


emojis = {
    "none": "<:none:855704123570520094>",
    "left": "<:left:904174939773497354>",
    "right": "<:right:904175010816622642>",
    "up": "<:upup:904175085206769694>",
    "down": "<:down:904175212692647987>",
    "exit": "<:exit:904182464346488852>",
}


async def fetch_endpoint(url: str, param: dict = {}) -> dict:
    param['agent'] = 'discord'
    async with ClientSession() as session:
        async with session.get(url + urlencode(param)) as response:
            return await response.json()


async def play_view(possible_moves: dict, score: int, name: str) -> disnake.ui.View:
    view = disnake.ui.View()
    for row_index in range(len(btn_rows)):
        row = btn_rows[row_index]
        for btn in row:
            if btn.startswith("none_"):
                view.add_item(disnake.ui.Button(
                    emoji=emojis["none"], custom_id=btn, disabled=True, row=row_index
                ))
            elif btn == "exit":
                view.add_item(
                    disnake.ui.Button(
                        style=disnake.ButtonStyle.red, emoji=emojis[btn], custom_id=btn, disabled=False, row=row_index
                ))
            elif btn =='score':
                view.add_item(disnake.ui.Button(
                    label=str(score), custom_id=btn, disabled=True, row=row_index
                ))
            elif btn =='name':
                view.add_item(disnake.ui.Button(
                    label=name, custom_id=btn, disabled=True, row=row_index
                ))
            else:
                if possible_moves[btn]:
                    btn_move_disbaled = False
                else:
                    btn_move_disbaled = True
                view.add_item(
                        disnake.ui.Button(
                            emoji=emojis[btn], custom_id=btn, disabled=btn_move_disbaled, row=row_index
                    ))
    return view


class continue_select(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(
                label="yes", description="yes => continue running game!"
            ),
            disnake.SelectOption(label="no", description="no => start new game!"),
        ]
        super().__init__(
            placeholder="found running game, continue?",
            custom_id="continue",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        match self.values[0]:
            case 'no':
                url = f"{baseurl}new_game?"
            case 'yes':
                url = f"{baseurl}data?"
        data = await fetch_endpoint(url=url, param={"id": inter.author.id, "name": inter.author.name})
        # emb = inter.message.embeds[0]
        # emb.description = f"score: {data['score']}"
        # emb.set_image(url=data['image_url'])
        await inter.message.edit(file=disnake.File(data['image_path']), attachments=[], view=await play_view(possible_moves=data["possible_moves"], score=data['score'], name=inter.author.name))


class continue_select_view(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(continue_select())
        self.add_item(
            disnake.ui.Button(
                style=disnake.ButtonStyle.red,
                emoji=emojis["exit"],
                custom_id="exit",
                disabled=False,
                row=1,
            )
        )


class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix="_", asyncio_debug=True)
        self.persistent_views_added = False

    async def on_ready(self):
        if not self.persistent_views_added:
            self.add_view(continue_select_view())


bot = Bot()


@bot.slash_command()
async def scores(inter: disnake.ApplicationCommandInteraction) -> None:
    data = await fetch_endpoint(url=f"{baseurl}scores?")
    await inter.response.send_message(
        embed=disnake.Embed(description=data["discord"], color=0xCCCCCC)
    )


@bot.slash_command()
async def play(inter: disnake.ApplicationCommandInteraction) -> None:
    data = await fetch_endpoint(url=f"{baseurl}data?", param={"id": inter.author.id, "name": inter.author.name})
    if data["can_continue"] == 1:
        view = continue_select_view()
    else:
        view = await play_view(possible_moves=data["possible_moves"], score=data['score'], name=inter.author.name)
    await inter.response.send_message(file=disnake.File(data['image_path']), view=view)

@bot.event
async def on_button_click(inter) -> None:
    if inter.component.custom_id == "exit":
        await inter.response.defer()
        await inter.message.delete()
        return
    c = ''
    data = await fetch_endpoint(url=f"{baseurl}move?", param={"id": inter.author.id, "action": inter.component.custom_id})
    if data["possible_moves"]['over']:
        c = 'Game Over!'
    await inter.response.defer()
    await inter.edit_original_message(content=c, file=disnake.File(data['image_path']), attachments=[], view=await play_view(possible_moves=data["possible_moves"], score=data['score'], name=inter.author.name))

bot.run(getenv("DISCORD_TOKEN"))
