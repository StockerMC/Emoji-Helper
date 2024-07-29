# Emoji Helper
Emoji Helper is a bot inspired by [Emote Manager](https://github.com/EmoteBot/EmoteManager/) that helps you manage emojis.
If you need any help, feel free to join the [Support Server](https://discord.gg/nptFDCVPWX) or make an issue/discussion.

## Note: This project is in development
There will be bugs/debug print statements currently.

# Commands
### Default prefixes:
- e!
<!-- E! --> 
- The bot's mention

### Notes:
- `<>` = required
- `[]` = optional
- `|` = or
- `...` = at least one
- `emoji type` = all|static|animated
- `emoji` an emoji or emoji name
- `server` a server ID or name
<!-- Add something about defaults to avoid repetitivity? possibly just for "defaults to all emojis"-->
<br>

`e!help`
    - View the bot's commands and their descriptions

### Emojis
#### Note: Your bot must have the manage emojis permission in the server for adding and modifying emojis <!-- is this correct -->

#### Adding emojis
- `e!add <name or custom emoji> [url | ...emojis]`
    - `emoji` does not include emoji names in this context
- `e!add <optional name (defaults to attachment name)> <attached image>`
    - Add an emoji/emojis to the server
    - Accepted image formats are PNG, GIF and JPEG/JPG
    - Aliases:
        - `e!steal`

<img src="./example_images/add.png" >

#### Modifying emojis
- `e!rename <name or emoji> <new name>`
    - Rename an emoji
- `e!remove <...emojis>`
    - Remove an emoji/emojis from the server
    - Aliases:
        - `e!delete`
        - `e!del`
        - `e!rm`

#### Transfering emojis

- `e!export [emoji type]`
    - Create a ZIP file with the server's emojis
    - Defaults to all emojis
    - Aliases:
        - `e!zip`
- `e!import <zip file URL or attachment>`
    - Import emojis from a ZIP file into the server
    - Aliases:
        - `e!unzip`
        - `e!addzip`
- `e!copy <server> <...emojis>`
    - Both the bot and you must have the manage emojis permission in the server
    - `e!copy all <server>`
        - Copies all the emojis from the current server to `server`

#### Other emoji-related commands

- `e!list [emoji type]`
    - Lists the emojis in the server
    - Defaults to all emojis
- `e!stats [emoji type]`
    - Shows the stats of of the provided emoji type emojis for the server
        - The number and percentage of emoji slots used and available <!-- does this make grammatical sense? -->
    - Defaults to all emojis
- `e!big <emoji>`
    - Shows an enlarged version of the emoji
    - Aliases:
        - `e!image`
- `e!info <emoji>`
    - Shows the information about an emoji

### Miscellaneous commands

- `e!emojify <...character>`
    - Turn characters into emojis
    - `e!emojify toggle`
        - Toggle the ability to use emojify command
        - This command requires the manage emojis permission
- `e!prefix [prefix]`
    - Show or change the prefix for the server
- `e!ping`
    - Show the bot's latency
- `e!invite`
    - Show the invite for the bot
    - Aliases:
        - `e!inv`
- `e!support`
    - Show the invite for the bot's support server
- `e!source`
    - Show the repository URL of the bot

# Hosting the bot

## Requirements
To host the bot, you will need:
- [Python 3.9+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [PostgresSQL 9.5+](https://www.postgresql.org/download/) (Optional) <!-- Is the version minimum correct? -->
    - For custom prefixes/toggling of the emojify command
- [ImageMagick](https://docs.wand-py.org/en/0.4.1/guide/install.html) (Optional)
    - For image compression/conversion

## Setting up the database (optional)
### Linux:
```bash
$ cd path/to/Emoji-Helper
$ sudo apt-get install xclip
$ cat data/schema.sql | xclip # copies schema.sql to your clipboard
OR
$ cd path/to/Emoji-Helper
$ cat schema.sql
# copy the printed text to your clipboard
```
```bash
$ sudo -u postgres psql
```
<!-- double check if previous step is correct -->

### Windows:
- Open command prompt and enter the following command
```bash
$ cd path\to\Emoji-Helper
$ clip data\schema.sql # copies schema.sql to your clipboard
```
- Search for psql in the search bar and open "SQL Shell (psql)"
    - Fill in the necessary information

- Enter the following
    - You don't have to name your database emoji_helper, but remember what you name it for putting it in the config later
```sql
CREATE DATABASE emoji_helper;
```
- Paste the copied SQL

## Running the bot

```bash
$ git clone https://github.com/StockerMC/Emoji-Helper
$ cd Emoji-Helper
$ (python) -m venv venv
Linux:
$ . venv/bin/activate
$ cp data/config.example.ini data/config.ini
Windows:
$ cd venv/Scripts && activate && cd ../..
$ copy data/config.example.ini data/config.ini

$ (python) -m pip install -r requirements.txt
# Open data/config.ini and add your token to [bot].token
# and mofiy the config to your needs.
$ (python) bot.py
```

- `(python)` refers to your python command
    - This is usually `py` on windows and `python3` or `python3.9` on linux

## Optional flags
#### Notes:
- Multiple flags can be used together
- All flags are optional

- `--shard-count`
    - The total number of shards.
    - Type: integer
    - Example: `(python) bot.py --shard-ids 10`
- `--shard-ids`
    - A list of shard_ids to launch the shards with.
    - Type: string of integers separated by a space
        - String means in double or single quotes as shown in the example below
    - Example: `(python) bot.py --shard-count "1 2 3 4"`
- `--config-file`
    - The file path for the config file
    - Type: `ini` file path
    - Defaults to `data/config.ini`

## Jishaku
- Jishaku is a debugging and experimenting cog that you can optionally install with `(python) -m pip install jishaku`
- Optionally, you can set flags for jishaku in your config file

<!-- # Contributing
Pull requests are welcome. -->

# License
[European Union Public License 1.2](https://choosealicense.com/licenses/eupl-1.2/)
As per the license, if you modify the source code you must make your bot open source and put its repository URL in the config file.
