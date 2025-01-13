import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import matplotlib.pyplot as plt
import wordcloud
from wordcloud import WordCloud
import numpy as np

plt.style.use('dark_background')
#######################  Page Config
st.set_page_config(
    page_title="CaDence",
    page_icon= "🎶",
    layout="wide",
    initial_sidebar_state="expanded")

# alt.themes.enable("dark")
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)



#######################
# Load data
omega_raw = pd.read_json('data/omega_raw.json', lines=True)
est_df = pd.read_json('data/est_df.json', lines=True)
cst_df = pd.read_json('data/cst_df.json', lines=True)
mst_df = pd.read_json('data/mst_df.json', lines=True)
pst_df = pd.read_json('data/pst_df.json', lines=True)
hst_df = pd.read_json('data/hst_df.json', lines=True)


#######################
# Sidebar

with st.sidebar:
    st.header('Time Zone and Week Controls')
    ##### Defaults Below
    present=['Present']
    allPlaces=['EST','CST','MST','PST','HST']
    ###### Button Select
    sb_tz = st.multiselect("Select one or more options:",
        ['EST','CST','MST','PST','HST'], key='time zone')
    
    all_options = st.button("Select all Time Zones")
    if all_options:
        sb_tz = allPlaces

    st.header('Week')
    sb_wk = st.multiselect("Choose a Week",['Present','Week 1','Week 2', 'Week 3','Week 4','Week 5'], key='option_2')
    
    all_options_w = st.button("Select all Weeks")
    if all_options_w:
        sb_wk = ['Week 1', 'Week 2', 'Week 3','Week 4','Week 5','Present']
    
################ Begin DF corelation to feed into Dashboard
    df_seled_wk =pd.DataFrame(columns=['artist', 'song','duration','ts','sessionId','level','state','userAgent','userId','firstName','gender','week','time_zone'])
#### Have 'present as default
    if sb_wk==[]:
        sb_wk=present
    else:
        sb_wk=sb_wk
#### If no tz, then all tz to avoid errors before selections are made.
    if sb_tz==[]:
        sb_tz=allPlaces
###### If selections are made, go with the selections
    else:
        sb_tz=sb_tz
#### Now that there's a df with the right tz, narrow down to the ones with the right weeks we want    
    for i in sb_tz:
        select_tz= omega_raw.loc[omega_raw['time_zone'] == i]
        df_seled_wk=pd.concat([df_seled_wk,select_tz])
    df_selected_week= df_seled_wk[df_seled_wk['week'].isin(sb_wk)]

    # color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    # selected_color_theme = st.selectbox('Select a color theme', color_theme_list)


#######################
# Plots

#1st Column - Plan level and Device Type

######## Plan Level

def paid_level(df_selected_week):
    paidlev = df_selected_week.groupby('userId')['level'].first().value_counts()

    #Titles
    label_tz = ", ".join(df_selected_week['time_zone'].unique())
    label_wk = ", ".join(df_selected_week['week'].unique())

    ## Horizontal bar chart. 
    fig, ax = plt.subplots(figsize=(8, 6))
    paidlev.plot(kind='barh', stacked=True, color=['#dc14c5', '#7f43ac'], ax=ax)
    ax.set_xlabel("Count")
    ax.set_ylabel("Level")
    ax.set_title(f"Paid vs Free Accounts in {label_tz} during {label_wk}") #here we need to adjust the labels to do not show all the weeks
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    return fig

####### Devices

def most_used_platform(df_selected_week):
    platform=df_selected_week.groupby('userId')['userAgent'].first().value_counts()
    ##Donut Chart
    fig = px.pie(platform, names=platform.index, values=platform, hole=.6,color='count',
                color_discrete_map={'Windows':'#dc14c5',
                                    'Mac':'#d84f9e',
                                    'Linux':'#7f43ac',
                                    'iPhone':'#3c34bc',
                                    'iPad':'#1eb75c'})
    fig.update_traces(textinfo='percent+label')
    # fig.update_layout(title_text=f"Most Used Platforms in {df_selected_tz.iloc[1,12]} in {selected_week}")
    return fig

#2nd Column - - User Map, Gender and Summary Table

####### State user Counts (Maisha and Sharmin)
#INSERT CODE

def get_state_count(df_selected_week):
    state_count = df_selected_week.groupby('state')['userId'].nunique()
    state_count_final = state_count.sort_values(ascending=False).nlargest(5)
    ####### You can change the graphic code here. If you want more than the top five,
    ####### Change the number in nlargest
    ax = state_count_final.plot(kind='bar', stacked=True)
    ax.set_xlabel("States")
    ax.set_ylabel("Count")
    # ax.set_title(f"Top States with Highest Number of Users in {df_selected_tz.iloc[1,12]} in {selected_week}")
    plt.legend(title="Count")
    st.pyplot(plt)

