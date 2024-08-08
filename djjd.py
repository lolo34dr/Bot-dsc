import discord
from discord.ext import commands, tasks
import requests
import asyncio
import json
import colorama
from colorama import init, Fore, Style
import random
import psutil

# Initialisation de colorama
init()

# Utilisation d'un espace réservé pour le jeton pour des raisons de sécurité
TOKEN = 'MTI2MTA0MjAxMTU5NTczNTA3MQ.GXNw8r.Legx4PhWxzsIY1QRfr7TxGoz89N5_dXI8hCER0'
YOUTUBE_API_KEY = 'AIzaSyAXv5cW6Hr_BaDVaIjEmnGXrd_Veu2BxYY'
CHANNEL_ID = 'UCu0z7E_xsrvqrwKbgwo7ZDg'
DISCORD_CHANNEL_ID = 1259868354647166999  # Remplacez par l'ID de votre canal Discord
ROLE_NAME = 'NEWS'

# Variable globale pour garder une trace des scores
scores = {'utilisateur': 0, 'bot': 0}

# Choix par défaut pour Pierre, Feuille, Ciseaux
choix_par_defaut = ['pierre', 'feuille', 'ciseaux']
# Choix personnalisés pour Pierre, Feuille, Ciseaux (modifiables par commande)
choix_personnalises = choix_par_defaut.copy()

# Jeu par défaut pour la Rich Presence
presence_par_defaut = "Counter-Strike 2"
presence_actuelle = presence_par_defaut  # Suivi de la présence actuelle

# Liste pour suivre les erreurs récentes
erreurs_recentes = []

# Intentions Discord pour les événements que le bot écoute
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True  # Activer l'intention de membres
intents.presences = True  # Activer l'intention de présences
intents.voice_states = True  # Activer l'intention de voix

# Initialisation du bot avec un préfixe de commande
bot = commands.Bot(command_prefix='!', intents=intents)

last_video_id = None

@tasks.loop(minutes=10)
async def check_youtube():
    global last_video_id
    url = f'https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={CHANNEL_ID}&part=snippet,id&order=date&maxResults=1'
    response = requests.get(url)
    data = response.json()
    video_id = data['items'][0]['id']['videoId']
    title = data['items'][0]['snippet']['title']
    video_url = f'https://www.youtube.com/watch?v={video_id}'

    if video_id != last_video_id:
        last_video_id = video_id
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        role = discord.utils.get(channel.guild.roles, name=ROLE_NAME)
        if role:
            await channel.send(f'{role.mention} Nouvelle vidéo : **{title}**\n{video_url}')

@bot.command(help="Affiche des informations sur le bot")
async def info(ctx):
    # Trie les commandes par ordre alphabétique
    commandes_triees = sorted(bot.commands, key=lambda x: x.name)

    liste_commandes = "\n".join([f"**{cmd.name}** - {cmd.help}" for cmd in commandes_triees])

    embed = discord.Embed(title="Informations sur le bot", description="Informations à propos du bot Discord", color=discord.Color.blue())
    embed.add_field(name="Nom du Bot", value=bot.user.name, inline=True)
    embed.add_field(name="ID du Bot", value=bot.user.id, inline=True)
    embed.add_field(name="Serveurs connectés", value=len(bot.guilds), inline=True)
    embed.add_field(name="Latence", value=f"{bot.latency * 1000:.2f} ms", inline=True)
    embed.add_field(name="Préfixe des commandes", value="!", inline=True)
    embed.add_field(name="Liste des commandes", value=liste_commandes, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(help="Envoie un message privé à tous les membres du serveur (administrateur seulement)")
async def dmall(ctx, *, message: str):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        return

    nombre_succes = 0
    nombre_echecs = 0

    for member in ctx.guild.members:
        if not member.bot:
            try:
                await member.send(message)
                nombre_succes += 1
                print(f'Message envoyé à {member.name}')
            except Exception as e:
                nombre_echecs += 1
                erreurs_recentes.append(f'Erreur en envoyant un message à {member.name}: {e}')
                print(f'Erreur en envoyant un message à {member.name}: {e}')
    
    await ctx.send(f"Messages privés envoyés à {nombre_succes} membres. {nombre_echecs} échecs.")

@bot.command(help="Bannit un membre du serveur (modérateur seulement)")
async def ban(ctx, member: discord.Member, *, reason="Aucune raison spécifiée"):
    if not ctx.author.guild_permissions.ban_members:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        return

    try:
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été banni pour la raison suivante: {reason}")
        print(f'{member.name} a été banni pour la raison suivante: {reason}')
    except discord.Forbidden:
        await ctx.send(f"Impossible de bannir {member.mention}. Assurez-vous que le bot a les bonnes permissions.")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur s'est produite lors du bannissement de {member.mention}: {e}")
        erreurs_recentes.append(f'Erreur en bannissant {member.name}: {e}')

@bot.command(help="Expulse un membre du serveur (modérateur seulement)")
async def kick(ctx, member: discord.Member, *, reason="Aucune raison spécifiée"):
    if not ctx.author.guild_permissions.kick_members:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        return

    try:
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} a été expulsé pour la raison suivante: {reason}")
        print(f'{member.name} a été expulsé pour la raison suivante: {reason}')
    except discord.Forbidden:
        await ctx.send(f"Impossible d'expulser {member.mention}. Assurez-vous que le bot a les bonnes permissions.")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur s'est produite lors de l'expulsion de {member.mention}: {e}")
        erreurs_recentes.append(f'Erreur en expulsant {member.name}: {e}')

