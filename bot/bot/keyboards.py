from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Novy filtr", callback_data="new_filter"
                ),
                InlineKeyboardButton(
                    text="Moje filtry", callback_data="my_filters"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Statistiky", callback_data="stats"
                ),
                InlineKeyboardButton(
                    text="Napoveda", callback_data="help"
                ),
            ],
        ]
    )


def transaction_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Prodej", callback_data="ft_trans_prodej"),
                InlineKeyboardButton(text="Pronajem", callback_data="ft_trans_pronajem"),
            ],
            [
                InlineKeyboardButton(text="Oba", callback_data="ft_trans_any"),
            ],
        ]
    )


def property_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Byt", callback_data="ft_prop_byt"),
                InlineKeyboardButton(text="Dum", callback_data="ft_prop_dum"),
            ],
            [
                InlineKeyboardButton(text="Pozemek", callback_data="ft_prop_pozemek"),
                InlineKeyboardButton(text="Vsechny", callback_data="ft_prop_any"),
            ],
        ]
    )


def disposition_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1+kk", callback_data="ft_disp_1+kk"),
                InlineKeyboardButton(text="1+1", callback_data="ft_disp_1+1"),
                InlineKeyboardButton(text="2+kk", callback_data="ft_disp_2+kk"),
            ],
            [
                InlineKeyboardButton(text="2+1", callback_data="ft_disp_2+1"),
                InlineKeyboardButton(text="3+kk", callback_data="ft_disp_3+kk"),
                InlineKeyboardButton(text="3+1", callback_data="ft_disp_3+1"),
            ],
            [
                InlineKeyboardButton(text="4+kk", callback_data="ft_disp_4+kk"),
                InlineKeyboardButton(text="4+1", callback_data="ft_disp_4+1"),
                InlineKeyboardButton(text="5+", callback_data="ft_disp_5+"),
            ],
            [
                InlineKeyboardButton(text="Vsechny", callback_data="ft_disp_any"),
            ],
        ]
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ulozit filtr", callback_data="ft_confirm"),
                InlineKeyboardButton(text="Zrusit", callback_data="ft_cancel"),
            ],
        ]
    )


def filter_actions_keyboard(filter_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Smazat", callback_data=f"del_filter_{filter_id}"
                ),
                InlineKeyboardButton(
                    text="Pozastavit/Aktivovat",
                    callback_data=f"toggle_filter_{filter_id}",
                ),
            ],
        ]
    )
