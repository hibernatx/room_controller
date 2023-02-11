import sqlite3




class Db:
    __db = None

    def __init__(self, dbfile):
        self.__db = sqlite3.connect(dbfile)
        self.__exec_sql(""" CREATE TABLE IF NOT EXISTS hosts (
                                        node_id text PRIMARY KEY UNIQUE NOT NULL,
                                        mac_addr text UNIQUE NOT NULL,
                                        hostname text UNIQUE NOT NULL
                                    ); """)

    def __exec_sql(self, sql, params=None):
        try:
            c = self.__db.cursor()
            if params:
                res = c.execute(sql, params)
            else:
                res = c.execute(sql)
            self.__db.commit()
            return res.fetchall()
        except Exception as e:
            return e

    def get_hosts(self, hosts=None):
        query = "SELECT * FROM hosts"
        if hosts:
            query += " WHERE "
            query += " OR ".join(["node_id = ?" for i in hosts])
        return self.__exec_sql(query, hosts)

    def add_host(self, node_id, hostname, mac_address):
        query = "INSERT INTO hosts VALUES (?,?,?)"
        self.__exec_sql(query, (node_id, mac_address, hostname))
        return 'ok'

    def remove_host(self, node_id):
        query = "DELETE FROM hosts WHERE node_id = ?"
        self.__exec_sql(query, [node_id])
        return 'ok'

    def update_host(self, node_id, hostname=None, mac_address=None):
        if hostname and mac_address:
            query = "UPDATE hosts SET hostname = ?, mac_addr = ?"
            self.__exec_sql(query, [hostname, mac_address])
        elif mac_address:
            query = "UPDATE hosts SET mac_addr = ?"
            self.__exec_sql(query, [mac_address])
        elif hostname:
            query = "UPDATE hosts SET hostname = ?"
            self.__exec_sql(query, [hostname])
        return 'ok'

    def __del__(self):
        self.__db.close()


if __name__ == '__main__':
    mydb = Db('hosts.db')
    mydb.addhost('A1', '1.1.1.1', '00-D8-61-9F-0E-52')
    mydb.addhost('A2', '1.0.0.1', '00-D8-61-9F-0E-53')
    mydb.addhost('A3', '0.0.0.0', '00-D8-61-9F-0E-54')
    print(mydb.gethosts())