@bot.command(help="Bannit temporairement un membre du serveur (modérateur seulement)")
async def tempban(ctx, member: discord.Member, duration: int, *, reason="Aucune raison spécifiée"):
    if not ctx.author.guild_permissions.ban_members:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        return

    try:
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été temporairement banni pour {duration} jours pour la raison suivante: {reason}")
        print(f'{member.name} a été temporairement banni pour {duration} jours pour la raison suivante: {reason}')
    except discord.Forbidden:
        await ctx.send(f"Impossible de bannir temporairement {member.mention}. Assurez-vous que le bot a les bonnes permissions.")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur s'est produite lors du bannissement temporaire de {member.mention}: {e}")
        erreurs_recentes.append(f'Erreur en bannissant temporairement {member.name}: {e}')

@bot.command(help="Joue à Pierre, Feuille, Ciseaux contre le bot")
async def rpc(ctx, user_choice: str):
    choix = choix_personnalises  # Utiliser les choix personnalisés
    bot_choice = random.choice(choix)

    user_choice = user_choice.lower()
    if user_choice not in choix:
        await ctx.send(f"Choix invalide. Veuillez choisir entre {', '.join(choix)}.")
        return

    if user_choice == bot_choice:
        result = "C'est une égalité!"
    elif (user_choice == 'pierre' and bot_choice == 'ciseaux') or \
         (user_choice == 'feuille' and bot_choice == 'pierre') or \
         (user_choice == 'ciseaux' and bot_choice == 'feuille'):
        result = "Vous avez gagné!"
        scores['utilisateur'] += 1
    else:
        result = "J'ai gagné!"
        scores['bot'] += 1

    embed_score = discord.Embed(title="Pierre, Feuille, Ciseaux", description=f"**{result}**\n\nScores:\nUtilisateur: {scores['utilisateur']}\nBot: {scores['bot']}", color=discord.Color.green())
    embed_score.add_field(name="Votre choix", value=user_choice.capitalize(), inline=True)
    embed_score.add_field(name="Choix du bot", value=bot_choice.capitalize(), inline=True)

    await ctx.send(embed=embed_score)

@bot.command(help="Change la Rich Presence du bot (administrateur seulement)")
async def setpresence(ctx, *, presence: str):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        return

    global presence_actuelle

    if presence.lower() == "reset":
        presence_actuelle = presence_par_defaut
        await bot.change_presence(activity=discord.Game(name=presence_par_defaut))
        await ctx.send(f"La Rich Presence a été réinitialisée à la valeur par défaut: {presence_par_defaut}")
    else:
        presence_actuelle = presence
        await bot.change_presence(activity=discord.Game(name=presence))
        await ctx.send(f"La Rich Presence a été mise à jour: {presence}")

