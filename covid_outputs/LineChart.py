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

fig = go.Figure()

# Add traces
fig.add_trace(go.Scatter(x=df['#time'], y=df['susceptible'],
                    mode='lines+markers',
                    name='susceptible',  line=dict(color='orange')))
fig.add_trace(go.Scatter(x=df['#time'], y=df['exposed'],
                    mode='lines+markers',
                    name='exposed',  line=dict(color='purple')))
fig.add_trace(go.Bar(x=df['#time'], y=df['new cases'],
                    name='change in # affected'))
fig.add_trace(go.Scatter(x=df['#time'], y=df['infectious'],
                    mode='lines+markers',
                    name='infectious',  line=dict(color='red')))
fig.add_trace(go.Scatter(x=df['#time'], y=df['recovered'],
                    mode='lines+markers',
                    name='recovered', line=dict(color='green')))
fig.add_trace(go.Scatter(x=df['#time'], y=df['dead'],
                    mode='lines+markers',
                    name='dead', line=dict(color='black')))

py.offline.plot(fig, filename='cases-{}-.html'.format(sys.argv[1]))