####### Gender
def get_gender(df_selected_week):
    gender_df = df_selected_week.groupby('userId')['gender'].first().value_counts()
    label_tz = ", ".join(df_selected_week['time_zone'].unique())
    label_wk = ", ".join(df_selected_week['week'].unique())
###### Vertical bar graph
    fig, ax = plt.subplots(figsize=(4, 6))
    gender_df.plot(kind='bar', stacked=True, color=['#1f77b4', '#ff7f0e'], ax=ax)
    ax.set_xlabel("Gender")
    ax.set_ylabel("Counts")
    ax.set_title(f"Gender Counts in {label_tz} during {label_wk}")
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    return fig




#3rd Column -  Top 10 Songs, Duration and Artists

####### Song
def most_played(df_selected_week):
    mps=df_selected_week['song'].value_counts().nlargest(5).reset_index()
    mps.columns = ['Song', 'Plays']  
    mps['Rank'] = mps.index + 1  
    mps = mps[['Rank', 'Song', 'Plays']]
    return mps

####### Duration

def hours_listened(df_selected_week):
    odur=df_selected_week.groupby('state')['duration'].sum()/60
    odur=odur.round().sort_values(ascending=False)
    odur=odur.reset_index(drop=False)
    odur_final=odur.drop(odur[odur['duration'] == 0].index)
### Finding middle section to highlight
    index_third=odur.iloc[0,1]//3
    topnum=odur.iloc[0,1]-index_third
    bottomnum=odur_final.iloc[-1,1]+index_third
    y_av=np.mean(odur_final['duration'])
    odur_final.plot.bar('state','duration')
    plt.axhspan(topnum, bottomnum, color='red', alpha=0.2)
    # plt.title(f"Duration in Hours per User in {df_selected_tz.iloc[1,12]} in {selected_week}")
    plt.axhline(y=y_av, color='r', linestyle='--', label='Average')
    st.pyplot(plt)

####### Artist
def most_played_artist(df_selected_week):
    mpa=df_selected_week['artist'].value_counts()
# WordCloud 
    wc = WordCloud(background_color='black', colormap='winter', width=800, height=400).generate_from_frequencies(mpa)
    plt.figure(figsize=(10, 7))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")
    st.pyplot(plt)



#######################
# Dashboard Main Panel
#######################
col = st.columns((2.5, 5, 2.5), gap='medium') #Divide the dashboard into 3 columns - inside the () are display the relative size of the columns (portion)

#1st Column - Plan level and Device Type
with col[0]:
    st.image("/Users/efigueroa/Desktop/CaDence_nb.st_version/Media/logonobglittle.png")
####PLAN LEVEL

    st.markdown('#### Account Levels')
    level_chart = paid_level(df_selected_week)

    if level_chart:
        st.pyplot(level_chart, use_container_width=True)


####DEVICES

    st.markdown('## Platforms')
    donut = most_used_platform(df_selected_week)
    st.plotly_chart(donut, use_container_width=True)

#2nd Column - User Map, Gender and Summary Table

with col[1]:

####USER MAP
    st.markdown('### User Count per State')
    get_state_count = get_state_count(df_selected_week)

    if get_state_count:
        st.plotly_chart(get_state_count, use_container_width=True)
####GENDER
    st.markdown('### Gender Distribution')
    gender_chart = get_gender(df_selected_week)

    if gender_chart:
        st.pyplot(gender_chart)

####SUMMARY TABLE



    
#3rd Column - Top 10 Songs, Duration and Artists
with col[2]:

####TOP SONGS
    st.markdown('#### Most Played Songs (Top 5)')
    most_played_songs = most_played(df_selected_week)

    if most_played_songs is not None:
        st.markdown(most_played_songs.style.hide(axis="index").to_html(), unsafe_allow_html=True)
        # st.table(most_played_songs.reset_index(drop=True))

####DURATION
    st.markdown('#### Hours Listening')
    hours_listened = hours_listened(df_selected_week)

    if hours_listened is not None:
        st.table(hours_listened)

####TOP ARTISTS
    st.markdown('#### Top Artists')
    wordcloud_chart = most_played_artist(df_selected_week)
    if wordcloud_chart:
        st.pyplot(plt)
    
    
    
#  with st.expander('About', expanded=True):
#     st.write('''
#             - Data: [U.S. Census Bureau](https://www.census.gov/data/datasets/time-series/demo/popest/2010s-state-total.html).
#             - :orange[**Gains/Losses**]: states with high inbound/ outbound migration for selected year
#             - :orange[**States Migration**]: percentage of states with annual inbound/ outbound migration > 50,000
#             ''')