@bot.command(help="Envoie un message privé à un utilisateur spécifié")
async def dm(ctx, member: discord.Member, *, message):
    if member == ctx.message.author:
        await ctx.send("Vous ne pouvez pas vous envoyer un message privé à vous-même.")
        return

    try:
        await member.send(message)
        await ctx.send(f"Message envoyé à {member.name}#{member.discriminator}")
        print(f"Message envoyé à {member.name}#{member.discriminator}: {message}")
    except discord.Forbidden:
        await ctx.send("Impossible d'envoyer un message à cet utilisateur. Assurez-vous que je peux lui envoyer des messages privés.")
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite: {e}")
        erreurs_recentes.append(f'Erreur en envoyant un message à {member.name}: {e}')

@bot.command(help="Supprime et recrée le salon actuel avec les mêmes permissions (administrateur seulement)")
async def nuke(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        return

    # Récupère le salon actuel
    channel_actuel = ctx.channel
    nom_salon = channel_actuel.name
    type_salon = channel_actuel.type
    categorie = channel_actuel.category  # Récupère la catégorie parente

    # Récupère les permissions du salon actuel
    permissions = {}
    for permission in channel_actuel.permissions:
        if isinstance(permission, discord.Role):
            permissions[permission] = channel_actuel.permissions_for(permission)
        elif isinstance(permission, discord.Member):
            permissions[permission] = channel_actuel.permissions_for(permission)

    try:
        # Supprime le salon actuel
        await channel_actuel.delete(reason="Commande de nuke exécutée")

        # Recrée le salon dans la même catégorie que l'original avec les mêmes permissions
        if type_salon == discord.ChannelType.text:
            nouveau_salon = await ctx.guild.create_text_channel(name=nom_salon, category=categorie, overwrites=permissions)
        elif type_salon == discord.ChannelType.voice:
            nouveau_salon = await ctx.guild.create_voice_channel(name=nom_salon, category=categorie, overwrites=permissions)

        # Envoyer un message pour indiquer que l'opération est réussie
        await ctx.send(f"Le salon `{nom_salon}` a été supprimé et recréé avec succès dans la catégorie `{categorie.name}` avec les mêmes permissions.")

        # Journalisation
        print(f"Salon {nom_salon} supprimé et recréé par {ctx.author.name}#{ctx.author.discriminator} dans la catégorie {categorie.name} avec les mêmes permissions.")

    except Exception as e:
        await ctx.send(f"Une erreur s'est produite lors de la suppression et de la recréation du salon : {e}")
        erreurs_recentes.append(f'Erreur en recréant le salon {nom_salon}: {e}')

@bot.command(help="Efface un nombre spécifié de messages dans le salon")
async def clear(ctx, amount: int):
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        return

    if amount <= 0:
        await ctx.send("Le nombre de messages doit être supérieur à zéro.")
        return

    try:
        supprimes = await ctx.channel.purge(limit=amount + 1)  # +1 pour inclure le message de commande
        await ctx.send(f"{len(supprimes) - 1} messages ont été effacés.")
    except discord.Forbidden:
        await ctx.send("Je n'ai pas la permission de gérer les messages.")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur s'est produite: {e}")
        erreurs_recentes.append(f'Erreur en effaçant les messages: {e}')

@dm.error
async def dm_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Utilisation incorrecte de la commande. Utilisation : `!dm @utilisateur message`.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Je n'ai pas pu trouver l'utilisateur. Assurez-vous de mentionner l'utilisateur avec @.")

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user.name} (ID: {bot.user.id})')
    print(f'Connecté à {len(bot.guilds)} serveurs.')
    activity = discord.Activity(name=presence_actuelle, type=discord.ActivityType.playing)
    await bot.change_presence(activity=activity)

@bot.command(help="Affiche les performances du bot : RAM, CPU, Disque, Réseau, Erreurs récentes")
async def statue(ctx):
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    network_usage = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    network_usage = f"{network_usage / 1024 / 1024:.2f} MB"

    embed = discord.Embed(title="Performances du Bot", description="Voici les performances actuelles du bot Discord.", color=discord.Color.blue())
    embed.add_field(name="Usage CPU", value=f"{cpu_usage}%")
    embed.add_field(name="Usage RAM", value=f"{ram_usage}%")
    embed.add_field(name="Usage Disque", value=f"{disk_usage}%")
    embed.add_field(name="Usage Réseau", value=network_usage)
    embed.add_field(name="Erreurs récentes", value="\n".join(erreurs_recentes) if erreurs_recentes else "Aucune erreur récente.")
    
    await ctx.send(embed=embed)

