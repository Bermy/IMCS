import sys
import sqlite3
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QTableWidgetItem
from PyQt5 import uic


class Help(QDialog):
    """Окошко для помощи"""
    def __init__(self):
        super().__init__()
        uic.loadUi('help.ui', self)


class EditItemDialog(QDialog):
    def __init__(self, id, number, name, extra, ok_function):
        """Виджет изменения предметов"""
        super().__init__()
        uic.loadUi('edit_item.ui', self)
        self.name.setText(name)
        self.id = id
        self.number.setText(str(number))
        self.extra.setPlainText(extra)
        self.ok_function = ok_function
        self.ok_btn.clicked.connect(self.ok)
        self.cancel_btn.clicked.connect(self.cancel)

    def cancel(self):
        self.close()

    def ok(self):
        name = self.name.text()
        number = self.number.text()
        extra = self.extra.toPlainText()
        if number.isdigit():
            self.ok_function(self.id, number, name, extra)
            self.close()
        else:
            self.warning.setText('Перепроверьте данные!')


class AddItemDialog(QDialog):
    """Виджет добавления предметов"""
    def __init__(self, ok_function):
        self.ok_function = ok_function
        super().__init__()
        uic.loadUi('add_item_dialog.ui', self)
        self.ok_btn.clicked.connect(self.ok)
        self.cancel_btn.clicked.connect(self.cancel)

    def cancel(self):
        self.close()

    def ok(self):
        quantity = self.quantity.value()
        name = self.name.text()
        num = self.num.text()
        extra = self.extra.toPlainText()
        self.warning.setText(self.ok_function(quantity, name, num, extra))


class DelItemDialog(QDialog):
    """Виджет удаления предметов"""
    def __init__(self, close_function, name, number='', extra=''):
        """
        :param close_function: функция, выполняемая при закрытии (True, если согласие инааче False)
        :param name: Имя предмета
        :param number: Инвентарный номер предмета
        :param extra: доп.информация о предмете
        """
        self.close_function = close_function
        super().__init__()
        uic.loadUi('del_item_dialog.ui', self)
        self.extra.setReadOnly(True)
        self.ok_btn.clicked.connect(self.ok)
        self.cancel_btn.clicked.connect(self.cancel)
        self.name.setText(name)
        self.num.setText(str(number))
        self.extra.setPlainText(extra)

    def cancel(self):
        self.close_function(False)
        self.close()

    def ok(self):
        error = self.close_function(True)
        if not error:
            self.close()
        else:
            self.warning.setText(error)

  
class DataBase:
    def __init__(self, database, table):
        """
        :param database: путь к БД
        :param table: стандартная таблица
        """
        self.table = table
        self.con = sqlite3.connect(database)
        self.cur = self.con.cursor()

    def get_items(self, rule='', columns='*', table=None):
        """

        :param rule: правило отбора
        :param columns: поля
        :param table: таблица для запроса, если нет, то стандартная
        :return: кортеж кортежей с результатами запросов
        """
        rule = ' WHERE ' + rule if rule else ''
        columns = '*' if not columns else columns
        table = self.table if not table else table
        return self.cur.execute(f"SELECT {columns} FROM {table}{rule}").fetchall()

    def exec(self, requset):
        self.cur.execute(requset)
        self.con.commit()


class AbstractDatabaseWidget(QWidget):
    """Абстрактный виджет с таблицей из базы данных"""
    def __init__(self, database, table):
        super().__init__()
        self.database = DataBase(database, table)

    def set_tableWidget(self, table):
        # Метод для указывания виджета-таблицы. Нехорошо же, что всё ломается, если не существует tableWidget?
        self.tableWidget = table

    def get_allocated_items_indexes(self):
        """
        Возвращает множество всех выделенных индексов
        :return: множество индексов (По предварительным опытам - в правильной последовательности)
        """
        indexes = set(map(lambda x: x.row(), self.tableWidget.selectedIndexes()))
        return indexes

    def get_items(self, indexes, columns=(0,)):
        """
        Для получения значений из таблицы
        :param indexes: коллекция int индексов строк
        :param columns: коллекция int индексов колонок
        :return: list с list-ами значений выбранных колонок
        """
        indexes = tuple(indexes)
        columns = tuple(columns)
        result = []
        for index in indexes:
            result.append(tuple(self.tableWidget.model().index(int(index), int(column)).data() for column in columns))
        return result

    def show_in_table(self, rule='', column_sort=1):
        """
        Метод для отображения в таблице
        :param rule: правило отбора
        :param column_sort: номер столбца для сортировки
        """
        self.tableWidget.setRowCount(0)
        result = self.database.get_items(rule=rule)
        result = sorted(list(result), key=lambda x: x[column_sort])
        for row, items in enumerate(result):
            self.tableWidget.setRowCount(row + 1)
            for column, item in enumerate(items):
                self.tableWidget.setItem(row, column, QTableWidgetItem(str(item) if item else ''))

    def exec(self, request):
        # Метод для запроса в БД
        self.database.exec(request)

    def select_from_db(self, columns='*', rule=None, table=None):
        return self.database.get_items(rule, columns, table)


