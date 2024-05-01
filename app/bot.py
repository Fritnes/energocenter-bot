import os
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Fetch the token and allowed users from environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_USERS = os.getenv('ALLOWED_USERS', '')  # Expects a comma-separated list of user IDs

# Convert the string of user IDs into a set of integers
allowed_users = set(int(uid.strip()) for uid in ALLOWED_USERS.split(','))

# Database connection settings
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Establish a connection to the database
def connect_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in allowed_users:
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    await update.message.reply_text('Hello')

# Command handler for /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in allowed_users:
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT dt AT TIME ZONE 'EEST' AS Date, Idparam AS Line, val*3600 AS Power
            FROM public.d_quality t
            WHERE t.idfiders = 2 AND t.idparam IN (1, 2, 3)
            ORDER BY idfiders ASC, dt DESC, idparam ASC
            LIMIT 3;
        """)
        rows = cur.fetchall()
        message = "Latest Data:\n"
        total_power = 0
        for row in rows:
            date, line, power = row
            message += f"Date: {date}, Line: {line}, Power: {power:.2f} KWatts\n"
            total_power += power
        message += f"\nTotal Power (sum of all lines): {total_power:.2f} KWatts"
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text('Failed to fetch status.')
        print(e)
    finally:
        cur.close()
        conn.close()

# Main function to handle the bot
def main():
    application = Application.builder().token(TOKEN).build()
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    status_handler = CommandHandler('status', status)
    application.add_handler(status_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
