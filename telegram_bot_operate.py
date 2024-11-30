import telebot

def telegram_bot_operate(token,
                         check_archive_= (lambda x: print("error")),
                         check_file_= (lambda x: print("error")),
                         check_mess_= (lambda x: print("error"))):
  bot = telebot.TeleBot(token);

  # Обработчики команд
  @bot.message_handler(commands=['start'])
  def handle_start(message):
      bot.send_message(message.chat.id, "Этот бот создан, для проверки ваших проектов \n Можно прислать архив, файл или написать код в сообщении");

  @bot.message_handler(commands=['review'])
  def handle_start(message):
      bot.send_message(message.chat.id, "Для отправки кода на ревью можно:\n- Просто кидать архив с проектом\n- Кинуть отдельный файл\n- Скинуть текстом код");


  # Обработчик текста и файлов

  @bot.message_handler(content_types=['text', 'document'])
  def handle_message(message):

    # Ответ на текстовое сообщение
    if message.text:
      bot.send_message(message.chat.id, 'Код получен, идёт анализ');
      output = check_mess_(message.text);
      bot.send_document(message.chat.id,output)

    #file
    if message.document:
        bot.send_message(message.chat.id, 'Файл получен, идёт анализ');
        file_name = message.document.file_name;
        file_info = bot.get_file(message.document.file_id);

        downloaded_file = bot.download_file(file_info.file_path);

        if(file_name.split('.')[len(file_name.split('.')) - 1] == "zip"):
            output = check_archive_(downloaded_file);
            bot.send_document(message.chat.id,output)
        else:
            output = check_file_(downloaded_file);
            bot.send_document(message.chat.id,output)

  bot.polling(none_stop=True);
