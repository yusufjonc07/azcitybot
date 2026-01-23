from aiogram.filters.callback_data import CallbackData
from loader import _
from .base import BaseInlineKeyboard


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

class ChooseToSend(BaseInlineKeyboard):
    def keyboard(self, users):
        builder = self.builder()
        
        for id, name in users:
            builder.button(
                text=str(name),
                callback_data=ChooseToSend.Callback(data=id)
            )
            
        builder.adjust(1)
        return builder.as_markup()

    class Callback(CallbackData, prefix="choosetosend"):
        data: int


EndChatKeyboard = EndChatKeyboard()
ClaimChatKeyboard = ClaimChatKeyboard()
CancelChatKeyboard = CancelChatKeyboard()
ChooseToSend = ChooseToSend()