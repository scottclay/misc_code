''' Create a simple stocks correlation dashboard.

Choose stocks to compare in the drop down widgets, and make selections
on the plots to update the summary and histograms accordingly.

.. note::
    Running this example requires downloading sample data. See
    the included `README`_ for more information.

Use the ``bokeh serve`` command to run the example by executing:

    bokeh serve stocks

at your command prompt. Then navigate to the URL

    http://localhost:5006/stocks

.. _README: https://github.com/bokeh/bokeh/blob/master/examples/app/stocks/README.md

'''


#import pandas as pd
#
#df = pd.read_excel('notebooks/output.xlsx', sheetname='table1')
#print(df.head(5))
#quit()



from os import getenv
import pymssql
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pylab
pd.options.mode.chained_assignment = None  # default='warn'

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa


server = "188.95.129.233"
user = "Oak"
password = "o4kconsult"
port = "1433"

conn = pymssql.connect(server, user, password,port=port)



def miss_matched_entries(df_to_clean):
    missing_entries = df_to_clean[pd.isnull(df_to_clean.OwnerID_y) == True]
    cut_nans = df_to_clean.drop(missing_entries.index)
    return cut_nans, missing_entries

def get_monthly_rent(df):
    df['Monthly Rent'] = np.nan
    df.loc[df.strRentalFrequency == 'Monthly', 'Monthly Rent'] = df.dblRentalAmount
    df.loc[df.strRentalFrequency == 'Three Monthly', 'Monthly Rent'] = df.dblRentalAmount/3.0
    df.loc[df.strRentalFrequency == 'Six Monthly', 'Monthly Rent'] = df.dblRentalAmount/6.0
    df.loc[df.strRentalFrequency == 'Annually', 'Monthly Rent'] = df.dblRentalAmount/12.0
    return df
    

def get_fee(df):
    df['Cost'] = np.nan
    df.loc[df.strServiceProvided == 'Managed', 'Cost'] = 295.00
    df.loc[df.strServiceProvided == 'Rent Collection Only', 'Cost'] = 295.00
    df.loc[(df.strServiceProvided == 'Let Only')&(df['Tenancy Length']<=11.0), 'Cost'] = np.maximum(0.50*df.dblRentalAmount,350.00)
    df.loc[(df.strServiceProvided == 'Let Only')&(df['Tenancy Length']>=12.0), 'Cost'] = np.maximum(0.75*df.dblRentalAmount,500.00)
    return df

	

def get_data(output_filename,start_date='2017-11-01', end_date = '2017-12-01'):
    stmt = "SELECT * FROM dbo.Oak_Tenancy WHERE dteOccupiedDate >= '"+start_date+"' AND dteOccupiedDate < '"+end_date+"'"
    df1 = pd.read_sql(stmt,conn)
    
    true_owner = df1[df1.blnCurrentOwner == False].index
    df1 = df1.drop(df1.index[true_owner])
    df1 = df1.reset_index(drop=True)

    
    stmt = "SELECT * FROM dbo.Oak_LiveTransactions WHERE Date >= '2017-01-01' AND Date < '2018-02-01'"
    df = pd.read_sql(stmt,conn)
    
    checked_properties = df[df.blnDeleted == True].index   #identify the rows marked as deleted in this spreadsheet
    df2 = df.drop(df.index[checked_properties]) #create a new dataframe without the deleted entries
    df2 = df2.reset_index(drop=True) #reset the index to account for dropped rows
    
    df2.Description = df2.Description.str.lower()

    df3 = df2[(df2.Description.str.contains('letting')) & (df2.Type == 'PLI')]
    
    merged_df = pd.merge(df1, df3, on="TenancyID", how = 'left')
    
    merged_df.TenancyID = merged_df.TenancyID.astype(str).str.replace('-',' - ')
    
    merged_df['O_ID_B'] = np.where(merged_df['OwnerID_x'] == merged_df['OwnerID_y'], 1, 0)   
    merged_df['P_ID_B'] = np.where(merged_df['PropertyID_x'] == merged_df['PropertyID_y'], 1, 0) 
    
    merged_df = merged_df.drop(['dteMoveOutDate'], axis=1)
    
    mod_df, missing = miss_matched_entries(merged_df)
	
    mod_df['Tenancy Length'] = ((mod_df['dteVacatingDate'] - mod_df['dteOccupiedDate']) / np.timedelta64(1, 'M')).round(0)
    mod_df = get_monthly_rent(mod_df)
    mod_df = get_fee(mod_df)
    mod_df['Potential Interest'] = np.where(mod_df.Description != "letting fee", 1, 0)
    mod_df['Error'] = np.where(mod_df['Cost']!=mod_df['Net'], 1, 0)
	
    #print(mod_df.dtypes)
    #print(missing.dtypes)
    #print(mod_df.head(5))
    #print(missing.head(5))
    #print(mod_df.columns())
    #print(missing.columns())
	
    mod_df['OwnerID_x'] = mod_df['OwnerID_x'].astype(str)
    mod_df['TenancyID'] = mod_df['TenancyID'].astype(str)
    mod_df['PropertyID_x'] = mod_df['PropertyID_x'].astype(str)
    mod_df['OwnerID_y'] = mod_df['OwnerID_y'].astype(str)
    mod_df['PropertyID_y'] = mod_df['PropertyID_y'].astype(str)

    missing['OwnerID_x'] = missing['OwnerID_x'].astype(str)
    missing['TenancyID'] = missing['TenancyID'].astype(str)
    missing['PropertyID_x'] = missing['PropertyID_x'].astype(str)
    missing['OwnerID_y'] = missing['OwnerID_y'].astype(str)
    missing['PropertyID_y'] = missing['PropertyID_y'].astype(str)	
	
	
    writer = pd.ExcelWriter(output_filename+'.xlsx')
    mod_df.to_excel(writer,'Move_ins')
    missing.to_excel(writer,'Missing')
    writer.save()
    
    return mod_df, missing


