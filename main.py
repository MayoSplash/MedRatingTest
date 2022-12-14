#по тз можно использовать реквест
import requests
import os
import json
import datetime


# Возвращает список задач, которые висят на конкретном юзере из общего списка
def get_users_todolist(id, todos):
    result = []
    for todo in todos:
        if 'userId' in todo:
            if id == todo['userId']:
                result.append(todo)
    return result


# Возвращает список выполненных/невыполненных задач в зависимости от status
def get_sorted_titles_by_status(usersTodolist, status: bool):
    result = []
    if len(usersTodolist) == 0:
        return []

    for todo in usersTodolist:
        if status == todo['completed']:
            if len(todo['title']) < 48:
                result.append(todo['title'])
            else:
                result.append(todo['title'][:48] + '...')
    return result


# Возвращает текущее время в том формате, который должен быть указан в отчете по тз
def get_current_datetime():
    current_datetime = datetime.datetime.now()
    result = current_datetime.strftime('%d.%m.%Y %H:%M')
    return result


# Возвращает время создания отчета из файла в том формате, который нужен для именования старых файлов
# Умышленно заменяю двоеточия на точки во времени, чтобы некоторые файловые системы не ругались
# Можно было использовать временя изменения файла path.getmtime(), но мало ли кто-то руками будет менять отчеты
def get_datetime_from_file(filename):
    f = open(filename, 'r')
    lines = f.readlines()
    date, time = (lines[1].split(' ')[-3:-1:])
    date = date.split('.')
    time = time.replace(':', '.')
    result = '{Year}-{Month}-{Day}T{Time}'.format(Year=date[2], Month=date[1], Day=date[0], Time=time)
    return result


# Защищаем от обрыва сети
try:
    usersResponse = requests.get('https://json.medrating.org/users')
    todosResponse = requests.get('https://json.medrating.org/todos')
except ConnectionError:
    raise ConnectionError

users = json.loads(usersResponse.text)
todos = json.loads(todosResponse.text)

for user in users:
    # Формируем построчно отчет в result
    result = 'Отчет для {company}.\n'.format(company=user['company']['name'])
    result += '{name}<{email}> {datetime} \n'.format(name=user['name'],
                                                     email=user['email'],
                                                     datetime=get_current_datetime())
    usersTodolist = get_users_todolist(user['id'], todos)
    result += 'Всего задач: {len}\n\n'.format(len=len(usersTodolist))
    completedTodo = get_sorted_titles_by_status(usersTodolist, True)
    uncompletedTodo = get_sorted_titles_by_status(usersTodolist, False)
    result += 'Завершенные задачи({len}):\n'.format(len=len(completedTodo))
    for todo in completedTodo:
        result += todo + '\n'
    result += '\nОставшиеся задачи({len}):\n'.format(len=len(uncompletedTodo))
    for todo in uncompletedTodo:
        result += todo + '\n'

    # Переводим отчет в разряд старых
    # Если имя занято(например, скрипт запускают чаще раза в минуту), то добавляем секунды в название
    filename = 'tasks/{username}.txt'.format(username=user['username'])
    os.makedirs('tasks', exist_ok=True)
    if os.path.isfile(filename):
        newFilename = 'tasks/old_{username}_{datetime}.txt'.format(username=user['username'],
                                                                   datetime=get_datetime_from_file(filename))
        if os.path.isfile(newFilename):
            second = datetime.datetime.now()
            newFilename = 'tasks/old_{username}_{datetime}.{second}.txt' \
                .format(username=user['username'],
                        datetime=get_datetime_from_file(filename),
                        second=second.second)
        os.rename(filename, newFilename)

    # Пытаемся записать новейший отчет, в случае неудачи откатываем в старый
    try:
        f = open(filename, 'w')
        f.writelines(result)
        f.close()
    except Exception:
        os.rename(newFilename, filename)
        raise Exception
