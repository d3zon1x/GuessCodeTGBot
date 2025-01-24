import random
import string
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

# In-memory data stores
pending_invitations = {}  # invitation_code: player_id
active_games = {}         # player_id: game_session

#region ----------Functions----------

def generate_number():
    digits = random.sample('0123456789', 4)
    return ''.join(digits)

def check_guess(secret, guess):
    correct_pos = 0
    wrong_pos = 0

    secret_matched = [False] * len(secret)
    guess_matched = [False] * len(guess)

    for i in range(len(secret)):
        if secret[i] == guess[i]:
            correct_pos += 1
            secret_matched[i] = True
            guess_matched[i] = True

    for i in range(len(secret)):
        if not secret_matched[i]:
            for j in range(len(guess)):
                if not guess_matched[j] and secret[i] == guess[j]:
                    wrong_pos += 1
                    secret_matched[i] = True
                    guess_matched[j] = True
                    break

    return correct_pos, wrong_pos

#endregion

#region ----------Online----------

async def setcode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in active_games:
        await update.message.reply_text("You are not in an active game. \nUse /invite to start a game.")
        return

    if not context.args:
        await update.message.reply_text("Please send your secret code.\nExample: /setcode 1234")
        return

    secret_code = context.args[0]

    if (len(secret_code) != 4 or not secret_code.isdigit() or
            len(set(secret_code)) != 4):
        await update.message.reply_text(
            'Please send a 4-digit code with unique digits. Example: /setcode 1234',
            parse_mode=ParseMode.HTML
        )
        return

    game_session = active_games[user_id]
    game_session['secrets'][user_id] = secret_code

    await update.message.reply_text("Your secret code has been set!")

    if len(game_session['secrets']) == 2:
        for pid in game_session['players']:
            if pid == game_session['turn']:
                await context.bot.send_message(
                    chat_id=pid,
                    text="The game has started! It's your turn. Enter your guess.",
                    parse_mode=ParseMode.HTML
                )
            else:
                opponent_name = (await context.bot.get_chat(game_session['turn'])).full_name
                await context.bot.send_message(
                    chat_id=pid,
                    text=f"The game has started! It's your opponent <b>{opponent_name}</b>'s turn.",
                    parse_mode=ParseMode.HTML
                )

