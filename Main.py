from tkinter import *
from tkinter import ttk
from tkinter import TclError
import os
import requests 
from requests.exceptions import MissingSchema,InvalidSchema,ConnectionError
import sqlite3
from  Parcer import *
import threading
import multiprocessing 
import redis
from datetime import datetime
import time



class DB:

    def __init__(self):
        self.conn = sqlite3.connect("urls.db")
        self.curs = self.conn.cursor()
        self.curs.execute("CREATE TABLE IF NOT EXISTS urls (url text,status text, UNIQUE(url,status))")
        self.conn.commit()

    def set_data(self,url,status):

        self.curs.execute("SELECT * FROM urls")
        previous = self.curs.fetchall()
           
        self.curs.execute("INSERT OR IGNORE INTO urls(url, status) VALUES (?, ?)",(url, status))
        self.conn.commit()

        self.curs.execute("SELECT * FROM urls")
        if self.curs.fetchall() == previous:
            return False
        else:
            return True
            
        
    def get_data(self):
        self.curs.execute("SELECT * FROM urls")
        result = self.curs.fetchall()
        return result

    def update_data(self,url,status,entry_id):
        self.curs.execute("UPDATE urls SET url = ? , status = ? WHERE url = ?",(url,status,url))
        self.conn.commit()
        return True

    def delete_data(self,url):
        self.curs.execute("DELETE FROM urls WHERE url = ?",(url, ))
        self.conn.commit()
        return True


class HomeView:

    def __init__(self,main,db,red,*args, **kwargs):
        self.redis = red
        self.db = db
        self.main = main
        self.button_search = Button(self.main,text="Відслідковувати")
        self.button_search.place(x=225,y=150)
        self.button_search.bind("<Button-1>",self.check_url)

        self.button_starred_page = Button(self.main,text="Подивитися спостережуємі сторінки")
        self.button_starred_page.place(x=150,y=210)
        self.button_starred_page.bind("<Button-1>",self.open_starred_page)

        self.label_main = Label(self.main,text="Введіть посилання на оголошення",font="Roboto,Arial 12",bg="#002F34",fg="#ffffff")
        self.label_main.place(x=150,y=70)

        self.entry_main = Entry(self.main,width=45,cursor="fleur")
        self.entry_main.place(x=115,y=100)


    def check_url(self,event,*args, **kwargs):
        if self.entry_main.get():
            try:
                if requests.get(self.entry_main.get()):
                    
                    parser = Parcer(self.entry_main.get())
                    parser.set_data()
                
                    if self.db.set_data(self.entry_main.get(),parser.get_data()) == False:
                        self.label_warning = Label(self.main,text="Вибачте,однак данне посилання вже занесене",font="Roboto,Arial 12",bg="#002F34",fg="#ff2222")
                        self.label_warning.pack(expand=1)
                        self.entry_main.delete(0,"end")
                        self.main.after(2000,func=lambda *args: self.label_warning.destroy())
                    else:
                        self.label_success = Label(self.main,text="Вітаю,посилання додано у список для спостереження",font="Roboto,Arial 12",bg="#002F34",fg="#ff2222")
                        self.label_success.pack(expand=1)
                        self.entry_main.delete(0,"end")
                        self.main.after(2000,func=lambda *args: self.label_success.destroy())
                else:
                    self.label_main.destroy()
                    self.label_url_error = Label(self.main,text="Ви ввели некоректне посилання",font="Roboto,Arial 12",bg="#002F34",fg="#ff2222")
                    self.label_url_error.place(x=160,y=70)
                    self.entry_main.delete(0,"end")
                    self.main.after(2000,self.show_main_label,self.label_url_error)

            except (MissingSchema,InvalidSchema):
                self.label_main.destroy()
                self.label_url_error = Label(self.main,text="Ви ввели некоректне посилання",font="Roboto,Arial 12",bg="#002F34",fg="#ff2222")
                self.label_url_error.place(x=160,y=70)
                self.entry_main.delete(0,"end")
                self.main.after(2000,self.show_main_label,self.label_url_error)

            except ConnectionError:
                self.label_main.destroy()
                self.label_url_error = Label(self.main,text="У Вас відсутнє з'єднання з інтернетом",font="Roboto,Arial 12",bg="#002F34",fg="#ff2222")
                self.label_url_error.place(x=137,y=70)
                self.main.after(2000,self.show_main_label,self.label_url_error)
                
        else:
            self.label_main.destroy()
            self.label_empty = Label(self.main,text="Поле для посилання не заповнене",font="Roboto,Arial 12",bg="#002F34",fg="#ff2222")
            self.label_empty.place(x=150,y=70)
        
            self.main.after(2000,self.show_main_label,self.label_empty)
    
            

    def show_main_label(self,label_to_delete,*args):
        label_to_delete.destroy()
        self.label_main = Label(self.main,text="Введіть посилання на оголошення",font="Roboto,Arial 12",bg="#002F34",fg="#ffffff")
        self.label_main.place(x=150,y=70)

        



    def open_starred_page(self,event,*args, **kwargs):
        
        self.button_search.destroy()
        self.label_main.destroy()
        self.entry_main.destroy()
        self.button_starred_page.destroy()
        starred = StarredView(self.main,self.db,self.redis)
        
        