def get_stats(output_filename,start_date='2017-11-01', end_date = '2017-12-01'):
	mod_df, missing_df = get_data(output_filename, start_date=start_date, end_date = end_date)
	output_df=mod_df.drop(['OwnerID_x','PropertyID_x','OwnerID_y','PropertyID_y','strLengthOfTenancy','Date','blnCurrentOwner','blnVacant','blnDeleted','dteExtensionDate','Type'], axis=1)
	table1 = output_df[(output_df.Error == 1)&(output_df['Potential Interest']==0)][['dteOccupiedDate','TenancyID','strServiceProvided','Monthly Rent','Tenancy Length','Net','Cost' ]]
	table2 = output_df[(output_df.Error == 1)&(output_df['Potential Interest']==1)][['dteOccupiedDate','TenancyID','strServiceProvided','Monthly Rent','Tenancy Length','Net','Cost','Description' ]]
	table3 = missing_df[missing_df['Tenancy Status']=='Active'][['dteOccupiedDate','TenancyID','strServiceProvided','dblRentalAmount','Tenancy Status']]
	table4 = missing_df[missing_df['Tenancy Status']!='Active'][['dteOccupiedDate','TenancyID','strServiceProvided','dblRentalAmount','Tenancy Status']]
	print("total, correct, incorrect, missing, "+output_filename)
	print(len(output_df) + len(missing_df), len(output_df[output_df.Error == 0]), len(output_df[output_df.Error == 1]), len(missing_df))
	

'''
print("starting")
get_stats('Jan17_Data', start_date='2017-01-01', end_date = '2017-02-01')
get_stats('Feb17_Data', start_date='2017-02-01', end_date = '2017-03-01')
get_stats('Mar17_Data', start_date='2017-03-01', end_date = '2017-04-01')
get_stats('Apr17_Data', start_date='2017-04-01', end_date = '2017-05-01')
get_stats('May17_Data', start_date='2017-05-01', end_date = '2017-06-01')
get_stats('Jun17_Data', start_date='2017-06-01', end_date = '2017-07-01')
get_stats('Jul17_Data', start_date='2017-07-01', end_date = '2017-08-01')
get_stats('Aug17_Data', start_date='2017-08-01', end_date = '2017-09-01')
get_stats('Sep17_Data', start_date='2017-09-01', end_date = '2017-10-01')
get_stats('Oct17_Data', start_date='2017-10-01', end_date = '2017-11-01')
get_stats('Nov17_Data', start_date='2017-11-01', end_date = '2017-12-01')
get_stats('Dec17_Data', start_date='2017-12-01', end_date = '2018-01-01')

get_stats('Jan18_Data', start_date='2018-01-01', end_date = '2018-02-01')
quit()

'''
   