async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in active_games:
        await update.message.reply_text("You are not in an active game.")
        return

    game_session = active_games[user_id]
    if game_session['turn'] != user_id:
        await update.message.reply_text("It's not your turn. Please wait for your turn.")
        return

    if not context.args or len(context.args[0]) != 4 or not context.args[0].isdigit():
        await update.message.reply_text("Please enter a 4-digit guess. Example: /guess 1234")
        return

    guess_number = context.args[0]
    opponent_id = [pid for pid in game_session['players'] if pid != user_id][0]
    opponent_secret = game_session['secrets'].get(opponent_id)

    if not opponent_secret:
        await update.message.reply_text("Your opponent has not set their secret code yet.")
        return

    correct_pos, wrong_pos = check_guess(opponent_secret, guess_number)
    game_session['attempts'][user_id] += 1
    game_session['guesses'][user_id].append(guess_number)

    if correct_pos == 4:
        await update.message.reply_text(
            f"Congratulations! You guessed your opponent's code {opponent_secret} in {game_session['attempts'][user_id]} attempts."
        )
        await context.bot.send_message(
            chat_id=opponent_id,
            text="Unfortunately, your opponent guessed your code. The game is over."
        )
        del active_games[user_id]
        del active_games[opponent_id]
    else:
        await update.message.reply_text(
            f"{correct_pos} digits in the correct position, {wrong_pos} digits in the wrong position."
        )

        game_session['turn'] = opponent_id
        await context.bot.send_message(
            chat_id=opponent_id,
            text="It's your turn. Enter your guess using the /guess <number> command."
        )

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    guess_number = update.message.text.strip()

    if len(guess_number) != 4 or not guess_number.isdigit():
        await update.message.reply_text("Please enter a 4-digit number.")
        return

    if user_id in active_games:
        game_session = active_games[user_id]
        if game_session['turn'] != user_id:
            await update.message.reply_text("It's not your turn. Please wait for your turn.")
            return

        opponent_id = [pid for pid in game_session['players'] if pid != user_id][0]
        opponent_secret = game_session['secrets'].get(opponent_id)

        if not opponent_secret:
            await update.message.reply_text("Your opponent has not set their secret code yet.")
            return

        correct_pos, wrong_pos = check_guess(opponent_secret, guess_number)
        game_session['attempts'][user_id] += 1
        game_session['guesses'][user_id].append(guess_number)

        if correct_pos == 4:
            await update.message.reply_text(
                f"Congratulations! You guessed your opponent's code {opponent_secret} in {game_session['attempts'][user_id]} attempts."
            )
            await context.bot.send_message(
                chat_id=opponent_id,
                text="Unfortunately, your opponent guessed your code. The game is over."
            )
            del active_games[user_id]
            del active_games[opponent_id]
        elif wrong_pos == 0 and correct_pos == 0:
            await update.message.reply_text(
                "Unfortunately, none of the digits are correct. Try again!")

            game_session['turn'] = opponent_id
            await context.bot.send_message(
                chat_id=opponent_id,
                text="It's your turn. Enter your guess."
            )
        else:
            await update.message.reply_text(
                f"{correct_pos} digits in the correct position, {wrong_pos} digits in the wrong position."
            )

            game_session['turn'] = opponent_id
            await context.bot.send_message(
                chat_id=opponent_id,
                text="It's your turn. Enter your guess."
            )
    else:
        if user_id not in context.user_data:
            context.user_data[user_id] = {
                "secret": generate_number(),
                "attempts": 0,
                "message_ids": []
            }

        secret = context.user_data[user_id]["secret"]

        correct_pos, wrong_pos = check_guess(secret, guess_number)

        context.user_data[user_id]["attempts"] += 1

        if correct_pos == 4:
            message = await update.message.reply_text(
                f"Congratulations! You guessed the number {secret} in {context.user_data[user_id]['attempts']} attempts.",
                parse_mode=ParseMode.HTML
            )
            context.user_data[user_id]["message_ids"].append(message.message_id)
            context.user_data[user_id] = {
                "secret": generate_number(),
                "attempts": 0,
                "message_ids": []
            }
        elif wrong_pos == 0 and correct_pos == 0:
            message = await update.message.reply_text(
                "Unfortunately, none of the digits are correct. Try again!",
                parse_mode=ParseMode.HTML
            )
            context.user_data[user_id]["message_ids"].append(message.message_id)
        else:
            message = await update.message.reply_text(
                f"{correct_pos} digits in the correct position, {wrong_pos} digits in the wrong position. Try again!",
                parse_mode=ParseMode.HTML
            )
            context.user_data[user_id]["message_ids"].append(message.message_id)
#endregion

#region ----------Offline----------

async def guess_single_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id in active_games:
        await update.message.reply_text("You are in an active game with a friend. Use the /guess command for guesses.")
        return

    if user_id not in context.user_data:
        context.user_data[user_id] = {
            "secret": generate_number(),
            "attempts": 0,
            "message_ids": []
        }

    secret = context.user_data[user_id]["secret"]
    guess_number = update.message.text.strip()

    if len(guess_number) != 4 or not guess_number.isdigit():
        message = await update.message.reply_text(
            'Please enter a <b>4-digit</b> number.',
            parse_mode=ParseMode.HTML
        )
        context.user_data[user_id]["message_ids"].append(message.message_id)
        return

    correct_pos, wrong_pos = check_guess(secret, guess_number)

    context.user_data[user_id]["attempts"] += 1
    if guess_number == "1488":
        message = await update.message.reply_text(
            f"What? 1488? Not a chance! {await context.bot.get_chat(user_id).full_name}"
        )
    if correct_pos == 4:
        message = await update.message.reply_text(
            f"Congratulations! You guessed the number {secret} in {context.user_data[user_id]['attempts']} attempts.",
            parse_mode=ParseMode.HTML
        )
        context.user_data[user_id]["message_ids"].append(message.message_id)
        context.user_data[user_id] = {
            "secret": generate_number(),
            "attempts": 0,
            "message_ids": []
        }
    elif wrong_pos == 0 and correct_pos == 0:
        message = await update.message.reply_text(
            "Unfortunately, none of the digits are correct. Try again!",
            parse_mode=ParseMode.HTML
        )
        context.user_data[user_id]["message_ids"].append(message.message_id)
    else:
        message = await update.message.reply_text(
            f"{correct_pos} digits in the correct position, {wrong_pos} digits in the wrong position. Try again!",
            parse_mode=ParseMode.HTML
        )
        context.user_data[user_id]["message_ids"].append(message.message_id)

