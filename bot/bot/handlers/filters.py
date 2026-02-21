from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    transaction_type_keyboard,
    property_type_keyboard,
    disposition_keyboard,
    confirm_keyboard,
    filter_actions_keyboard,
    main_menu_keyboard,
)

router = Router()


class FilterWizard(StatesGroup):
    transaction_type = State()
    property_type = State()
    city = State()
    price_range = State()
    disposition = State()
    confirm = State()


# --- Start filter creation ---

@router.callback_query(F.data == "new_filter")
async def start_filter_wizard(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(FilterWizard.transaction_type)
    await callback.message.edit_text(
        "Novy filtr — Krok 1/5\n\nVyberte typ transakce:",
        reply_markup=transaction_type_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ft_trans_"), FilterWizard.transaction_type)
async def set_transaction_type(callback: CallbackQuery, state: FSMContext):
    value = callback.data.replace("ft_trans_", "")
    await state.update_data(transaction_type=None if value == "any" else value)
    await state.set_state(FilterWizard.property_type)
    await callback.message.edit_text(
        "Novy filtr — Krok 2/5\n\nVyberte typ nemovitosti:",
        reply_markup=property_type_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ft_prop_"), FilterWizard.property_type)
async def set_property_type(callback: CallbackQuery, state: FSMContext):
    value = callback.data.replace("ft_prop_", "")
    await state.update_data(property_type=None if value == "any" else value)
    await state.set_state(FilterWizard.city)
    await callback.message.edit_text(
        "Novy filtr — Krok 3/5\n\n"
        "Zadejte mesto (napr. Praha, Brno) nebo napiste 'vse' pro vsechna mesta:",
    )
    await callback.answer()


@router.message(FilterWizard.city)
async def set_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.update_data(city=None if city.lower() in ("vse", "vše", "all", "*") else city)
    await state.set_state(FilterWizard.price_range)
    await message.answer(
        "Novy filtr — Krok 4/5\n\n"
        "Zadejte cenovy rozsah ve formatu: MIN-MAX\n"
        "Napr: 2000000-5000000 (v CZK)\n"
        "Nebo napiste 'vse' pro libovolnou cenu:",
    )


@router.message(FilterWizard.price_range)
async def set_price_range(message: Message, state: FSMContext):
    text = message.text.strip()
    price_min = None
    price_max = None

    if text.lower() not in ("vse", "vše", "all", "*"):
        parts = text.replace(" ", "").split("-")
        if len(parts) == 2:
            try:
                price_min = float(parts[0])
                price_max = float(parts[1])
            except ValueError:
                await message.answer("Neplatny format. Zadejte napr: 2000000-5000000")
                return

    await state.update_data(price_min=price_min, price_max=price_max)
    await state.set_state(FilterWizard.disposition)
    await message.answer(
        "Novy filtr — Krok 5/5\n\nVyberte dispozici:",
        reply_markup=disposition_keyboard(),
    )


@router.callback_query(F.data.startswith("ft_disp_"), FilterWizard.disposition)
async def set_disposition(callback: CallbackQuery, state: FSMContext):
    value = callback.data.replace("ft_disp_", "")
    await state.update_data(disposition=None if value == "any" else value)
    await state.set_state(FilterWizard.confirm)

    data = await state.get_data()
    summary = format_filter_summary(data)

    await callback.message.edit_text(
        f"Souhrn filtru:\n\n{summary}\n\nUlozit tento filtr?",
        reply_markup=confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "ft_confirm", FilterWizard.confirm)
async def confirm_filter(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    data = await state.get_data()

    from bot.main import UserFilter
    uf = UserFilter(
        telegram_chat_id=callback.from_user.id,
        name=f"Filtr {data.get('city', 'CZ')}",
        property_type=data.get("property_type"),
        transaction_type=data.get("transaction_type"),
        city=data.get("city"),
        disposition=data.get("disposition"),
        price_min=data.get("price_min"),
        price_max=data.get("price_max"),
        notify_new=True,
        notify_price_drop=True,
    )
    db.add(uf)
    await db.commit()

    await state.clear()
    await callback.message.edit_text(
        "Filtr byl ulozen! Budete dostavat upozorneni na odpovidajici nemovitosti.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "ft_cancel")
async def cancel_filter(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Vytvareni filtru bylo zruseno.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


# --- List filters ---

@router.message(Command("filters"))
async def cmd_filters(message: Message, db: AsyncSession):
    await show_filters(message, db, message.from_user.id)


@router.callback_query(F.data == "my_filters")
async def cb_my_filters(callback: CallbackQuery, db: AsyncSession):
    await show_filters(callback.message, db, callback.from_user.id, edit=True)
    await callback.answer()


async def show_filters(message: Message, db: AsyncSession, chat_id: int, edit: bool = False):
    from bot.main import UserFilter
    query = select(UserFilter).where(UserFilter.telegram_chat_id == chat_id)
    result = await db.execute(query)
    filters = result.scalars().all()

    if not filters:
        text = "Nemate zadne filtry. Vytvorte novy pomoci 'Novy filtr'."
        if edit:
            await message.edit_text(text, reply_markup=main_menu_keyboard())
        else:
            await message.answer(text, reply_markup=main_menu_keyboard())
        return

    for uf in filters:
        status = "Aktivni" if uf.active else "Pozastaveny"
        text = (
            f"Filtr: {uf.name}\n"
            f"Stav: {status}\n"
            f"Typ: {uf.transaction_type or 'vsechny'} / {uf.property_type or 'vsechny'}\n"
            f"Mesto: {uf.city or 'vsechna'}\n"
            f"Cena: {format_price_range(uf.price_min, uf.price_max)}\n"
            f"Dispozice: {uf.disposition or 'vsechny'}"
        )
        await message.answer(text, reply_markup=filter_actions_keyboard(uf.id))


@router.callback_query(F.data.startswith("del_filter_"))
async def delete_filter(callback: CallbackQuery, db: AsyncSession):
    filter_id = int(callback.data.replace("del_filter_", ""))
    from bot.main import UserFilter
    query = select(UserFilter).where(
        UserFilter.id == filter_id,
        UserFilter.telegram_chat_id == callback.from_user.id,
    )
    result = await db.execute(query)
    uf = result.scalar_one_or_none()
    if uf:
        await db.delete(uf)
        await db.commit()
        await callback.message.edit_text("Filtr byl smazan.")
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_filter_"))
async def toggle_filter(callback: CallbackQuery, db: AsyncSession):
    filter_id = int(callback.data.replace("toggle_filter_", ""))
    from bot.main import UserFilter
    query = select(UserFilter).where(
        UserFilter.id == filter_id,
        UserFilter.telegram_chat_id == callback.from_user.id,
    )
    result = await db.execute(query)
    uf = result.scalar_one_or_none()
    if uf:
        uf.active = not uf.active
        await db.commit()
        status = "aktivovan" if uf.active else "pozastaven"
        await callback.message.edit_text(f"Filtr byl {status}.")
    await callback.answer()


def format_filter_summary(data: dict) -> str:
    lines = []
    lines.append(f"Transakce: {data.get('transaction_type') or 'vsechny'}")
    lines.append(f"Typ: {data.get('property_type') or 'vsechny'}")
    lines.append(f"Mesto: {data.get('city') or 'vsechna'}")
    lines.append(f"Cena: {format_price_range(data.get('price_min'), data.get('price_max'))}")
    lines.append(f"Dispozice: {data.get('disposition') or 'vsechny'}")
    return "\n".join(lines)


def format_price_range(price_min, price_max) -> str:
    if price_min and price_max:
        return f"{int(price_min):,} - {int(price_max):,} CZK".replace(",", " ")
    elif price_min:
        return f"od {int(price_min):,} CZK".replace(",", " ")
    elif price_max:
        return f"do {int(price_max):,} CZK".replace(",", " ")
    return "libovolna"
