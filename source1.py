from telethon import TelegramClient
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.functions.contacts import GetBlockedRequest, GetContactsRequest
from telethon.errors import ChatAdminRequiredError
from telethon.tl.types import UserStatusOnline
from colorama import Fore, Style
from datetime import datetime
from pathlib import Path
import os
import csv
import colorama
import asyncio

colorama.init()

logo = f"""   ██████╗░░░░░░░██████╗░░░░░█████╗░
   ██╔══██╗░░░░░░╚════██╗░░░██╔══██╗
   ██████╔╝█████╗░░███╔═╝░░░██║░░██║
   ██╔═══╝░╚════╝██╔══╝░░░░░██║░░██║
   ██║░░░░░░░░░░░███████╗██╗╚█████╔╝
   ╚═╝░░░░░░░░░░░╚══════╝╚═╝░╚════╝░\n
"""

async def main():
    use_existing_sessions = input("Хотите вы войти или использовать уже существующие сессии? (0 - использовать существующие, 1 - выполнить авторизацию): ")

    if use_existing_sessions == '0':
        sessions_folder = input("Введите путь к папке с сессиями: ")
        session_files = [f for f in os.listdir(sessions_folder) if f.endswith('.session')]

        tasks = []
        for session_file in session_files:
            session_path = os.path.join(sessions_folder, session_file)
            tasks.append(parse_session(session_path))

        await asyncio.gather(*tasks)
    elif use_existing_sessions == '1':
        api_id = 
        api_hash = ""
        phone_number = ""

        client = TelegramClient(phone_number, api_id, api_hash)
        await client.start()

        await parse_account(client)
        await client.disconnect()

async def parse_session(session_path):
    api_id = 
    api_hash = ""
    client = TelegramClient(session_path, api_id, api_hash)

    print(f"Начинаю парсинг сессии {session_path}")
    await client.connect()

    if not await client.is_user_authorized():
        print(f"Сессия {session_path} не авторизована. Пропускаю...")
        return

    await parse_account(client)
    await client.disconnect()
    print(f"Парсинг сессии {session_path} завершен")

