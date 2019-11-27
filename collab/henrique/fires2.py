
# coding: utf-8

# In[1]:


import plotly.express as px
import csv
from datetime import datetime
import pandas as pd
px.set_mapbox_access_token(open(".\\mapbox_token").read())


# In[7]:


data_ini = -30;
data_fim = 0;
data_aux = '1900-01-01 00:00:00'
strings = []

with open('C:\\Users\\rique\\Desktop\\fires2.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    group = 0
    for row in readCSV:
        if (row[4] == 'True'):
            row[0] = (float(row[0]) ** (1/3))
            row[1] = float(row[1])
            row[2] = float(row[2])
            group += 1
            str_date = row[5]
            data_aux = datetime.strptime(str_date, '%Y-%m-%d').date()
            row.append(0)
            row.append(group)
            strings.append(row)
        if (row[4] == 'False'):
            row[0] = (float(row[0]) ** (1/3))
            row[1] = float(row[1])
            row[2] = float(row[2])
            str_date = row[5]
            if (abs((data_aux - datetime.strptime(str_date, '%Y-%m-%d').date()).days) > data_ini) and (abs((data_aux - datetime.strptime(str_date, '%Y-%m-%d').date()).days) < data_fim):
                row.append((data_aux - datetime.strptime(str_date, '%Y-%m-%d').date()).days)
                row.append(group)
                strings.append(row)
            else:
                del(row)      
        #print(row)
#print(strings)


# In[8]:


#top/down	date	lat	lon	instrument	radius	NaN
df = pd.DataFrame(strings)

df.head()


# # Visualização Completa Estática

# In[9]:


fig = px.scatter_mapbox(df, lat=1, lon=2, color=7, hover_name=8, size=0,
                  color_continuous_scale=px.colors.diverging.RdYlBu, size_max=15, zoom=3, opacity=0.5)
fig.update_layout(mapbox_style="satellite")
fig.show()


# # Visualização Completa Dinâmica (Animada)

# In[24]:


data_ini = -30;
data_fim = 30;
data_aux = '1900-01-01 00:00:00'
strings = []

with open('C:\\Users\\rique\\Desktop\\fires2.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    group = 0
    for row in readCSV:
        if (row[4] == 'True'):
            row[0] = (float(row[0]) ** (1/3))
            row[1] = float(row[1])
            row[2] = float(row[2])
            group += 1
            str_date = row[5]
            data_aux = datetime.strptime(str_date, '%Y-%m-%d').date()
            row.append(0)
            row.append(group)
            strings.append(row)
        if (row[4] == 'False'):
            row[0] = (float(row[0]) ** (1/3))
            row[1] = float(row[1])
            row[2] = float(row[2])
            str_date = row[5]
            if (abs((data_aux - datetime.strptime(str_date, '%Y-%m-%d').date()).days) > data_ini) and (abs((data_aux - datetime.strptime(str_date, '%Y-%m-%d').date()).days) < data_fim):
                row.append((data_aux - datetime.strptime(str_date, '%Y-%m-%d').date()).days)
                row.append(group)
                strings.append(row)
            else:
                del(row)      
        #print(row)
#print(strings) 

df = pd.DataFrame(strings)

fig = px.scatter_mapbox(df, lat=1, lon=2, color=7, hover_name=8, size=0,
                      color_continuous_scale=px.colors.diverging.RdYlBu, size_max=15, zoom=3, opacity=0.5,
                      animation_frame=1)
fig.update_layout(mapbox_style="satellite")
fig.show()


# # Visualização Animada em Grupos
# ## Escolher grupo (ver número acima)

# In[6]:


data_ini = -30;
data_fim = 30;
data_aux = '1900-01-01 00:00:00'
strings = []
eh_primeiro = 'S'
grupo_a_mostrar = 17

def show(strings):
    df = pd.DataFrame(strings)

    fig = px.scatter_mapbox(df, lat=1, lon=2, color=7, hover_name=8, size=0,
                          color_continuous_scale=px.colors.diverging.RdYlBu, size_max=15, zoom=3, opacity=0.5,
                          animation_frame=0)
    fig.update_layout(mapbox_style="satellite")
    fig.show()
    for i in strings:
        strings.remove(i)

with open('C:\\Users\\rique\\Desktop\\fires2.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    group = 0
    for row in readCSV:
        if (row[4] == 'True'):
            row[0] = (float(row[0]) ** (1/3))
            row[1] = float(row[1])
            row[2] = float(row[2])
            group += 1
            if (eh_primeiro != 'S' and grupo_a_mostrar == group-1):
                show(strings)
            str_date = row[5]
            data_aux = datetime.strptime(str_date, '%Y-%m-%d').date()
            row.append(0)
            row.append(group)
            if (grupo_a_mostrar == group):
                strings.append(row)
        if (row[4] == 'False'):
            row[0] = (float(row[0]) ** (1/3))
            row[1] = float(row[1])
            row[2] = float(row[2])
            eh_primeiro = 'N'
            str_date = row[5]
            if (abs((data_aux - datetime.strptime(str_date, '%Y-%m-%d').date()).days) > data_ini) and (abs((data_aux - datetime.strptime(str_date, '%Y-%m-%d').date()).days) < data_fim):
                row.append((data_aux - datetime.strptime(str_date, '%Y-%m-%d').date()).days)
                row.append(group)
                if (grupo_a_mostrar == group):
                    strings.append(row)
            else:
                del(row)
    if (grupo_a_mostrar == 20):
        show(strings)