class MainWindow(AbstractDatabaseWidget):
    def __init__(self):
        self.item_id = None
        super().__init__('database.sqlite', 'items')
        uic.loadUi('main.ui', self)

        self.setWindowTitle('СКПИ им. Жегалова 0.2.1')
        self.item_edit.clicked.connect(self.item_edit_dialog)
        self.del_inventory_btn.clicked.connect(self.del_inventory)
        self.add_inventory_btn.clicked.connect(self.add_inventory)
        self.show_inventory_btn.clicked.connect(self.show_all)
        self.show_items_in_storage_btn.clicked.connect(self.show_items_in_storage)
        self.show_on_hands_btn.clicked.connect(self.show_on_hands)
        self.in_btn.clicked.connect(self.coming)
        self.out_btn.clicked.connect(self.out)
        self.search_btn.clicked.connect(self.search)
        self.search_in_table_in_btn.clicked.connect(self.search_in_table_in)

        self.tableWidget.setColumnHidden(0, True)
        self.show_in_table(column_sort=1)
        self.table_now = self.show_all
        self.search_in_table_out_btn.clicked.connect(self.search_in_table_out)
        self.take_in_table_out_btn.clicked.connect(self.take_in_table_out)
        self.take_in_table_in_btn.clicked.connect(self.take_in_table_in)
        self.help_btn.clicked.connect(self.help)
        self.tabWidget.currentChanged.connect(self.del_item_id)

    def keyPressEvent(self, event):
        # переназначение клавиш
        if event.key() == Qt.Key_F1:
            self.help()
        if int(event.modifiers()) == Qt.ControlModifier:
            if event.key() == Qt.Key_Q:
                if self.take_in_table_in():
                    self.tabWidget.setCurrentIndex(0)
            elif event.key() == Qt.Key_E:
                if self.take_in_table_out():
                    self.tabWidget.setCurrentIndex(1)

    def help(self):
        help = Help()
        help.exec()

    def out(self):
        # Метод для возврата предмета
        if self.item_id:
            if self.owner_out.text():
                self.exec(f'''UPDATE items SET owner = "{self.owner_out.text()}"
                                            WHERE id = {self.item_id} AND owner is Null''')
                self.show_items_in_storage()
            else:
                self.out_warning.setText('Укажите принимающего')

    def coming(self):
        # Метод для взятия со склада
        if self.item_id:
            self.exec(f'UPDATE items SET owner = Null WHERE id = {self.item_id} AND NOT owner is Null')
            self.show_on_hands()

    def take_in_table_in(self):
        # Для клавиши Вернул - Взять из Таблицы
        return self.take_in_table(out=False)

    def take_in_table_out(self):
        # Для клавиши Взял - Взять из Таблицы
        return self.take_in_table(out=True)

    def take_in_table(self, out):
        # Общий метод для клавиш "Взять из таблицы"
        self.del_item_id()
        items = self.get_allocated_items_indexes()
        if len(items) == 1:
            item = self.get_items(items, columns=(i for i in range(5)))
            id, inventory_num, name, owner, extra = item[0]
            if not inventory_num.isdigit():
                return None
            if not out and owner:
                self.inventory_in.setText(str(inventory_num))
                self.name_item_in.setText(name)
                self.name_owner_in.setText(owner)
                self.item_id = id
            elif out and not owner:
                self.inventory_number_out.setText(str(inventory_num))
                self.name_out.setText(name)
                self.item_id = id

    def search_in_table_in(self):
        # Метод для кнопки Вернул-Найти в Таблице
        inventory = self.inventory_in.text()
        item_name = self.name_item_in.text()
        name_owner = self.name_owner_in.text()
        self.search_in_table(True, inventory, item_name, name_owner)

    def search_in_table_out(self):
        # Метод для кнопки Взял-Найти в Таблице
        name_owner = None
        inventory_num = self.inventory_number_out.text()
        if not inventory_num.isdigit():
            return None
        item_name = self.name_out.text()
        self.search_in_table(False, inventory_num, item_name, name_owner)

    def search_in_table(self, no, inventory_number, item_name, name_owner):
        # Общий метод для кнопок "Найти в таблице"
        if not inventory_number.isdigit():
            return None
        no = 'NOT' if no else ''
        if inventory_number != '':
            self.show_in_table(f'inventory_number = {inventory_number} AND {no} owner is Null')
        elif item_name and name_owner:
            self.show_in_table(f'''(name like "%{item_name}%" OR owner like "%{name_owner}%")
                                        AND {no} owner is Null''')
        elif item_name:
            self.show_in_table(f'''name like "%{item_name}%" AND {no} owner is Null''')
        elif name_owner:
            self.show_in_table(f'''owner like "%{name_owner}%" AND NOT owner is Null''')

    def show_items_in_storage(self, *arg, rule=''):  # Здесь и ниже: *arg нужно, чтобы Qt не совал что попало в rule
        # Показать предметы на складе
        rule = 'owner is NULL' if not rule else f'owner is NULL AND {rule}'
        self.show_in_table(rule)
        self.table_now = self.show_items_in_storage
        self.list_label.setText('Инвентарь на Складе')

    def show_all(self, *arg, rule=''):
        # Показать весь список предметов
        rule = rule if rule else ''
        self.show_in_table(rule)
        self.table_now = self.show_all
        self.list_label.setText('Весь список')

    def show_on_hands(self, *arg, rule=''):
        # Показать предметы на руках
        rule = 'NOT owner is NULL' if not rule else 'NOT owner is NULL AND ' + rule
        self.show_in_table(rule)
        self.table_now = self.show_on_hands
        self.list_label.setText('На руках')

    def del_inventory(self):
        # Метод для кнопки Удалить Инвентарь
        ids = self.get_items(indexes=self.get_allocated_items_indexes())
        if len(ids) == 1:
            self.item_id = ids[0][0]
            item = self.select_from_db(columns="name, inventory_number, extra", rule=f'id = {self.item_id}')[0]
            name, num, extra = item
            dialog = DelItemDialog(self.del_inventory_db, name, num, extra)
            dialog.exec()

    def del_inventory_db(self, delete):
        # Метод для Удалить Инвентарь -> Удалить
        if delete:
            self.exec(f'DELETE from items WHERE id = {self.item_id}')
            self.del_item_id()
            self.table_now()
        self.del_item_id()

    def add_inventory(self):
        # вызывает диалог для добавления элементов
        dialog = AddItemDialog(self.add_inventory_db)
        dialog.exec()

    def add_inventory_db(self, quantity, name, num, extra):
        # проверяет корректность ввода и добавляет элементы
        try:
            num = int(num)
        except Exception:
            return None
        for i in range(quantity):
            if self.select_from_db(rule=f'inventory_number = {i + num}'):
                return f'Инвентарный номер {num + i} уже занят!'
        if name and num:
            try:
                num = int(num)
            except ValueError:
                return 'Укажите число в инвентарном номере'
            for _ in range(quantity):
                self.exec(f'INSERT INTO items(inventory_number, name, extra) VALUES({num},"{name}","{extra}")')
                self.table_now()
                num += 1
            return None
        if name:
            return 'укажите инвентарный номер'
        elif num:
            return 'Укажите наименовение'
        return 'Перепроверьте данные: неизвестная ошибка'

    def search(self):
        # выводит результаты поиска
        text = (self.search_text.text()).strip()
        if text:
            rule = self.comboBox.currentIndex()
            if rule == 0:
                rule = 'inventory_number'
                try:
                    int(text)
                    return self.table_now(rule=f'{rule} = {text}')
                except Exception:
                    return None
            elif rule == 1:
                rule = 'name'
            else:
                rule = 'owner'
            rule = f' {rule} LIKE "%{text}%"'
            self.table_now(rule=rule)
            self.list_label.setText('Поиск')

    def item_edit_dialog(self):
        item = self.get_allocated_items_indexes()
        if not item:
            return None
        item = self.get_items(item, tuple(i for i in range(5)))[0]
        id = item[0]
        number = item[1]
        if not number.isdigit():
            return None
        name = item[2]
        extra = item[4]
        dialog = EditItemDialog(id, number, name, extra, self.item_edit_db)
        dialog.exec()

    def item_edit_db(self, id, number, name, extra):
        self.exec(f'UPDATE items SET inventory_number = {number}, name = "{name}", extra = "{extra}" WHERE id = {id}')

    def del_item_id(self):
        self.item_id = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    app.exec()
    sys.exit()
