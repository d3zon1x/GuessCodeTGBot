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

# Function to generate a random 4-digit number
def generate_number():
    digits = random.sample('0123456789', 4)
    return ''.join(digits)

# Logic to check guesses
def check_guess(secret, guess):
    correct_pos = 0
    wrong_pos = 0

    secret_matched = [False] * len(secret)
    guess_matched = [False] * len(guess)

    # First pass: Find correct digits in the correct position
    for i in range(len(secret)):
        if secret[i] == guess[i]:
            correct_pos += 1
            secret_matched[i] = True
            guess_matched[i] = True

    # Second pass: Find correct digits in the wrong position
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


# /setcode command - sets the user's secret number in multiplayer game
async def setcode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Check if the user is in an active game
    if user_id not in active_games:
        await update.message.reply_text("Ви не в активній грі. Використайте /invite, щоб розпочати гру.")
        return

    # Validate the secret code
    if not context.args:
        await update.message.reply_text("Будь ласка, надішліть свій секретний код. Приклад: /setcode 1234")
        return

    secret_code = context.args[0]

    if (len(secret_code) != 4 or not secret_code.isdigit() or
            len(set(secret_code)) != 4):
        await update.message.reply_text(
            'Будь ласка, надішліть 4-значний код з неповторюваними цифрами. Приклад: /setcode 1234',
            parse_mode=ParseMode.HTML
        )
        return

    game_session = active_games[user_id]
    game_session['secrets'][user_id] = secret_code

    await update.message.reply_text("Ваш секретний код встановлено!")

    # Check if both players have set their codes
    if len(game_session['secrets']) == 2:
        # Notify players that the game is starting
        for pid in game_session['players']:
            if pid == game_session['turn']:
                await context.bot.send_message(
                    chat_id=pid,
                    text="Гра розпочалася! Зараз ваш хід. Введіть свій здогад.",
                    parse_mode=ParseMode.HTML
                )
            else:
                opponent_name = (await context.bot.get_chat(game_session['turn'])).full_name
                await context.bot.send_message(
                    chat_id=pid,
                    text=f"Гра розпочалася! Зараз хід вашого опонента <b>{opponent_name}</b>.",
                    parse_mode=ParseMode.HTML
                )

# /guess command - makes a guess in multiplayer game
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Check if the user is in an active game
    if user_id not in active_games:
        await update.message.reply_text("Ви не в активній грі.")
        return

    game_session = active_games[user_id]
    if game_session['turn'] != user_id:
        await update.message.reply_text("Зараз не ваш хід. Будь ласка, зачекайте свого ходу.")
        return

    # Validate the guess
    if not context.args or len(context.args[0]) != 4 or not context.args[0].isdigit():
        await update.message.reply_text("Будь ласка, введіть 4-значний здогад. Приклад: /guess 1234")
        return

    guess_number = context.args[0]
    opponent_id = [pid for pid in game_session['players'] if pid != user_id][0]
    opponent_secret = game_session['secrets'].get(opponent_id)

    if not opponent_secret:
        await update.message.reply_text("Ваш опонент ще не встановив свій секретний код.")
        return

    # Check the guess
    correct_pos, wrong_pos = check_guess(opponent_secret, guess_number)
    game_session['attempts'][user_id] += 1
    game_session['guesses'][user_id].append(guess_number)

    # Check if the guess is correct
    if correct_pos == 4:
        await update.message.reply_text(
            f"Вітаємо! Ви вгадали код опонента {opponent_secret} за {game_session['attempts'][user_id]} спроб."
        )
        await context.bot.send_message(
            chat_id=opponent_id,
            text="На жаль, ваш опонент вгадав ваш код. Гра завершена."
        )
        # End the game for both players
        del active_games[user_id]
        del active_games[opponent_id]
    else:
        await update.message.reply_text(
            f"{correct_pos} цифр(и) на своєму місці, {wrong_pos} цифр(и) не на своєму місці."
        )

        # Switch turns
        game_session['turn'] = opponent_id
        await context.bot.send_message(
            chat_id=opponent_id,
            text="Зараз ваш хід. Введіть свій здогад за допомогою команди /guess <число>"
        )

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    guess_number = update.message.text.strip()

    # Validate input


    # Check if the user is in a multiplayer game
    if user_id in active_games:
        game_session = active_games[user_id]
        if game_session['turn'] != user_id:
            await update.message.reply_text("Зараз не ваш хід. Будь ласка, зачекайте свого ходу.")
            return

        opponent_id = [pid for pid in game_session['players'] if pid != user_id][0]
        opponent_secret = game_session['secrets'].get(opponent_id)

        if not opponent_secret:
            await update.message.reply_text("Ваш опонент ще не встановив свій секретний код.")
            return

        # Check the guess
        correct_pos, wrong_pos = check_guess(opponent_secret, guess_number)
        game_session['attempts'][user_id] += 1
        game_session['guesses'][user_id].append(guess_number)

        # Check if the guess is correct
        if correct_pos == 4:
            await update.message.reply_text(
                f"Вітаємо! Ви вгадали код опонента {opponent_secret} за {game_session['attempts'][user_id]} спроб."
            )
            await context.bot.send_message(
                chat_id=opponent_id,
                text="На жаль, ваш опонент вгадав ваш код. Гра завершена."
            )
            # End the game for both players
            del active_games[user_id]
            del active_games[opponent_id]
        else:
            await update.message.reply_text(
                f"{correct_pos} цифр(и) на своєму місці, {wrong_pos} цифр(и) не на своєму місці."
            )

            # Switch turns
            game_session['turn'] = opponent_id
            await context.bot.send_message(
                chat_id=opponent_id,
                text="Зараз ваш хід. Введіть свій здогад."
            )
    else:
        # Single-player game
        if user_id not in context.user_data:
            context.user_data[user_id] = {
                "secret": generate_number(),
                "attempts": 0,
                "message_ids": []
            }

        secret = context.user_data[user_id]["secret"]

        # Check the guess
        correct_pos, wrong_pos = check_guess(secret, guess_number)

        context.user_data[user_id]["attempts"] += 1

        if correct_pos == 4:
            message = await update.message.reply_text(
                f"Вітаю! Ти вгадав число {secret} за {context.user_data[user_id]['attempts']} спроб.",
                parse_mode=ParseMode.HTML
            )
            context.user_data[user_id]["message_ids"].append(message.message_id)
            # Reset the game
            context.user_data[user_id] = {
                "secret": generate_number(),
                "attempts": 0,
                "message_ids": []
            }
        elif wrong_pos == 0 and correct_pos == 0:
            message = await update.message.reply_text(
                "На жаль, жодної цифри не вгадано. Спробуй ще!",
                parse_mode=ParseMode.HTML
            )
            context.user_data[user_id]["message_ids"].append(message.message_id)
        else:
            message = await update.message.reply_text(
                f"{correct_pos} цифр(и) на своєму місці, {wrong_pos} цифр(и) не на своєму місці. Спробуй ще!",
                parse_mode=ParseMode.HTML
            )
            context.user_data[user_id]["message_ids"].append(message.message_id)
