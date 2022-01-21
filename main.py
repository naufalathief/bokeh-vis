from bokeh.io import curdoc, output_notebook
from bokeh.models.tools import HoverTool
from bokeh.models import DateRangeSlider,  ColumnDataSource, PreText, Select, Range1d, RadioButtonGroup, Div, CustomJS, Button
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import column, row
import bokeh
import pandas as pd
import numpy as np
from os.path import dirname, join
import locale
locale.setlocale(locale.LC_ALL)
# import data
df_confirmed = pd.read_csv(
    join(dirname(__file__), 'data', 'confirmed.csv'), parse_dates=['date'])
df_death = pd.read_csv(join(dirname(__file__), 'data',
                            'death.csv'), parse_dates=['date'])
df_recovered = pd.read_csv(
    join(dirname(__file__), 'data', 'recovered.csv'), parse_dates=['date'])

df_confirmed.drop("Unnamed: 0", axis=1, inplace=True)
df_death.drop("Unnamed: 0", axis=1, inplace=True)
df_recovered.drop("Unnamed: 0", axis=1, inplace=True)

regions_death = df_death.columns[0:-1]
regions_confirmed = df_confirmed.columns[0:-1]
regions_recovered = df_recovered.columns[0:-1]
total_death_case = dict(df_death.iloc[-1, ])
total_recovered_case = dict(df_recovered.iloc[-1, ])
total_confirmed_case = dict(df_confirmed.iloc[-1, ])


def create_source(region, case, date_range=None):
    if case == 'confirmed':
        plot = df_confirmed[region]
    elif case == 'death':
        plot = df_death[region]
    elif case == 'recovered':
        plot = df_recovered[region]
    if case == "all":
        df = pd.DataFrame(data={
            'date': df_death['date'],
            'death': df_death[region],
            'recovered': df_recovered[region],
            'plot': df_confirmed[region]
        })
    else:
        df = pd.DataFrame(data={
            'date': df_death['date'],
            'plot': plot
        })
    if date_range is not None:
        mask = (df['date'] > np.datetime64(date_range[0])) & (
            df['date'] <= np.datetime64(date_range[1]))
        df = df.loc[mask]
    return ColumnDataSource(df)


def make_plot(source, title, case='confirmed', sizing_mode=None):
    if sizing_mode is None:
        plt = figure(x_axis_type='datetime', name='plt', height=800)
    else:
        plt = figure(x_axis_type='datetime',
                     sizing_mode=sizing_mode, name='plt', height=500)
    plt.title.text = title
    plt.title.text_font_size = "large"
    plt.line('date', 'plot', source=source, color='dodgerblue', line_width=1,
             name='case', legend_label=case)
    plt.circle('date', 'plot', size=10, color="black", source=source)

    hover = HoverTool(tooltips=[('Tanggal', '@date{%F}'), ('Total Kasus', '@plot')],
                      formatters={'@date': 'datetime'})
    plt.add_tools(hover)
    plt.legend.location = "top_left"
    plt.legend.background_fill_color= "black"
    plt.xaxis.axis_label = "Tanggal"
    plt.yaxis.axis_label = "Total Kasus"
    plt.axis.axis_label_text_font_style = "bold"
    plt.grid.grid_line_alpha = 0.3
    return plt


def update(date_range=None, force=False):
    global region, case, plt
    plt.title.text = "Kasus "+ case.capitalize() + " di " + region
    newdata = create_source(region, case, date_range).data
    source.data.update(newdata)


def handle_region_change(attrname, old, new):
    global region
    region = region_select.value
    update()


