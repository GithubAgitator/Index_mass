
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, PhotoSize)


BOT_TOKEN = 'Токен вашего бота'

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage: MemoryStorage = MemoryStorage()

# Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)

# Создаем "базу данных" пользователей
user_dict: dict[int, dict[str, str | int | bool]] = {}

# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillForm(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    fill_name = State()        # Состояние ожидания ввода имени
    fill_masa = State()         # Состояние ожидания ввода массы
    fill_rost = State()      # Состояние ожидания ввода роста
    fill_imt = State()

# Этот хэндлер будет срабатывать на команду /start вне состояний
# и предлагать перейти к заполнению анкеты, отправив команду /fillform
@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text='Чтобы перейти к заполнению анкеты - '
                              'отправьте команду /fillform')

# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(text='Чтобы снова перейти к заполнению анкеты - '
                              'отправьте команду /fillform')
    # Сбрасываем состояние
    await state.clear()


# Этот хэндлер будет срабатывать на команду "/cancel" в состоянии
# по умолчанию и сообщать, что эта команда доступна в машине состояний
@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(text='Отменять нечего.'
                              'Чтобы перейти к заполнению анкеты - '
                              'отправьте команду /fillform')


# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода имени
@dp.message(Command(commands='fillform'), StateFilter(default_state))
async def process_fillform_command(message: Message, state: FSMContext):
    await message.answer(text='Пожалуйста, введите ваше имя')
    # Устанавливаем состояние ожидания ввода имени
    await state.set_state(FSMFillForm.fill_name)

# Этот хэндлер будет срабатывать, если введено корректное имя

@dp.message(StateFilter(FSMFillForm.fill_name), F.text.isalpha())
async def process_name_sent(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    await state.update_data(name=message.text)
    await message.answer(text='Спасибо!\n\nА теперь введите ваш рост')
    # Устанавливаем состояние ожидания ввода возраста
    await state.set_state(FSMFillForm.fill_rost)

# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_name))
async def warning_not_name(message: Message):
    await message.answer(text='То, что вы отправили не похоже на имя\n\n'
                              'Пожалуйста, введите ваше имя\n\n'
                              'Если вы хотите прервать рассчёт - '
                              'отправьте команду /cancel')

# Этот хэндлер будет срабатывать, если введен корректная масса тела
# и переводить в состояние ввода роста
@dp.message(StateFilter(FSMFillForm.fill_rost),
            lambda x: x.text.isdigit() and 100 <= int(x.text) <= 300)
async def process_masa(message: Message, state: FSMContext):
    await state.update_data(rost=message.text)
    await message.answer(text='Спасибо! Теперь укажите ваш вес:')
    await state.set_state(FSMFillForm.fill_masa)



# Этот хэндлер будет срабатывать, если во время ввода массы тела
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_rost))
async def warning_not_name(message: Message):
    await message.answer(text='То, что вы отправили не похоже\n\n'
                              'Пожалуйста, введите вашу рост\n\n'
                              'Если вы хотите прервать заполнение анкеты - '
                              'отправьте команду /cancel')

# Этот хэндлер будет срабатывать, если введен корректный рост
@dp.message(StateFilter(FSMFillForm.fill_masa),
            lambda y: y.text.isdigit() and 40 <= int(y.text) <= 200)
async def process_rost_sent(message: Message, state: FSMContext):
    await state.update_data(masa=message.text)

    # Создаем объекты инлайн-кнопок
    yes_news_button = InlineKeyboardButton(text='Да',
                                           callback_data='yes_news')
    no_news_button = InlineKeyboardButton(text='Нет, спасибо',
                                          callback_data='no_news')
    # Добавляем кнопки в клавиатуру в один ряд
    keyboard: list[list[InlineKeyboardButton]] = [
        [yes_news_button,
         no_news_button]]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Редактируем предыдущее сообщение с кнопками, отправляя
    # новый текст и новую клавиатуру
    await message.answer(text='Спасибо!\n\n'
                                          'Остался последний шаг.\n'
                                          'Хотели бы вы узнать ИМТ?',
                                     reply_markup=markup)
    await state.set_state(FSMFillForm.fill_imt)


@dp.callback_query(StateFilter(FSMFillForm.fill_imt),
            Text(text=['yes_news', 'no_news']))
async def process_imt(callback: CallbackQuery, state: FSMContext):
    await state.update_data(imt=callback.data == 'yes_news')
    user_dict[callback.from_user.id] = await state.get_data()
    r = (int(user_dict[callback.from_user.id]["rost"]) / 100) ** 2
    t = int(user_dict[callback.from_user.id]["masa"]) / r
    # user_dict[callback.from_user.id] = await state.get_data()
    if 18.5 <= t < 25:
        await callback.message.answer(text='Ваш вес в норме! Так держать')
    elif 26 <= t < 30:
        await callback.message.answer(text='Избыточный вес')
    elif 30 <= t < 35:
        await callback.message.answer(text='Ожирение I степени')
    elif 36 <= t:
        await callback.message.answer(text='Ожирение II степени')
    await state.update_data(education=callback.data)
    # Завершаем машину состояний
    await state.clear()
    await callback.message.answer(text='Чтобы посмотреть данные вашей '
                                       'анкеты - отправьте команду /showdata')




# Этот хэндлер будет срабатывать на отправку команды /showdata
# и отправлять в чат данные анкеты, либо сообщение об отсутствии данных
@dp.message(Command(commands='showdata'), StateFilter(default_state))
async def process_showdata_command(message: Message):
    await message.answer(text=f'Имя: {user_dict[message.from_user.id]["name"]}\n'
                    f'Масса тела: {user_dict[message.from_user.id]["masa"]}\n'
                    f'Рост: {user_dict[message.from_user.id]["rost"]}\n'
                    f'Ваш ИМТ: {user_dict[message.from_user.id]["imt"]}')





# Этот хэндлер будет срабатывать на любые сообщения, кроме тех
# для которых есть отдельные хэндлеры, вне состояний
@dp.message(StateFilter(default_state))
async def send_echo(message: Message):
    await message.reply(text='Извините, моя твоя не понимать')


# Запускаем поллинг
if __name__ == '__main__':
    dp.run_polling(bot)