#endregion

#region ----------Commands----------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    context.user_data[user_id] = {
        "secret": generate_number(),
        "attempts": 0,
        "message_ids": []
    }
    message = await update.message.reply_text(
        '<b>Hello!</b> I am a bot for the "Guess the Number" game.\n'
        'I have guessed a 4-digit number, try to guess it. Enter your number!\n'
        ,
        parse_mode=ParseMode.HTML
    )
    context.user_data[user_id]["message_ids"].append(message.message_id)

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    old_secret = context.user_data.get(user_id, {}).get("secret", "N/A")

    message_ids = context.user_data.get(user_id, {}).get("message_ids", [])

    for msg_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except Exception as e:
            print(f"Failed to delete message {msg_id}: {e}")
            pass

    context.user_data[user_id] = {
        "secret": generate_number(),
        "attempts": 0,
        "message_ids": []
    }

    message = await update.message.reply_text(
        f'The game has been restarted! The previous number was: <b>{old_secret}</b>.\n'
        'I have guessed another number, try to guess it.',
        parse_mode=ParseMode.HTML
    )
    context.user_data[user_id]["message_ids"].append(message.message_id)

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id in context.user_data:
        del context.user_data[user_id]

    invitation_code = ''.join(random.choices(string.digits, k=8))

    pending_invitations[invitation_code] = user_id

    await update.message.reply_text(
        f"Your invitation code:\n",
        parse_mode=ParseMode.HTML
    )
    await update.message.reply_text(
        f"<b>{invitation_code}</b>\n",
        parse_mode=ParseMode.HTML
    )
    await update.message.reply_text(
        'Share this code with a friend. When they enter it using the /join command, the game will start.\n'
        '<b>/endgame</b> - End the current game with a friend\n',
        parse_mode=ParseMode.HTML
    )

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if not context.args:
        await update.message.reply_text("Please enter the invitation code. Example: /join 12345678")
        return

    invitation_code = context.args[0]

    if invitation_code not in pending_invitations:
        await update.message.reply_text("Invalid invitation code. Please check and try again.")
        return

    player1_id = pending_invitations.pop(invitation_code)
    player2_id = user_id

    if player1_id in context.user_data:
        del context.user_data[player1_id]
    if player2_id in context.user_data:
        del context.user_data[player2_id]

    game_session = {
        'players': [player1_id, player2_id],
        'secrets': {},
        'attempts': {player1_id: 0, player2_id: 0},
        'turn': player1_id,
        'guesses': {player1_id: [], player2_id: []}
    }

    active_games[player1_id] = game_session
    active_games[player2_id] = game_session

    player1_name = (await context.bot.get_chat(player1_id)).full_name
    player2_name = update.effective_user.full_name

    await context.bot.send_message(
        chat_id=player1_id,
        text=f"Player <b>{player2_name}</b> has joined the game! Please send your secret 4-digit code with unique digits using the /setcode command.",
        parse_mode=ParseMode.HTML
    )
    await update.message.reply_text(
        f"You have joined the game with <b>{player1_name}</b>! Please send your secret 4-digit code with unique digits using the /setcode command."
    )

    print(active_games)

async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in active_games:
        await update.message.reply_text("You are not in an active game that can be ended.")
        return

    game_session = active_games[user_id]
    opponent_id = [pid for pid in game_session['players'] if pid != user_id][0]

    await update.message.reply_text("You ended the game. Thanks for playing!")
    await context.bot.send_message(
        chat_id=opponent_id,
        text="Your opponent ended the game. Thanks for playing!"
    )

    del active_games[user_id]
    del active_games[opponent_id]

#endregion


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start a single-player game\n"
        "/restart - Restart a single-player game\n"
        "/invite - Create an invitation code for a game with a friend\n"
        "/join <code> - Join a game with a friend using a code\n"
        "/setcode <number> - Set your secret code in a multiplayer game\n"
        "/guess <number> - Make a guess in a multiplayer game\n"
        "/endgame - End the current game with a friend\n"
        "/help - Show this help message"
    )


def main():
    application = Application.builder().token("7616000568:AAGeXiJFUjcVJznFvgtD9XMroc6-JyoAhSY").build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart", restart))
    application.add_handler(CommandHandler("invite", invite))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("setcode", setcode))
    # application.add_handler(CommandHandler("guess", guess))
    application.add_handler(CommandHandler("endgame", endgame))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