#endregion

#region ----------Offline----------

async def guess_single_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Check if the user is in a multiplayer game
    if user_id in active_games:
        await update.message.reply_text("Ви в активній грі з другом. Використайте команду /guess для здогадів.")
        return

    if user_id not in context.user_data:
        context.user_data[user_id] = {
            "secret": generate_number(),
            "attempts": 0,
            "message_ids": []
        }

    secret = context.user_data[user_id]["secret"]
    guess_number = update.message.text.strip()

    # Validate input
    if len(guess_number) != 4 or not guess_number.isdigit():
        message = await update.message.reply_text(
            'Будь ласка, введіть <b>4-значне</b> число.',
            parse_mode=ParseMode.HTML
        )
        context.user_data[user_id]["message_ids"].append(message.message_id)
        return

    correct_pos, wrong_pos = check_guess(secret, guess_number)

    context.user_data[user_id]["attempts"] += 1
    # if guess_number == "1488":
    #     message = await update.message.reply_text(
    #         f"Ти ебанат яке 1488? зверя нет страшней кашкі {(await context.bot.get_chat(user_id)).full_name} нюхає какашкє пасхалкоооооооооо"
    #     )
    if correct_pos == 4:
        message = await update.message.reply_text(
            f"Вітаю! Ти вгадав число {secret} за {context.user_data[user_id]['attempts']} спроб.",
            parse_mode=ParseMode.HTML
        )
        context.user_data[user_id]["message_ids"].append(message.message_id)
        # Reset the game
        context.user_data[user_id] = {
            "secret": generate_number(),
            "attempts": 0,
            "message_ids": []
        }
    elif wrong_pos == 0 and correct_pos == 0:
        message = await update.message.reply_text(
            "На жаль, жодної цифри не вгадано. Спробуй ще!",
            parse_mode=ParseMode.HTML
        )
        context.user_data[user_id]["message_ids"].append(message.message_id)
    else:
        message = await update.message.reply_text(
            f"{correct_pos} цифр(и) на своєму місці, {wrong_pos} цифр(и) не на своєму місці. Спробуй ще!",
            parse_mode=ParseMode.HTML
        )
        context.user_data[user_id]["message_ids"].append(message.message_id)



#endregion

#region ----------Commands----------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    # Initialize user data for single-player game
    context.user_data[user_id] = {
        "secret": generate_number(),
        "attempts": 0,
        "message_ids": []
    }
    # Send message with bold text and store the message ID
    message = await update.message.reply_text(
        '<b>Привіт!</b> Я бот для гри в "Вгадай число".\n'
        'Я загадав 4-значне число, спробуй його вгадати. Введи своє число!',
        parse_mode=ParseMode.HTML
    )
    context.user_data[user_id]["message_ids"].append(message.message_id)