try: 
	mod_df = pd.read_excel('Nov17_Data.xlsx', sheet_name='Move_ins')
	missing_df = pd.read_excel('Nov17_Data.xlsx', sheet_name='Missing')	
except FileNotFoundError:
	#mod_df, missing_df = get_data()
	exit()

output_df=mod_df.drop(['OwnerID_x','PropertyID_x','OwnerID_y','PropertyID_y','strLengthOfTenancy','Date','blnCurrentOwner','blnVacant','blnDeleted','dteExtensionDate','Type'], axis=1)
table1 = output_df[(output_df.Error == 1)&(output_df['Potential Interest']==0)][['dteOccupiedDate','TenancyID','strServiceProvided','Monthly Rent','Tenancy Length','Net','Cost' ]]
table2 = output_df[(output_df.Error == 1)&(output_df['Potential Interest']==1)][['dteOccupiedDate','TenancyID','strServiceProvided','Monthly Rent','Tenancy Length','Net','Cost','Description' ]]
table3 = missing_df[missing_df['Tenancy Status']=='Active'][['dteOccupiedDate','TenancyID','strServiceProvided','dblRentalAmount','Tenancy Status']]
table4 = missing_df[missing_df['Tenancy Status']!='Active'][['dteOccupiedDate','TenancyID','strServiceProvided','dblRentalAmount','Tenancy Status']]


print("output_df = ",len(output_df))
print("missing_df = ",len(missing_df))
print("correct = ",len(output_df[output_df.Error == 0]))
print("incorrect = ",len(output_df[output_df.Error == 1]))

'''
env = Environment(loader=FileSystemLoader('./templates/'))
template = env.get_template("report_live.html")
template_vars = {"title" : "Linley and Simpson Analysis - November",
                 "title1": "Detected errors between November move ins and Live transactions",
                 "national_pivot_table1": table1.to_html(index=False),       
                 "title2": "Potential errors! Check the Description! ",
                 "national_pivot_table2": table2.to_html(index=False),   
                 "title3": "ACTIVE tenancies with NO entry in Live Transactions",
                 "national_pivot_table3": table3.to_html(index=False),   
                 "title4": "PROBLEMATIC tenancies with NO entry in Live Transactions",
                 "national_pivot_table4": table4.to_html(index=False),   
                }
html_out = template.render(template_vars)
with open('./reports/nov_live.pdf', "w+b") as out_pdf_file_handle:
    pisa.CreatePDF(
        src=html_out,  # HTML to convert
        dest=out_pdf_file_handle)  # File handle to receive result

'''
#############################################################################

from random import random

from bokeh.layouts import column, row
from bokeh.models import Button
from bokeh.palettes import RdYlBu3

from bokeh.plotting import figure, curdoc
# create a plot and style its properties


#############################################################################
# Plot click box
'''
p = figure(x_range=(0, 100), y_range=(0, 100), toolbar_location=None)
p.border_fill_color = 'black'
p.background_fill_color = 'black'
p.outline_line_color = None
p.grid.grid_line_color = None

# add a text renderer to our plot (no data yet)
r = p.text(x=[], y=[], text=[], text_color=[], text_font_size="20pt",
           text_baseline="middle", text_align="center")

i = 0

ds = r.data_source
'''
# create a callback that will add a number in a random location
def callback():
    global i

    # BEST PRACTICE --- update .data in one step with a new dict
    new_data = dict()
    new_data['x'] = ds.data['x'] + [random()*70 + 15]
    new_data['y'] = ds.data['y'] + [random()*70 + 15]
    new_data['text_color'] = ds.data['text_color'] + [RdYlBu3[i%3]]
    new_data['text'] = ds.data['text'] + [str(i)]
    ds.data = new_data

    i = i + 1

#############################################################################
# add a button widget and configure with the call back
button = Button(label="Refresh")
button.on_click(callback)


#############################################################################
# RadioButtonGroup

from bokeh.models.widgets import RadioButtonGroup

button_group = RadioButtonGroup(labels=["Nov17", "Dec17", "Jan18"], active=0)

#############################################################################


	
	





#############################################################################
# pie chart 1


###
from math import pi

total_entries = len(output_df) + len(missing_df) 
correct_entries = len(output_df[output_df.Error == 0]) 
incorrect_entries = len(output_df[output_df.Error == 1])
missing_entries = len(missing_df)