async def parse_account(client):
    me = await client.get_me()
    phone_number = me.phone
    current_time = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")

    folder_name = f"{me.phone}-{current_time}"
    folder_path = Path(folder_name)
    folder_path.mkdir(exist_ok=True)

    dialogs = await client.get_dialogs(limit=1200)
    admin_chats = [dialog for dialog in dialogs if hasattr(dialog.entity, 'admin_rights') and dialog.entity.admin_rights]
    admin_chats_count = len(admin_chats)
    dialogs_count = len(dialogs)

    try:
        if me.status:
            if isinstance(me.status, UserStatusOnline):
                formatted_time = "Online"
            else:
                form_time = me.status.was_online.strftime("%Y-%m-%d %H:%M:%S %Z")
                formatted_time = f"Offline ({form_time})"
        else:
            formatted_time = "error."
    except Exception as e:
        formatted_time = "error."

    blocked_users = await client(GetBlockedRequest(offset=0, limit=1000))
    total_blocked_users = len(blocked_users.users)

    with open(folder_path / 'Info.txt', 'a', encoding="UTF-8") as file:
        file.write('\n')
        file.write(f'{logo}')
        file.write('   ┌--------------------------------\n')
        file.write(f'   ├ First Name: {me.first_name}\n')
        file.write(f'   ├ Last Name: {me.last_name}\n')
        file.write(f'   ├ Nick (TAG): {me.username}\n')
        file.write(f'   ├ Chat ID: {me.id}\n')
        file.write(f'   ├ Phone: {me.phone}\n')
        file.write(f'   ├ Blocked Users Count: {total_blocked_users}\n')
        file.write(f'   ├ Dialogs Count: {dialogs_count}\n')
        file.write(f'   ├ Admin Rigths Dialogs: {admin_chats_count}\n')
        file.write(f'   ├ Last Activity: {formatted_time}\n')
        file.write(f'   └--------------------------------\n')

    group_folder_path = folder_path / 'groups'
    group_folder_path.mkdir(exist_ok=True)
    file_with_group_name = f"{admin_chats_count}-groups_with_admin_rigths.txt"
    file_path = group_folder_path / file_with_group_name

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write('\n')
        file.write(f'{logo}')
        file.write('   ┌--------------------------------\n')
        file.write(f'   ├ Count Chat: {admin_chats_count}\n')

        for chat in admin_chats:
            try:
                if (hasattr(chat.entity, 'megagroup') and chat.entity.megagroup) or (hasattr(chat.entity, 'broadcast') and chat.entity.broadcast):
                    try:
                        invite = await client(ExportChatInviteRequest(chat.id))
                        participants = await client.get_participants(chat.id)
                        participants_count = len(participants)

                        group_info = f"ID: {chat.id}, Название: {chat.title}, Приватная ссылка: {invite.link}"
                        if hasattr(chat.entity, 'username'):
                            group_info += f", Публичная ссылка: https://t.me/{chat.entity.username}"
                        group_info += f", Участников: {participants_count}"

                        file.write(f'   ├ {group_info}\n')

                    except ChatAdminRequiredError:
                        print(f"Ошибка: Недостаточно прав администратора для чата {chat.id}")
            except Exception as e:
                print(f"Ошибка при обработке диалога {chat.id}: {str(e)}")

        file.write(f'   └--------------------------------\n')

    blocked_folder_path = folder_path / 'blocked_users'
    blocked_folder_path.mkdir(exist_ok=True)
    txt_file_path = blocked_folder_path / 'blocked.txt'

    with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
        for user in blocked_users.users:
            user_info = f"TAG: {user.username or '-'} | ID: {user.id or '-'}," \
                        f" Имя: {user.first_name or '-'}," \
                        f" Фамилия: {user.last_name or '-'}"
            txt_file.write(user_info + '\n')

    csv_file_path = blocked_folder_path / 'blocked.csv'
    with open(csv_file_path, 'w', encoding='utf-8-sig', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=';')
        csv_writer.writerow(['TAG', 'ID', 'Имя', 'Фамилия'])
        for user in blocked_users.users:
            csv_writer.writerow([user.username or '-', user.id or '-', user.first_name or '-', user.last_name or '-'])

    contacts = await client(GetContactsRequest(
        hash=-12398745604826
    ))

    total_contacts = len(contacts.users)
    total_contacts_with_photo = sum(1 for contact in contacts.users if getattr(contact, 'photo'))

    contacts_folder_path = folder_path / 'contacts'
    contacts_folder_path.mkdir(exist_ok=True)
    contacts_photo_folder = contacts_folder_path / 'photo'
    contacts_photo_folder.mkdir(exist_ok=True)
    file_with_contact_name = f"{total_contacts}-contacts.txt"
    file_path = contacts_folder_path / file_with_contact_name

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write('\n')
        file.write(f'{logo}')
        file.write('   ┌--------------------------------\n')
        file.write(f'   ├ Count contacts: {total_contacts}\n')
        for contact in contacts.users:
            try:
                contact_info = f"   ├ Номер: {contact.phone}, Имя: {contact.first_name}, Фамилия: {contact.last_name}, TAG: {contact.username}, ID: {contact.id}"
                file.write(f"{contact_info}\n")

                if contact.photo:
                    photo = await client.get_profile_photos(contact.id, limit=1)
                    if photo:
                        file_path = contacts_photo_folder / f"{contact.phone}.jpg"
                        await client.download_media(photo[0], file=file_path)
            except Exception as e:
                pass

        file.write(f'   └--------------------------------\n')

    csv_file_path = contacts_folder_path / 'contacts.csv'
    with open(csv_file_path, 'w', encoding='utf-8-sig', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=';')
        csv_writer.writerow(['number', 'Имя', 'Фамилия', 'ID'])
        for contact in contacts.users:
            csv_writer.writerow([contact.phone or '-', contact.first_name or '-', contact.last_name or '-', contact.id or '-'])

    print(f"Информация по аккаунту {me.phone} собрана.")

if __name__ == "__main__":
    asyncio.run(main())
