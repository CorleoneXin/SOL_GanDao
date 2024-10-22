from PyQt5.QtSql import QSqlDatabase,QSqlQuery

class DBSqlite(object):
    db_file ='tmp.db'
    db_database = None
    def __init__(self, filename):
        self.db_file = filename
        if QSqlDatabase.contains('qt_sql_default_connection'):
            self.db_database = QSqlDatabase.database('qt_sql_default_connection')
        else :
            self.db_database = QSqlDatabase.addDatabase('QSQLITE')
        
        self.db_database.setDatabaseName(filename)
        if not self.db_database.open():
            print('err openDb')
            return
        
    def createTable(self, sql):
        query = QSqlQuery()
        query.exec_(sql)

    def getData(self, sql):
        query = QSqlQuery();
        ret_result = []
        if query.exec(sql):
            col_count = query.record().count();
            while query.next():
                raw_value = []
                for i in range(col_count):
                    raw_value.append(query.value(i))
                ret_result.append(raw_value)
        return ret_result

    def getDB(self):
        return self.db_database

    def insertData(self, sql):
         query = QSqlQuery()
         ret = query.exec_(sql)
         return ret

    def delData(self, sql):
        query = QSqlQuery()
        ret = query.exec_(sql)
        return ret


    def closeDB(self):
        self.db_database.close()