angle0 = 0.0
angle1 = (correct_entries/total_entries)*2*pi
angle2 = angle1 + (incorrect_entries/total_entries)*2*pi
angle3 = angle2 + (missing_entries/total_entries)*2*pi


###


from bokeh.plotting import *
from numpy import pi

# define starts/ends for wedges from percentages of a circle
#percents = [0, 0.3, 0.4, 0.6, 0.9, 1]
percents = [correct_entries/total_entries, incorrect_entries/total_entries, missing_entries/total_entries,1.0]
starts = [p*2*pi for p in percents[:-1]]
ends = [p*2*pi for p in percents[1:]]

colors = ["red", "green", "blue"]

q = figure(plot_width=400, plot_height=400, x_range=(-1,1), y_range=(-1,1))

q.wedge(x=0, y=0, radius=1, start_angle=starts, end_angle=ends, color=colors)



################# pie chart 2



from bokeh.plotting import figure, output_file, show

pp = figure(plot_width=400, plot_height=400,x_range=(-1.2, 1.2), y_range=(-1.2, 1.2))

pp.wedge(x=0 , y=0, radius=1, start_angle=angle0, end_angle=angle1, color="green", legend="correct")
pp.wedge(x=0 , y=0, radius=1, start_angle=angle1, end_angle=angle2, color="red", legend="incorrect")
# "explode" one wedge by offsetting its center
#pp.wedge(x=0.1 , y=-0.1, radius=1, start_angle=angle2, end_angle=angle3, color="orange")
pp.wedge(x=0 , y=-0, radius=1, start_angle=angle2, end_angle=angle3, color="blue",legend="missing")


#mytext = Label(x=0, y=0, text='here your text')

#pp.add_layout(mytext)



#################### pie chart 3

current_month = "Jan18"
def get_current_month(current_month):
	try: 
		mod_df = pd.read_excel(current_month+'_Data.xlsx', sheet_name='Move_ins')
		missing_df = pd.read_excel(current_month+'_Data.xlsx', sheet_name='Missing')	
	except FileNotFoundError:
		#mod_df, missing_df = get_data()
		exit()	
	output_df=mod_df.drop(['OwnerID_x','PropertyID_x','OwnerID_y','PropertyID_y','strLengthOfTenancy','Date','blnCurrentOwner','blnVacant','blnDeleted','dteExtensionDate','Type'], axis=1)
	table1 = output_df[(output_df.Error == 1)&(output_df['Potential Interest']==0)][['dteOccupiedDate','TenancyID','strServiceProvided','Monthly Rent','Tenancy Length','Net','Cost' ]]
	table2 = output_df[(output_df.Error == 1)&(output_df['Potential Interest']==1)][['dteOccupiedDate','TenancyID','strServiceProvided','Monthly Rent','Tenancy Length','Net','Cost','Description' ]]
	table3 = missing_df[missing_df['Tenancy Status']=='Active'][['dteOccupiedDate','TenancyID','strServiceProvided','dblRentalAmount','Tenancy Status']]
	table4 = missing_df[missing_df['Tenancy Status']!='Active'][['dteOccupiedDate','TenancyID','strServiceProvided','dblRentalAmount','Tenancy Status']]
	return output_df, missing_df, table1, table2, table3, table4

###################################################################################

from bokeh.models.widgets import Select
###
select_month_angles = Select(title="Option:", value="desired_month", options=["Jan17","Feb17","Mar17","Apr17","May17","Jun17","Jul17","Aug17","Sep17","Oct17","Nov17","Dec17","Jan18"])


def calc_angles(current_month = "Nov17"):
	
	output_df, missing_df, table1, table2, table3, table4 = get_current_month(current_month)

	total_entries = len(output_df) + len(missing_df) 
	correct_entries = len(output_df[output_df.Error == 0]) 
	incorrect_entries = len(output_df[output_df.Error == 1])
	missing_entries = len(missing_df)

	angle0 = 0.0
	angle1 = (correct_entries/total_entries)*2*pi
	angle2 = angle1 + (incorrect_entries/total_entries)*2*pi
	angle3 = angle2 + (missing_entries/total_entries)*2*pi
	
	angles = ["angle0","angle1","angle2","angle3"]
	values = [angle0, angle1, angle2, angle3]
	
	angle_set_one = [angle0, angle1, angle2]
	angle_set_two = [angle1, angle2, angle3]
	angle_colors = ["green","red","blue"]
	angle_legend = ["correct","incorrect","missing"]
	#angles = {
	#"angle0": [angle0],
	#"angle1": [angle1],
	#"angle2": [angle2],
	#"angle3": [angle3]
	#}
	angledata = {'x':angle_set_one, 'y':angle_set_two, 'c':angle_colors, 'l':angle_legend}
	#angledata = {'angle0':angles['angle0'], 'angle1':angles['angle1'], 'angle2':angles['angle2'], 'angle3':angles['angle3']}
	anglesource = ColumnDataSource(angledata)
	return anglesource

	
