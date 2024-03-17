#include libraries of kivy for gui
from kivy.app import App #base class for creating and starting kivy applications
from kivy.uix.widget import Widget #Widget class for all ui classes to inherit from
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stacklayout import StackLayout
from kivy.graphics import Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label 
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox 
from kivy.properties import StringProperty,BooleanProperty


#For notes data management
import sqlite3
import os
script_dir = os.path.abspath( os.path.dirname( __file__ ) )




def removeText(*tfs):
    for textfield in tfs:
        textfield.select_all()
        textfield.delete_selection()
        
#classes to manage ui components          
class InsertNote(BoxLayout): #text field for creating object in todo list

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.removeText=removeText
    def fetchTagInput(self):
        tagText=self.ids['assignTag'].text
        if tagText ==None or  tagText =="":
            return
        try:
            self.ids['chosenTags'].addTagItem(TagItem(tagName=tagText,color="blue",activate=True))
            #self.ids['reuseTag'].dropDown.add_widget(TagItem(tagName=tagText,color="blue",activate=True))
        except Exception as e:
            print(e)
        
        
    def addNote(self):
        try:
            #collect content from Text input and store in variable
            noteTitle=self.ids.enterTitle
            noteCont= self.ids.enterNote #Indexing starts from bottom

            noteTags=[]
            # fetch tags selected in tags list
            for tItem in self.ids['chosenTags'].ids['tagList']:
                if tItem.children[0].active:         # checkbox is selected
                    noteTags.append(tItem.tagName)
                
            
            #uSING tags as text for now ,maybe will convert to indexed field that will act like a key to find same hash value notes
            
            #note insert query string
            query="INSERT INTO notes(title,content) VALUES (?,?)"
            parameters=(noteTitle.text,noteCont.text)
            #execute the query
            cursor.execute(query,parameters)
            cursor.execute("SELECT MAX(id) FROM notes")
            val=1
            for maxId in cursor:
                val=maxId[0]
            if len(noteTags) != 0:
                for tag in noteTags:
                    tagQry="INSERT INTO tags(id,tagName) VALUES(?,?)"
                    tagParameter=(val,tag)
                    cursor.execute(tagQry,tagParameter)
            #after all notes have been edited display status of operation
            noteListBox=self.parent.parent.ids["noteListParent"]
            #In sqlite insertion query does not return inserted rows and result is typically empty
            conn.commit()                    
            noteListBox.addListItem(title=noteTitle.text,content=noteCont.text)
            
        except Exception as e:
            print("Error in inserting data and creating new noteList Item widget rollback called")
            conn.rollback()
            print(e)
            
    
        
class ListItem(BoxLayout):# Note items
    def __init__(self,noteTitle,noteContent,*tags,**kwargs):
        self.title=noteTitle
        self.content=noteContent        
        super().__init__(**kwargs)
    
class DisplayList(BoxLayout): #for displaying list of Notes that are inserted
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.removeText=removeText

    def addListItem(self,title,content,*tags):   
        self.ids['noteList'].add_widget(ListItem(noteTitle=title,noteContent=content))
        self.ids['noteList'].height=len(self.ids['noteList'].children)*100
           
    
    def cleanNotesList(self):
        #First remove any previously existing note List Items
        self.ids['noteList'].clear_widgets()
    def executeQuery(self,command,title,*tags):
        
        if command ==0:#display notes filtered by search title
            query="SELECT * FROM notes WHERE title=(?)"
            parameters=(title,)
        elif command==1 :
            
            parameters=[]
            for tItem in self.parent.parent.ids['tgDrop'].dropDown.container.children:
                if tItem.children[0].active:         # checkbox is selected
                    parameters.append(tItem.tagName)
            if len(parameters)!=0 :
                query="SELECT  * FROM notes JOIN tags ON notes.id= tags.id WHERE tags.tagName  in ("+"?,"*(len(parameters)-1) +"?) GROUP BY notes.id" # Perform a separate tag query if required to display associated tags with the notes in the list
            else:
                query="SELECT * FROM notes JOIN tags ON notes.id= tags.id WHERE tags.tagName  in ()"
                
            
        else: # display all notes
            query="SELECT * FROM  notes"
            parameters=()
        queryResult=cursor.execute(query,parameters)
        return queryResult

    def display(self,queryResult):
        notesList=self.ids.noteList #box layout section        
        for row in queryResult:
            try:
                self.addListItem(title=row[1],content=row[2])
            except Exception as e:
                print("Error in adding widget")
                print(e)
    def searchCall(self,criteria,title,*tags):
        result=self.executeQuery(criteria,title,*tags)
        self.cleanNotesList()
        self.display(result)
    def resetSelections(self):
        for tItem in self.parent.parent.ids['tgDrop'].dropDown.container.children:
            tItem.ids['cb'].active= False
            
