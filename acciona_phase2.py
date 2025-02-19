import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import textwrap
import streamlit as st

# set page
st.set_page_config(
    page_title="Acciona Phase II",
    page_icon="",
    layout="wide")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)

# load data
df = pd.read_csv("data/all_phase2.csv")
pvlocs = pd.read_csv("data/photovoltaic_locations.csv")
wlocs = pd.read_csv("data/wind_turbines_locations.csv")
df = df.merge(pd.concat([pvlocs,wlocs]),on="sitename")
df['year'] = df.time.apply(lambda x: x[0:4])

# chart colors
scenarios= ['ssp126', 'ssp245', 'ssp585']
assets = ['PV','Wind']

alpha = 0.1
colors = {
    'PV':{
        'ssp126':'rgb(245,222,152)',
        'ssp245':'rgb(245,150,35)',
        'ssp585':'rgb(118,47,61)',
    },
    'PVa':{
        'ssp126':f'rgba(245,222,152,{alpha})',
        'ssp245':f'rgba(245,150,35,{alpha})',
        'ssp585':f'rgba(118,47,61,{alpha})',
    },
    'Wind':{
        'ssp126':'rgb(150,242,238)',
        'ssp245':'rgb(45,156,237)',
        'ssp585':'rgb(5,28,97)',
    },
    'Winda':{
        'ssp126':f'rgba(150,242,238,{alpha})',
        'ssp245':f'rgba(45,156,237,{alpha})',
        'ssp585':f'rgba(5,28,97,{alpha})',
    },    
}

def make_small_multiples(asset):
    # small multiples
    dfasset = df[(df.asset_type==asset)]
    varnames = dfasset.varname.unique()
    sites = dfasset.sitename.unique()

    fig = make_subplots(
        shared_xaxes=True, shared_yaxes='rows',
        rows=len(varnames), cols=len(sites)+1,
        subplot_titles = [ x.replace("_"," ") for x in sites],
        horizontal_spacing=0.02,
        vertical_spacing=0.0
    )
    # add the lines
    domains = []
    for row,var in enumerate(varnames):
        ymin=1e6
        ymax=-1e6
        for col,site in enumerate(sites):
            dfa = dfasset[(dfasset.sitename==site)&(dfasset.varname==var)]
            for scenario in scenarios:
                # Add the main line
                fig.add_trace(go.Scatter(
                        x=dfa[(dfa.scenario==scenario)]['year'],
                        y=dfa[(dfa.scenario==scenario)]['value'],
                        name = scenario,
                        mode='lines', 
                        showlegend=False,
                        line=dict(color=colors[asset][scenario])
                    ),
                    row=row+1, col=col+1)  
                ymin = min(ymin, dfa[(dfa.scenario==scenario)]['value'].min() )
                ymax = max(ymax, dfa[(dfa.scenario==scenario)]['value'].max() )
        domains.append( [ymin,ymax])
        
    # add the row labels
    for row,var in enumerate(varnames):  
        svar = var.split()
        bvar = ""
        curlen = 0
        for idx,s in enumerate(svar):
            if curlen>= 10: #idx>0 and idx%1==0:
                bvar = bvar+"<br>"+s
                curlen = 0
            else:
                bvar = bvar +" "+ s
                curlen += len(s)
                
        fig.add_annotation(x=0, y=(domains[row][1]+domains[row][0])*0.5, #(ymax+ymin)*0.5/len(sites),
                        showarrow=False,yshift=0,xshift=0,
                        text=bvar, font=dict(size=10),align="left",
                        row=row+1, col=len(sites)+1)   

    fig.update_layout(template='plotly_white')

    fig.update_xaxes(showticklabels=False)
    fig.update_xaxes(showline=True, linewidth=0.1, linecolor='rgb(200,200,200)', mirror=True)
    fig.update_yaxes(showline=True, linewidth=0.1, linecolor='rgb(200,200,200)', mirror=True)
    fig.update_xaxes(ticklabelstep=3)

    return fig