@bot.event
async def on_presence_update(before, after):
    guild = after.guild
    role_cs2 = discord.utils.get(guild.roles, name="IN GAME CS2")
    role_val = discord.utils.get(guild.roles, name="IN GAME VALORANT")

    if role_cs2 is None or role_val is None:
        print("Les rôles IN GAME CS2 ou IN GAME VALORANT n'existent pas.")
        return

    activity_names = [activity.name for activity in after.activities if activity.type == discord.ActivityType.playing]

    if "Counter-Strike 2" in activity_names:
        if role_cs2 not in after.roles:
            await after.add_roles(role_cs2)
    else:
        if role_cs2 in after.roles:
            await after.remove_roles(role_cs2)

    if "VALORANT" in activity_names:
        if role_val not in after.roles:
            await after.add_roles(role_val)
    else:
        if role_val in after.roles:
            await after.remove_roles(role_val)

@bot.event
async def on_member_update(before, after):
    role_tr3s = discord.utils.get(after.guild.roles, name="TR3S")

    if role_tr3s is None:
        print("Le rôle TR3S n'existe pas.")
        return

    if role_tr3s in after.roles and role_tr3s not in before.roles:
        # Le rôle TR3S a été ajouté
        if not after.nick or not after.nick.startswith("TR3S "):
            new_nick = f"TR3S {after.name}" if not after.nick else f"TR3S {after.nick}"
            try:
                await after.edit(nick=new_nick)
                print(f"Pseudo de {after.name} changé en {new_nick}")
            except discord.Forbidden:
                print(f"Impossible de changer le pseudo de {after.name}. Permissions manquantes.")
            except discord.HTTPException as e:
                print(f"Erreur en changeant le pseudo de {after.name}: {e}")

    elif role_tr3s not in after.roles and role_tr3s in before.roles:
        # Le rôle TR3S a été retiré
        if after.nick and after.nick.startswith("TR3S "):
            new_nick = after.nick[5:]
            try:
                await after.edit(nick=new_nick)
                print(f"Pseudo de {after.name} changé en {new_nick}")
            except discord.Forbidden:
                print(f"Impossible de changer le pseudo de {after.name}. Permissions manquantes.")
            except discord.HTTPException as e:
                print(f"Erreur en changeant le pseudo de {after.name}: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    role_in_voice = discord.utils.get(member.guild.roles, name="IN VOICE")

    if role_in_voice is None:
        print("Le rôle IN VOICE n'existe pas.")
        return

    if after.channel and role_in_voice not in member.roles:
        # Le membre a rejoint un canal vocal
        await member.add_roles(role_in_voice)
        if not member.nick or not member.nick.startswith("IN VOICE "):
            new_nick = f"IN VOICE {member.name}" if not member.nick else f"IN VOICE {member.nick}"
            try:
                await member.edit(nick=new_nick)
                print(f"Pseudo de {member.name} changé en {new_nick}")
            except discord.Forbidden:
                print(f"Impossible de changer le pseudo de {member.name}. Permissions manquantes.")
            except discord.HTTPException as e:
                print(f"Erreur en changeant le pseudo de {member.name}: {e}")

    elif before.channel and not after.channel and role_in_voice in member.roles:
        # Le membre a quitté un canal vocal
        await member.remove_roles(role_in_voice)
        if member.nick and member.nick.startswith("IN VOICE "):
            new_nick = member.nick[9:]
            try:
                await member.edit(nick=new_nick)
                print(f"Pseudo de {member.name} changé en {new_nick}")
            except discord.Forbidden:
                print(f"Impossible de changer le pseudo de {member.name}. Permissions manquantes.")
            except discord.HTTPException as e:
                print(f"Erreur en changeant le pseudo de {member.name}: {e}")

bot.run(TOKEN)