def update_angles(attrname,old,new):
		statistic = select_month_angles.value
		new_source = calc_angles(statistic)
		scotty.data.update(new_source.data)
		#scotty = calc_angles(statistic)
		


#datasource1 = get_annual_source1()

scotty = calc_angles()

select_month_angles.on_change('value', update_angles)
	

qq = figure(plot_width=400, plot_height=400,x_range=(-1.2, 1.2), y_range=(-1.2, 1.2))

#qq.wedge(x=0 , y=0, radius=1, start_angle=angles['angle0'], end_angle=angles['angle1'], color="green", legend="correct")
#qq.wedge(x=0 , y=0, radius=1, start_angle=angles['angle1'], end_angle=angles['angle2'], color="red", legend="incorrect")
#qq.wedge(x=0 , y=-0, radius=1, start_angle=angles['angle2'], end_angle=angles['angle3'], color="blue",legend="missing")

#new_angle_1 = scotty['angle1']

qq.wedge(x=0 , y=0, radius=1, start_angle='x', end_angle='y', color='c', legend='l', source = scotty)#, legend="correct")
#qq.wedge(x=0 , y=0, radius=1, start_angle='', end_angle='', source = scotty, color='', legend="incorrect")
#qq.wedge(x=0 , y=-0, radius=1, start_angle='', end_angle='', source = scotty, color='',legend="missing")


##################################################################################



select = Select(title="Month:", value="desired_month", options=["Nov17","Dec17","Jan18"])


############################


select_month = Select(title="Option:", value="desired_month", options=["Nov17","Dec17","Jan18"])

def get_annual_source1(statistic="Nov17"):
	Month = [1,2,3,4,5,6,7,8,9,10,11,12]
	Totals = np.array([240,233,290,265,270,319,359,410,515,284,238,203])
	Correct = (np.array([93,81,114,103,95,125,132,145,161,115,110,99])/Totals)*100.0
	Incorrect = (np.array([102,104,128,126,132,150,176,197,269,121,95,79])/Totals)*100.0
	Missing = (np.array([45,48,48,36,43,44,51,68,85,48,33,25])/Totals)*100.0
	
	data = {
	"Month": Month,
	"Nov17": Incorrect,
	"Dec17": Totals,
	"Jan18": Correct
	}
	
	datadata = {'x':data['Month'], 'y':data[statistic]}
	datasource = ColumnDataSource(datadata)
	return datasource

def update_annual_source1(attrname,old,new):
		statistic = select_month.value
		new_source = get_annual_source1(statistic)
		datasource1.data.update(new_source.data)
	

datasource1 = get_annual_source1()

select_month.on_change('value', update_annual_source1)

t1 = figure(plot_width=800, plot_height=400)

# add both a line and circles on the same plot
t1.line('x', 'y', source = datasource1, line_width=2)
t1.circle('x', 'y', source = datasource1, fill_color="white", size=8)





#############################################################################
#bar

r = figure(plot_width=400, plot_height=400)
r.vbar(x=[1, 2, 3], width=0.5, bottom=[0.0,0.3,0.0], top=[1.2, 2.5, 3.7], color="firebrick")
r.vbar(x=[1, 2, 3], width=0.5, bottom=[1.2,2.5,3.7], top=[3.0, 4.0, 5.0], color="green")
	   
	   
#############################################################################
#line

from bokeh.models.widgets import Select

select = Select(title="Option:", value="power", options=["1.0","2.0","3.0"])


def make_line_plot(power):
	x = np.array([1., 2., 3., 4., 5.])
	y = np.array([6., 7., 8., 7., 3.])
	z = y**power
	test_data = {'x': x, 'y': z}
	source = ColumnDataSource(test_data)
	return source


def change_line_plot(attrname, old, new):
	power = float(select.value )
	new_source = make_line_plot(power)
	source.data.update(new_source.data)
	