class StarredView:

    def __init__(self,main,db,red):
        self.redis = red
        self.main = main
        self.db = db

        self.button_back = Button(self.main,text="Назад")
        self.button_back.place(x=10,y=10)
        self.button_back.bind("<Button-1>",self.back)

        self.get_data_from_db()


    def back(self,event):
        for index in self.main.winfo_children():
            index.destroy()
        HomeView(self.main,self.db,self.redis)


    def get_data_from_db(self):
        self.tree = ttk.Treeview(self.main)
        
        self.tree["columns"] = ("urls","status")
        self.tree.column("#0",width=190)
        self.tree.column("urls",width=190,minwidth=100)
        self.tree.column("status",width=190,minwidth=100)

        self.tree.heading("#0",text="Номер")
        self.tree.heading("urls",text="Посилання")
        self.tree.heading("status",text="Статус")
        
        for index in range(0,len(self.db.get_data())):
            self.tree.insert(parent="",index=index,text="{}".format(index),values=(self.db.get_data()[index][0],self.db.get_data()[index][1]))
            
        
        self.tree.place(x=15,y=65)

            
        self.tree.bind("<Double-1>",self.delete_row)
        self.check_data()


    def delete_row(self,event):
        def controller_yes(event,url):
            self.frame.destroy()
            self.main["bg"] = "#002F32"
            self.db.delete_data(url)
            StarredView(self.main,self.db,self.redis)


        def controller_no(event):
            self.frame.destroy()
            self.main["bg"] = "#002F32"
            StarredView(self.main,self.db,self.redis)

        if not self.tree.selection():
            return
        selected_item = self.tree.selection()[0]
        values = self.tree.item(selected_item,option="text")
        url = self.tree.item(selected_item,option="values")[0]
        self.main["bg"] = "#cdd1ce"
        self.frame = Toplevel(self.main)
        self.frame.geometry("350x250+790+300")
        self.frame.title("Підтвердження")
        self.frame["bd"] = "5px"
        self.frame["bg"] = "#002F32"
        label_attention = Label(self.frame,text="Ви точно хочете видалити запис?")
        label_attention.place(x=45,y=20)
        button_yes = Button(self.frame,text="Так")
        button_no = Button(self.frame,text="Ні")
        button_yes.place(x=45,y=110)
        button_no.place(x=247,y=110)
        button_yes.bind("<Button-1>",lambda event: controller_yes(event,url))
        button_no.bind("<Button-1>",controller_no)
        print(values)
        print(url)

    def check_data(self):
        def update_data(event):
            
            #Preapearing for the upcoming actions
            
            previous = self.db.get_data()
            self.redis.flushall()


            #Function for the deleting of the listbox

            def delete_listbox():
                for inserts in all_inserts:
                    inserts.destroy()
                    StarredView(self.main,self.db,self.redis)
                    
            #Function for the getting data in diffrent proceses

            def thread_get_data(index):
                self.redis.hset("new_data","{}".format(index),Parcer(self.db.get_data()[index][0]).get_data())
                
            #Controller for the previous func

            for index in range(0,len(self.db.get_data())):
                proces = multiprocessing.Process(target=thread_get_data,args=(index,),daemon=True)
                proces.start()
                
            #Script for the showing of the listbox
                
            time.sleep(3)
            for element in self.main.winfo_children():
                element.destroy()
            list_view = Listbox(self.main,height=400)
            list_view["bg"] = '#002F34'
            list_view["fg"] = "#ff2222"
            list_view["bd"] = "5px"

            
            for index_updated in range(0,len(self.db.get_data())):
                if self.redis.hget("new_data",index_updated).decode("utf-8") != self.db.get_data()[index_updated][1]:
                    
                    list_view.insert(END,"Посилання під номером {} змінило статус".format(index_updated))
                    self.redis.hset("inserted_data",index_updated,index_updated)
                else:
                    pass
            
            #Script for the checking whether there is no checked data but if exsists to pack the list_view

            if len(self.redis.hvals("inserted_data")) == 0:
                list_view.destroy()
                label_error = Label(self.main,text="Ні одне з посилань не змінило свій статус",font="Roboto,Arial 12",bg="#002F34",fg="#ff2222")
                label_error.place(x=130,y=10)
                self.main.after(3000,lambda *args:  label_error.destroy())
                StarredView(self.main,self.db,self.redis)
            else:
                list_view.pack(fill=BOTH)
            

            
            #Script for the updating of the data in db

            
            for index_url in range(0,len(self.db.get_data())):
                self.db.update_data(self.db.get_data()[index_url][0],self.redis.hget("new_data",index_url).decode("utf-8"),index_url)
                

            #Actions for the showing starred page

                all_inserts = [list_view]
                self.main.after(8000,delete_listbox)
            
                


        """The making of button and the adding of its bind"""

        self.button_check = Button(self.main,text="Оновити")
        self.button_check.place(x=255,y= 310)
        self.button_check.bind("<Button-1>",update_data)

    
    
        



def main():
    root = Tk()
    db = DB()
    red = redis.Redis("localhost",6379)
    app = HomeView(root,db,red)
    root.geometry('600x400+670+250')
    root.title("OlxTracker")
    root.resizable(False,False)
    root["bg"] = "#002F34"
    root.mainloop()
    
if __name__== "__main__":
    
    main()
    