class TagItem(BoxLayout):
    tagName=StringProperty("") # DEFINE PROPERTIES BEFORE PASSING THEM IN CONSTRUCTOR PARAMETERS IF NOT DEFINED UNDER KV FILE
    status=BooleanProperty(False)
    color=StringProperty("black")
    activate=BooleanProperty(False)
    def __init(self,tagName,color="black",activate=False,**kwargs):
        super(TagItem,self).__init__(**kwargs)
        self.tagName=tagName
        self.color=color
        self.activate=activate
        
    def checkbox_click(self,instance,value):
        self.status=value
class TagsDropDown(BoxLayout):
    buttonName=StringProperty("")
    def __init__(self,buttonName="Choose",*args,**kwargs):
        super(TagsDropDown,self).__init__(*args,**kwargs)
        self.dropDown=DropDown()
        self.tags={} # dictionary of status
        self.buttonName=buttonName
        self.mainButton=Button(text=self.buttonName)
        self.mainButton.bind(on_press=self.displayTags)
        self.mainButton.bind(on_release=self.dropDown.open)
        self.add_widget(self.mainButton)

        
    def displayTags(self,instance):
    # to keep status of previously checked and unchecked  tags consistent 
        if self.tags == {}:
            self.getTags(instance)
        #fix call where new tag addition is removed by dropDown.clear widgets function call
                    
    def getTags(self,instance):
        try:
            findTagQry="SELECT DISTINCT tagName FROM tags "
            self.dropDown.clear_widgets()
            qryResult=cursor.execute(findTagQry)
            for row in qryResult:
                self.tags[row]= False
                tI=TagItem(tagName=row[0])
                self.dropDown.add_widget(tI)  
        except exception as e:
            print(e)

class AssociatedTags(ScrollView):
    def __init__(self,*args,**kwargs):
        super(AssociatedTags,self).__init__(*args,**kwargs)
    def addTagItem(self,tagItem):   
        self.ids['tagList'].add_widget(tagItem)
        self.ids['tagList'].width=len(self.ids['tagList'].children)*15
    
    
class NoteManager(BoxLayout):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.removeText=removeText
    
    
class NotesApp(App):
    def __init__(self):
        super().__init__()
        self.manager=None
    def build(self):
        
        self.manager= NoteManager()
        return self.manager

    def on_start(self):
        global conn
        global cursor
        conn = sqlite3.connect("./notes.fnote")
        cursor= conn.cursor()
        createQry= "CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,title TEXT, content TEXT)"
        tagQry="CREATE TABLE IF NOT EXISTS tags(id INTEGER ,tagName TEXT,FOREIGN KEY(id) REFERENCES notes(id) ON DELETE CASCADE ON UPDATE NO ACTION ,PRIMARY KEY(id,tagName))"
        cursor.execute(createQry)
        cursor.execute(tagQry)
        qr=self.manager.ids['noteListParent'].executeQuery(command=2,title=None)
        self.manager.ids['noteListParent'].display(qr)
        
    def on_stop(self):
        cursor.close()
        conn.close()
if __name__ == '__main__':
    NotesApp().run()