# /restart command - restarts single-player game
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Retrieve the old secret number before resetting
    old_secret = context.user_data.get(user_id, {}).get("secret", "N/A")

    # Retrieve and delete previous messages
    message_ids = context.user_data.get(user_id, {}).get("message_ids", [])

    for msg_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except Exception as e:
            print(f"Failed to delete message {msg_id}: {e}")
            pass  # Ignore messages that can't be deleted

    # Reset the game state for the user
    context.user_data[user_id] = {
        "secret": generate_number(),
        "attempts": 0,
        "message_ids": []
    }

    # Inform the user that the game is restarting and display the old secret number
    message = await update.message.reply_text(
        f'Гра перезапущена! Попереднє число було: <b>{old_secret}</b>.\n'
        'Я знову загадав число, спробуй його вгадати.',
        parse_mode=ParseMode.HTML
    )
    context.user_data[user_id]["message_ids"].append(message.message_id)

    # /invite command - generates an invitation code for multiplayer game

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # End single-player game if active
    if user_id in context.user_data:
        del context.user_data[user_id]

    # Generate a unique 8-digit code
    invitation_code = ''.join(random.choices(string.digits, k=8))

    # Store the invitation
    pending_invitations[invitation_code] = user_id

    # Inform the user
    await update.message.reply_text(
        f"Ваш код запрошення: <b>{invitation_code}</b>\n"
        "Поділіться цим кодом з другом. Коли він введе його за допомогою команди /join, гра розпочнеться.",
        parse_mode=ParseMode.HTML
    )

    # /join command - joins a multiplayer game using the invitation code

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Check if the user provided an invitation code
    if not context.args:
        await update.message.reply_text("Будь ласка, введіть код запрошення. Приклад: /join 12345678")
        return

    invitation_code = context.args[0]

    # Check if the invitation code exists
    if invitation_code not in pending_invitations:
        await update.message.reply_text("Невірний код запрошення. Перевірте та спробуйте ще раз.")
        return

    player1_id = pending_invitations.pop(invitation_code)
    player2_id = user_id

    # End single-player games for both players if active
    if player1_id in context.user_data:
        del context.user_data[player1_id]
    if player2_id in context.user_data:
        del context.user_data[player2_id]

    # Initialize the game session
    game_session = {
        'players': [player1_id, player2_id],
        'secrets': {},      # player_id: secret_number
        'attempts': {player1_id: 0, player2_id: 0},
        'turn': player1_id, # whose turn it is
        'guesses': {player1_id: [], player2_id: []}  # store guesses
    }

    # Store the game session for both players
    active_games[player1_id] = game_session
    active_games[player2_id] = game_session

    # Notify both players
    player1_name = (await context.bot.get_chat(player1_id)).full_name
    player2_name = update.effective_user.full_name

    await context.bot.send_message(
        chat_id=player1_id,
        text=f"Гравець <b>{player2_name}</b> приєднався до гри! Будь ласка, надішліть свій секретний 4-значний код з неповторюваними цифрами за допомогою команди /setcode",
        parse_mode=ParseMode.HTML
    )
    await update.message.reply_text(
        f"Ви приєдналися до гри з <b>{player1_name}</b>! Будь ласка, надішліть свій секретний 4-значний код з неповторюваними цифрами за допомогою команди /setcode",
        parse_mode=ParseMode.HTML
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            await update.message.reply_text(
                "Список доступних команд:\n"
        "/start - Розпочати одиночну гру\n"
        "/restart - Перезапустити одиночну гру\n"
        "/invite - Створити код запрошення для гри з другом\n"
        "/join <код> - Приєднатися до гри з другом за кодом\n"
        "/setcode <число> - Встановити свій секретний код у грі з другом\n"
        "/guess <число> - Зробити здогад у грі з другом\n"
        "/endgame - Завершити поточну гру з другом\n"
        "/help - Показати це повідомлення"
            )

async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Check if the user is in an active multiplayer game
    if user_id not in active_games:
        await update.message.reply_text("Ви не в активній грі, яку можна завершити.")
        return

    game_session = active_games[user_id]
    opponent_id = [pid for pid in game_session['players'] if pid != user_id][0]

    # Notify both players
    await update.message.reply_text("Ви завершили гру. Дякуємо за гру!")
    await context.bot.send_message(
        chat_id=opponent_id,
        text="Ваш опонент завершив гру. Дякуємо за гру!"
    )

    # Clean up the game session data
    del active_games[user_id]
    del active_games[opponent_id]
#endregion



def main():
    # Enter your BotFather token
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

    # Handle number inputs for single-player game
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
