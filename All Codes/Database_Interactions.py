# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 15:06:16 2019

@author: User
"""

import sqlite3
import pandas as pd


class DB_Operator():
    def __init__(self, DB_name):
        self.DB = DB_name + '.db'
        self.conn = sqlite3.connect(self.DB)
        self.c = self.conn.cursor()

    def create_new_table(self, table_name, columns, var_type = 'text'):
        command = 'CREATE TABLE '
        command = command + table_name + ' ('
        if var_type == 'text':
            for items in columns:
                command += items + ' text, '
            command = command[:-2] +')'
            
        elif type == 'numbers':
            for items in columns:
                command += items + ' double, '
            command = command[:-2] +')'
            
        self.c.execute(command)
        
    def DF_to_new_table(self, Dataframe, tablename):
        Dataframe.to_sql(tablename, con = self.conn, if_exists = 'append')

    def read_entire_table(self, tablename):
        command = 'select * from ' + tablename
        DF = pd.read_sql(command, con = self.conn)        
        return DF
    
    def Select_rows(self, tablename, find, by = 'Asset'):
        command = 'SELECT * FROM ' + tablename +' WHERE '
        command = command + by + ' =?'
        Collect = []
        for items in find:
            ite = (items,)    
            self.c.execute(command, ite)
            col_name_list = [tuple[0] for tuple in self.c.description]
            rows = self.c.fetchall()
            Collect.extend(rows)
        Output = pd.DataFrame(Collect, columns = col_name_list)
        return Output
        
    def disconnect(self):
        self.c.close()
        



