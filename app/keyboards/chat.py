from aiogram.filters.callback_data import CallbackData
from loader import _
from .base import BaseInlineKeyboard


class NewChatKeyboard(BaseInlineKeyboard):
    def keyboard(self):
        builder = self.builder()
        builder.button(
            text=_("🟢 New Chat"),
            callback_data=NewChatKeyboard.Callback(data="start")  # oddiy string emas, Callback ishlatyapmiz
        )
        return builder.as_markup()

    class Callback(CallbackData, prefix="newchat"):
        data: str


class EndChatKeyboard(BaseInlineKeyboard):
    def keyboard(self, chatId: str):
        builder = self.builder()
        builder.button(
            text=_("🙌 End Chat"),
            callback_data=EndChatKeyboard.Callback(chatId=chatId)
        )
        return builder.as_markup()

    class Callback(CallbackData, prefix="endchat"):
        chatId: str
        
class CancelChatKeyboard(BaseInlineKeyboard):
    def keyboard(self):
        builder = self.builder()
        builder.button(
            text=_("🙅‍♂️ Cancel Chat"),
            callback_data=CancelChatKeyboard.Callback(data="cancel")
        )
        return builder.as_markup()

    class Callback(CallbackData, prefix="cancelchat"):
        data: str

class ClaimChatKeyboard(BaseInlineKeyboard):
    def keyboard(self, user_Id):
        builder = self.builder()
        builder.button(
            text=_("☑️ Claim Chat"),
            callback_data=ClaimChatKeyboard.Callback(data=user_Id)
        )
        return builder.as_markup()

    class Callback(CallbackData, prefix="claimchat"):
        data: int


NewChatKeyboard = NewChatKeyboard()
EndChatKeyboard = EndChatKeyboard()
ClaimChatKeyboard = ClaimChatKeyboard()
CancelChatKeyboard = CancelChatKeyboard()