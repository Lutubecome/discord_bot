import discord
from discord.ext import commands
from datetime import datetime
import dateparser

# Ersetze 'YOUR_BOT_TOKEN' mit deinem tatsächlichen Bot-Token
TOKEN = 'MTM1MzA3MzcyMzk5Njg5NzI5MQ.GU004s.VYS04P6JHv4obfkQEnufDFyfeFKDtvvThJ1vBU'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

OUTPUT_CHANNEL_ID = 1352218057816277002 # Festgelegte Kanal-ID
next_task_id = 1

REQUIRED_PERMISSIONS = discord.Permissions(send_messages=True, embed_links=True, attach_files=True, view_channel=True, read_message_history=True)

async def check_permissions(channel):
    """Prüft, ob der Bot die erforderlichen Berechtigungen in einem Kanal hat."""
    permissions = channel.permissions_for(channel.guild.me)
    missing_permissions = []
    for permission, value in REQUIRED_PERMISSIONS:
        if value and not getattr(permissions, permission):
            missing_permissions.append(permission)
    return missing_permissions

class TaskEditModal(discord.ui.Modal, title="Aufgabe bearbeiten"):
    def __init__(self, task_data):
        super().__init__()
        self.task_data = task_data
        self.fach = discord.ui.TextInput(label="Fach", default=task_data["fach"])
        self.aufgabe = discord.ui.TextInput(label="Aufgabe", default=task_data["aufgabe"], style=discord.TextStyle.paragraph)
        self.bis = discord.ui.TextInput(label="Bis (YYYY-MM-DD)", default=task_data["bis"])
        self.add_item(self.fach)
        self.add_item(self.aufgabe)
        self.add_item(self.bis)

    async def on_submit(self, interaction: discord.Interaction):
        self.task_data["fach"] = self.fach.value
        self.task_data["aufgabe"] = self.aufgabe.value
        self.task_data["bis"] = self.bis.value

        try:
            message = await interaction.channel.fetch_message(self.task_data["message_id"])
            embed = message.embeds[0]
            embed.description = f"**Fach** = {self.task_data['fach']}\n**Bis** = {self.task_data['bis']}\n**Aufgabe** = {self.task_data['aufgabe']}"
            await message.edit(embed=embed)
            await interaction.response.send_message("Aufgabe aktualisiert!", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("Nachricht nicht gefunden. Aufgabenbearbeitung fehlgeschlagen.", ephemeral=True)
        except Exception as e:
            print(f"Fehler beim Bearbeiten der Aufgabe: {e}")
            await interaction.response.send_message("Beim Bearbeiten der Aufgabe ist ein Fehler aufgetreten.", ephemeral=True)

class UploadSolutionModal(discord.ui.Modal, title="Lösung hochladen"):
    def __init__(self, message_id):
        super().__init__()
        self.message_id = message_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.message.attachments:
            attachment = interaction.message.attachments[0]
            if attachment.content_type in ['application/pdf', 'image/jpeg', 'image/png']:
                try:
                    message = await interaction.channel.fetch_message(self.message_id)
                    # Hier kannst du die Logik implementieren, um die Lösung zu speichern oder anzuzeigen
                    await interaction.response.send_message("Lösung erfolgreich hochgeladen!", ephemeral=True)
                except discord.NotFound:
                    await interaction.response.send_message("Nachricht nicht gefunden. Lösung konnte nicht hochgeladen werden.", ephemeral=True)
                except Exception as e:
                    print(f"Fehler beim Hochladen der Lösung: {e}")
                    await interaction.response.send_message("Beim Hochladen der Lösung ist ein Fehler aufgetreten.", ephemeral=True)
            else:
                await interaction.response.send_message("Bitte lade eine PDF- oder JPEG-Datei hoch.", ephemeral=True)
        else:
            await interaction.response.send_message("Bitte lade eine Datei hoch.", ephemeral=True)

class TaskView(discord.ui.View):
    def __init__(self, message_id): #message id hinzugefügt
        super().__init__()
        self.message_id = message_id #message id hinzugefügt

    @discord.ui.button(label="Bearbeiten", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TaskEditModal(self.message_id)) #message id hinzugefügt

    @discord.ui.button(label="Lösung", style=discord.ButtonStyle.success)
    async def upload_solution(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UploadSolutionModal(self.message_id)) #message id hinzugefügt


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="füge_aufgabe_hinzu", description="Füge eine neue Aufgabe hinzu")
async def füge_aufgabe_hinzu(interaction: discord.Interaction, fach: str, bis: str, aufgabe: str):
    global next_task_id
    fälligkeitsdatum = dateparser.parse(bis)
    if fälligkeitsdatum is None:
        await interaction.response.send_message("Ungültiges Datumsformat. Bitte verwende ein gültiges Datumsformat.", ephemeral=True)
        return

    aufgaben_daten = {'id': next_task_id, 'fach': fach, 'bis': bis, 'aufgabe': aufgabe, 'message_id': None}  # Speichere das eingegebene Datum
    next_task_id += 1

    await interaction.response.send_message(f"Aufgabe hinzugefügt: {fach} - {aufgabe} (Fällig: {bis})", ephemeral=True)  # Zeige das eingegebene Datum an

    ausgabekanal = bot.get_channel(OUTPUT_CHANNEL_ID)
    if ausgabekanal:
        fehlende_berechtigungen = await check_permissions(ausgabekanal)
        if fehlende_berechtigungen:
            await interaction.response.send_message(f"Bot benötigt folgende Berechtigungen in {ausgabekanal.mention}: {', '.join(fehlende_berechtigungen)}", ephemeral=True)
            return

        try:
            # Hier wird das Embed im gewünschten Format erstellt
            einbettung = discord.Embed(
                title="Neue Aufgabe",
                description=f"**Fach** = {fach}\n**Bis** = {bis}\n**Aufgabe** = {aufgabe}",  # Zeige das eingegebene Datum an
                color=discord.Color.blue()
            )
            nachricht = await ausgabekanal.send(embed=einbettung, view=TaskView(aufgaben_daten))
            aufgaben_daten['message_id'] = nachricht.id
            await nachricht.edit(view=TaskView(aufgaben_daten))
        except discord.NotFound:
            await interaction.response.send_message("Ausgabekanal nicht gefunden.", ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.response.send_message("Bot hat keine Berechtigung, Nachrichten im Ausgabekanal zu senden.", ephemeral=True)
            return
        except discord.HTTPException as e:
            print(f"Fehler beim Senden der Aufgabennachricht: {e}")
            await interaction.response.send_message("Beim Senden der Aufgabennachricht ist ein Fehler aufgetreten.", ephemeral=True)
            return
        except Exception as e:
            print(f"Fehler beim Senden der Aufgabennachricht: {e}")
            await interaction.response.send_message("Ein unerwarteter Fehler ist aufgetreten.", ephemeral=True)
            return

bot.run(TOKEN)
