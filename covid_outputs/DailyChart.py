import plotly.express as px
import plotly.graph_objects as go
import  plotly as py
import pandas as pd
import sys

df = pd.read_csv(sys.argv[1], delimiter=',')
# fig = px.line(df, x="#time", y="susceptible", title='COVID-19 Simulation - London Borough of Brent')
# fig = px.line(df, x="#time", y="exposed", title='COVID-19 Simulation - London Borough of Brent')
# py.offline.plot(fig, filename='name.html')

df['new cases'] = df['exposed'].diff(1) + df['infectious'].diff(1)

layout = go.Layout(yaxis=(dict(type='log',autorange=True)))

fig = go.Figure(layout=layout)

# Add traces
fig.add_trace(go.Scatter(x=df['#time'], y=df['num infections today'],
                    mode='lines+markers',
                    name='# of new infections (sim)',  line=dict(color='orange')))
fig.add_trace(go.Scatter(x=df['#time'], y=df['num hospitalisations today'],
                    mode='lines+markers',
                    name='# of new hospitalisations',  line=dict(color='purple')))
#fig.add_trace(go.Bar(x=df['#time'], y=df['ward arrivals'],
#                    name='# of new hospitalisations (data)'))

py.offline.plot(fig, filename='cases-{}-.html'.format(sys.argv[1]))