def handle_case_change(attrname, old, new):
    from bokeh.models.glyphs import Line
    global case
    cases = ["confirmed", "recovered", "death", 'all']
    case = cases[new]
    update()

    if case == 'confirmed' or case == "all":
        color = 'dodgerblue'
    elif case == 'death':
        color = 'red'
    elif case == 'recovered':
        color = "green"

    if case != "all" or case == 'global':
        plt.legend.items = [
            (case, [plt.renderers[0]])
        ]
        plt.renderers[0].glyph.line_color = color
        plt.renderers[1].glyph.line_color = color
        try:
            plt.renderers[2].visible = False
            plt.renderers[3].visible = False
        except IndexError:
            print(False)
    else:
        try:
            plt.renderers[0].glyph.line_color = 'dodgerblue'
            plt.renderers[1].glyph.line_color = 'dodgerblue'
            plt.renderers[2].visible = True
            plt.renderers[3].visible = True
            plt.legend.items = [
                ("confirmed", [plt.renderers[0]]),
                ("recovered", [plt.renderers[2]]),
                ("death", [plt.renderers[3]])
            ]
        except IndexError:
            plt.vbar('date', top='recovered', width=1, line_width=5, source=source, color='green',
                     name='recovered', legend_label="recovered")
            plt.step(x='date', y='death', source=source, color='red', line_width=2,
                     name='death', legend_label="death")


def handle_range_change(attrname, old, new):
    global slider_value
    slider_value = range_slider.value_as_datetime
    update(date_range=slider_value)



stats = PreText(text='', width=500)
case = "confirmed"
region = 'Indonesia'
source = create_source(region, case)
total_data = len(source.data['date'])-1
case_date = pd.to_datetime(source.data['date'])
slider_value = case_date[0], case_date[-1]
theme = 'caliber'


total_case_template = ("""
    <div style="width:150px;
    position:center;">
        <div class="card text-center w-100">
            <div class="card-header bg-{color}">
                <h5 class="m-0">Local {case}</h5>
            </div>
            <div class="card-body p-2">
                <h3><strong id="total-{region}-{case}">{total}</strong></h3>
            </div>
        </div>
    </div>
      """)

death_count = df_death.iloc[-1, df_death.columns.get_loc(region)]
confirmed_count = df_confirmed.iloc[-1, df_confirmed.columns.get_loc(region)]
recovered_count = df_recovered.iloc[-1, df_recovered.columns.get_loc(region)]
death_case = Div(text=total_case_template.format(
    case="Death", region="Region", color='grey', total=f'{death_count:n}'), width_policy="max")
confirmed_case = Div(text=total_case_template.format(
    case="Confirmed", region="Region", color='grey', total=f'{confirmed_count:n}'), width_policy="max")
recovered_case = Div(text=total_case_template.format(
    case="Recovered", region="Region", color='grey', total=f'{recovered_count:n}'), width_policy="max")


case_select = RadioButtonGroup(
    labels=["Confirmed", "Recovered", "Death"], active=0, name="case_select")
region_select = Select(value=region, title='Negara/Daerah',
                       options=list(regions_confirmed), name="region_select")
range_slider = DateRangeSlider(
    start=slider_value[0], end=slider_value[1], value=(0, slider_value[1]), title='Date', name="range_slider")



region_select.on_change('value', handle_region_change)

code = """
    var death = document.getElementById("total-Region-Death");
    var recovered = document.getElementById("total-Region-Recovered");
    var confirmed = document.getElementById("total-Region-Confirmed");
    var region = cb_obj.value
    death.innerHTML = death_case[region].toLocaleString('id')
    recovered.innerHTML = recovered_case[region].toLocaleString('id')
    confirmed.innerHTML = confirmed_case[region].toLocaleString('id')
"""

js_on_change_region = CustomJS(
    args=dict(source=source, death_case=total_death_case, confirmed_case=total_confirmed_case, recovered_case=total_recovered_case), code=code)
region_select.js_on_change('value', js_on_change_region)

case_select.on_change('active', handle_case_change)
range_slider.on_change('value', handle_range_change)

plt = make_plot(source, case.capitalize() + " case in " +
                region, case, sizing_mode="stretch_both")


controls = column(region_select,  case_select, range_slider,
                  confirmed_case, death_case, recovered_case)
main_layout = column(
    row(controls, plt, sizing_mode="stretch_height"), sizing_mode="stretch_both")
curdoc().add_root(main_layout)
curdoc().title = "Kasus COVID Januari-April 2020"
curdoc().theme = theme
