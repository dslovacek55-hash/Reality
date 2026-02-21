from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Vitejte v Czech Reality Trackeru!\n\n"
        "Sleduju nemovitosti na Sreality, Bazos a Bezrealitky.\n"
        "Nastavte si filtry a dostanete upozorneni na nove inzeraty "
        "a zmeny cen.\n\n"
        "Vyberte akci:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Dostupne prikazy:\n\n"
        "/start - Hlavni menu\n"
        "/filters - Sprava filtru\n"
        "/stats - Statistiky sledovanych nemovitosti\n"
        "/help - Tato napoveda\n\n"
        "Nastavte si filtry a budete dostavat upozorneni "
        "na nove inzeraty a zmeny cen primo do Telegramu.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(lambda c: c.data == "help")
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text(
        "Dostupne prikazy:\n\n"
        "/start - Hlavni menu\n"
        "/filters - Sprava filtru\n"
        "/stats - Statistiky\n"
        "/help - Napoveda\n\n"
        "Pouzijte 'Novy filtr' pro vytvoreni notifikacniho filtru.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