power = 1.0
s = figure(plot_width=800, plot_height=400)

source = make_line_plot(power)

select.on_change('value', change_line_plot)

# add both a line and circles on the same plot
s.line('x', 'y', source = source, line_width=2)
s.circle('x', 'y', source=source, fill_color="white", size=8)


#############################################################################
#line 2

from bokeh.models.widgets import Select

select_annual = Select(title="Option:", value="statistic", options=["Totals","Correct","Incorrect","Missing"])

def get_annual_source(statistic="Totals"):
	Month = [1,2,3,4,5,6,7,8,9,10,11,12]
	Totals = np.array([240,233,290,265,270,319,359,410,515,284,238,203])
	Correct = (np.array([93,81,114,103,95,125,132,145,161,115,110,99])/Totals)*100.0
	Incorrect = (np.array([102,104,128,126,132,150,176,197,269,121,95,79])/Totals)*100.0
	Missing = (np.array([45,48,48,36,43,44,51,68,85,48,33,25])/Totals)*100.0
	
	data = {
	"Month": Month,
	"Totals": Totals,
	"Correct": Correct,
	"Incorrect": Incorrect,
	"Missing": Missing
	}
	
	datadata = {'x':data['Month'], 'y':data[statistic]}
	datasource = ColumnDataSource(datadata)
	return datasource

def update_annual_source(attrname,old,new):
		statistic = select_annual.value
		new_source = get_annual_source(statistic)
		datasource.data.update(new_source.data)
	

datasource = get_annual_source()

select_annual.on_change('value', update_annual_source)

t = figure(plot_width=800, plot_height=400)

# add both a line and circles on the same plot
t.line('x', 'y', source = datasource, line_width=2)
t.circle('x', 'y', source = datasource, fill_color="white", size=8)


##################################################################################
# table
from bokeh.models.widgets import PreText
stats = PreText(text='', width=1000)
pd.set_option('display.width', 1000)
stats.text = str(table1)



#table2
stats2 = PreText(text='', width=1000)

d = {'x':[1,2,3,4,5,6,7,8,9,0], 'y':[10,20,30,40,50,60,70,80,90,100], 'c':[100,200,300,400,500,600,700,800,900,1000], 'l':[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]}
df = pd.DataFrame(data=d)

#tabledata = {'x':[1,2,3,4,5,6,7,8,9,0], 'y':[1,2,3,4,5,6,7,8,9,0], 'c':[1,2,3,4,5,6,7,8,9,0], 'l':[1,2,3,4,5,6,7,8,9,0]}
tablesource = ColumnDataSource(df)
stats2.text = str(tablesource.data)

#table3
from bokeh.models.widgets import TableColumn,  DataTable


def get_table(current_month = "Nov17"):
	
	output_df, missing_df, table1, table2, table3, table4 = get_current_month(current_month)
	table_source = ColumnDataSource(table1)
	#table_source = ColumnDataSource(output_df[['TenancyID','dteOccupiedDate']])	
	return table_source

	
def update_table(attrname,old,new):
		statistic = select_month_angles.value
		new_source = get_table(statistic)
		tablesource2.data.update(new_source.data)
		

select_month_angles.on_change('value', update_table)

tablesource2 = get_table()
columns2 = [TableColumn(field="dteOccupiedDate", title="Date"),TableColumn(field="TenancyID", title="ID"),TableColumn(field="strServiceProvided", title="Service"),TableColumn(field="Monthly Rent", title="Monthly Rent"), TableColumn(field="Tenancy Length", title="Tenancy Length"), TableColumn(field="Net", title="Net"),TableColumn(field="Cost", title="Cost")]
data_table2 = DataTable(source=tablesource2,columns=columns2, width=1100, height=400)


###################################################################################
# create dashboard

# put the button and plot in a layout and add to the document
curdoc().add_root(column(button, button_group, select))
curdoc().add_root(select_month_angles)


curdoc().add_root(row(qq,r))
curdoc().add_root(row(q,r))

#curdoc().add_root(s)
curdoc().add_root(column(select_annual,t))
#curdoc().add_root(column(select_month,t1))
#curdoc().add_root(t)
#curdoc().add_root(stats)
#curdoc().add_root(stats2)
curdoc().add_root(data_table2)

#curdoc().add_root(column(button, p, s))


#create a session
#session = push_session(curdoc())
#session.show()
#session.loop_until_closed()