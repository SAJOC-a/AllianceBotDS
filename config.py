import discord

ffmpeg_path = "other\\ffmpeg.exe"  # Заменить на свой путь к ffmpeg
bot_token = ''  # Токен бота Discord
admins = [716257537888092182]  # Список ID администраторов, имеющих доступ к некоторым командам

roles = [  # Список ролей для выдачи (Название роли, цвет, уникальный id, id роли на сервере)
            {'label': 'EaZyBreaZy', 'row': 0, 'style': discord.ButtonStyle.green, 'custom_id': 'role:eazybreazy',
             'role_id': 1264941017698668574},
            {'label': 'Cannon', 'row': 0, 'style': discord.ButtonStyle.blurple, 'custom_id': 'role:cannon',
             'role_id': 1061469907713282068},
            {'label': 'Ramirez', 'row': 0, 'style': discord.ButtonStyle.red, 'custom_id': 'role:ramirez',
             'role_id': 1264697302581510238},
            {'label': 'Darknight', 'row': 0, 'style': discord.ButtonStyle.gray, 'custom_id': 'role:darknight',
             'role_id': 1264940222190325793},
            # {'label': 'Снять роли альянса', 'row': 0, 'style': discord.ButtonStyle.grey, 'custom_id': 'role:delete',
            #  'role_id': None}
        ]


welcome_channel_id = 1273921480215760906  # ID канала, куда будут поступать приветственные сообщения
roles_channel_id = 1273921444782407731  # ID канала, где происходит выдача ролей

use_logs = False  # Отправлять ли логи на канал в сервер? True - да, False - нет.
logs_channel_id = 1272860750804684830  # ID канала, куда будут поступать логи с сервера

use_music = False  # Загружать ли муз. часть в бота? True - да, False - нет.
music_channels = [1272860750804684830]  # ID каналов, где разрешено управление музыкой