def make_site_plots(sel_site):
    # map selector and individual charts
    dfsite = df[(df.sitename==sel_site)]
    asset_type = df[(df.sitename==sel_site)].asset_type.unique()[0]
    varnames = dfsite.varname.unique()

    if asset_type=="PV":
        ROWS = 4
    else:
        ROWS = 3

    fig = make_subplots(
        shared_xaxes=False, shared_yaxes=False,
        rows=ROWS, cols=2,
        #row_heights=[RATIO]+[(1-RATIO)/ROWS]*ROWS,
        subplot_titles = [ x.replace("_"," ") for x in varnames],
        specs= [[{}, {}] ]*(ROWS),
        # [
        #    [{"type": "scattergeo", "colspan": 2 },None] ] +
        #    horizontal_spacing=0.005,
        vertical_spacing=0.075,
    )

    for idx,var in enumerate(varnames):

        row, col = (1+(idx)//2, 1+(idx)%2)
            
        dfa = dfsite[(dfsite.varname==var)]
        
        for scenario in dfa.scenario.unique():
            # Add the main line
            fig.add_trace(go.Scatter(
                x=dfa[(dfa.scenario==scenario)]['year'],
                y=dfa[(dfa.scenario==scenario)]['value'],
                mode='lines', 
                name=scenario,
                line=dict(color=colors[asset_type][scenario]),
                showlegend=False),
                row=row, col=col    
            )
            
            # Add the confidence interval
            fig.add_trace(go.Scatter(
                x=dfa[(dfa.scenario==scenario)]['year'], 
                y=dfa[(dfa.scenario==scenario)]['percentile_5'], 
                fill=None,
                mode='lines',
                line_color=colors[asset_type+'a'][scenario], 
                hoverinfo='skip', 
                showlegend=False
            ),
                row=row, col=col)
            fig.add_trace(go.Scatter(
                x=dfa[(dfa.scenario==scenario)]['year'], 
                y=dfa[(dfa.scenario==scenario)]['percentile_95'], 
                fill='tonexty',
                mode='lines',
                line_color=colors[asset_type+'a'][scenario], 
                hoverinfo='skip', 
                showlegend=False,
                fillcolor=colors[asset_type+'a'][scenario]
            ),
                row=row, col=col,)

    fig.update_layout(template='plotly_white',
                    width=700,
                    height=165*ROWS)
    fig.update_annotations(font_size=12)
    fig.update_xaxes(ticklabelstep=3)
    fig.update_layout(
        margin={'t':20,'l':20,'b':20,'r':20}
    )        
    return fig


def make_map():
    sdf = df[['lat','lon','asset_type','sitename']]
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(lon=sdf['lon'],lat=sdf['lat'],
                        marker_color=sdf["asset_type"].apply(lambda x: colors[x]['ssp245']),
                            text = sdf["sitename"],
                            hoverinfo="text",showlegend=False,
                            marker=dict(size=12, opacity=0.8)))
    fig.update_geos(projection_type= "natural earth") # "orthographic") 
    fig.update_layout(
        margin={'t':0,'l':0,'b':0,'r':0}
    )
    fig.update_layout(dragmode=False)
    return fig


sel_site = None

st.title("Acciona Phase II")
st.markdown("This is a dashboard to explore the results of the Acciona Phase II project. The data is based on the results of the simulations of the different assets (PV and Wind) under different scenarios (SSP126, SSP245, SSP585)")
st.empty()

# Layout    
left_column, right_column = st.columns(2)

with left_column:
    event = st.plotly_chart(make_map(),
                    on_select="rerun", selection_mode=["points"])
    points = event["selection"].get("points", [])
    if points:
        first_point = points[0]
        sel_site = first_point.get("text", None)
    else:
        sel_site = None
    st.empty()
    #sel_site = st.selectbox("Select site",df.sitename.unique())
    if sel_site is not None:
        title_col, close_col = st.columns([0.9, 0.1])
        if close_col.button("",icon=":material/close:"):
            sel_site = None
        else:
            title_col.markdown(f"### Power and damage predictions for {sel_site.replace('_',' ')}")
            st.plotly_chart(make_site_plots(sel_site))

with right_column:
    st.plotly_chart(make_small_multiples('PV'))
    st.plotly_chart(make_small_multiples('Wind'))


