from loader import *
from other.funcs import *
import discord
import config


class Buttons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None
        self.button_configs = config.roles

        for key in self.button_configs:
            self.add_item(discord.ui.Button(label=key['label'], row=key['row'], style=key['style'],
                                            custom_id=key['custom_id']))


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        button_id = interaction.data['custom_id']
        await self.handle_role(interaction, button_id)
        return True


    async def handle_role(self, interaction: discord.Interaction, button_id):
        # Убираем все имеющиеся роли альянса
        for delete_role_id in config.roles:
            role = interaction.guild.get_role(delete_role_id['role_id'])
            if role:
                await interaction.user.remove_roles(role)

        # Если это не только удаление ролей, то выдача запрошенной роли
        if button_id != 'role:delete':
            role_id = next((config['role_id'] for config in self.button_configs if config['custom_id'] == button_id),
                           None)
            if role_id:
                role = interaction.guild.get_role(role_id)
                if role:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f':star: Успешно выдана роль: {role.name}', ephemeral=True)
                    logger.info(f'{interaction.user.id}: выдана роль - {role.name}')
        else:
            await interaction.response.send_message(':star: Успешно сняты роли альянса', ephemeral=True)


class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def get_roles(self, ctx):
        embed = discord.Embed(title="❕ Получите роль, чтобы продолжить общение!",
                              colour=0x00f5cc)

        embed.set_author(name="AllianceBot | 🗡 Авто-выдача ролей",
                         icon_url="https://i.imgur.com/n4b21Yo.png")

        embed.set_image(url="https://i.imgur.com/8YVqwyI.png")

        # Send message with buttons
        await ctx.send(embed=embed, view=Buttons())
