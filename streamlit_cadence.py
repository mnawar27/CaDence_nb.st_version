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
    st.image("/Users/efigueroa/Desktop/CaDence_nb.st_version/Media/logonobglittle.png")
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

######## Plan Level GABI

def paid_level(df_selected_week):
    paidlev = df_selected_week.groupby('userId')['level'].first().value_counts()
    paidlev=paidlev.reset_index(drop=False)

    #Titles
    label_tz = ", ".join(df_selected_week['time_zone'].unique())
    label_wk = ", ".join(df_selected_week['week'].unique())

    ## Horizontal bar chart.  
    fig, ax = plt.subplots(figsize=(1,2))
    paidlev.plot(kind='bar',stacked=True,color=['#dc14c5', '#20b85f'], ax=ax)
    ax.set_title("Paid vs Free Accounts",fontsize=20,pad=20)
    ax.set_xticklabels(paidlev['level'],rotation=0, ha='right')
    y=paidlev['count'].nlargest(1)
    ax.set_yticks(np.arange(0, max(y) + 100, 100))
    ax.set_xticklabels(['Free','Paid'])
    ax.legend().remove()
    return fig

####### Devices  GABI

def most_used_platform(df_selected_week):
    platform=df_selected_week.groupby('userId')['userAgent'].first().value_counts()
    ##Donut Chart
    fig = px.pie(platform, names=platform.index,values=platform, hole=.6,color='count',
                color_discrete_map={'Windows':'#dc14c5',
                                    'Mac':'#d84f9e',
                                    'Linux':'#7f43ac',
                                    'iPhone':'#3c34bc',
                                    'iPad':'#1eb75c'})
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(showlegend=False, font_size=15, height=380,width=100,title=dict(text="Platforms Used", x=0.3,font=dict(size=20)))
    return fig

#2nd Column - - User Map, Gender and Summary Table

####### State user Counts (Maisha and Sharmin)
######## MAISHA

def get_state_count(omega_raw, time_zone='All', week='All'):
    df = omega_raw.copy()
    if time_zone != 'All': df = df[df['time_zone'] == time_zone]
    if week != 'All': df = df[df['week'] == week]

    groupby_cols = ['state', 'time_zone'] if week == 'All' else ['state', 'time_zone', 'week']
    state_count = df.groupby(groupby_cols)['userId'].nunique().reset_index()

    state_count.columns = ['State', 'Time Zone', 'User Count'] if week == 'All' else ['State', 'Time Zone', 'Week', 'User Count']
    # hover_data = {'User Count': True, 'Time Zone': True, 'Week': True} if week != 'All' else {'User Count': True, 'Time Zone': True}

    # Create plot
    fig = px.choropleth(state_count, locations='State', locationmode='USA-states', color='User Count',
                        hover_name='State', color_continuous_scale="plasma")
    fig.update_layout(mapbox_zoom=9,
    title={
        'text': "Users Per State",
        'x': 0.5,  # Set x position to the center
        'xanchor': 'center',  # Anchor the title to the center
        'font_size':25
    })
    fig.update_geos(visible=True, showcoastlines=True, coastlinecolor="Black", showland=True, landcolor="lightgray", projection_type="albers usa",bgcolor='black')
    return fig

####### Gender
####### SHARMIN #######
def get_gender_shaded_horizontal(df_selected_week):
    # Get the gender count (adjust for correct column names)
    gender_counts = df_selected_week['gender'].value_counts()
    # Replace 'M' with 'Male' and 'F' with 'Female' using map
    gender_counts.index = gender_counts.index.map({'M': 'Male', 'F': 'Female'})
    # Create a horizontal bar chart
    fig, ax = plt.subplots(figsize=(6, 3))
    # Shaded colors: Medium turquoise for Male, plum for Female
    colors = ['mediumturquoise', 'plum']  # Adjust the color scheme for Male and Female
    bars = ax.barh(gender_counts.index, gender_counts.values, color=colors, height=0.4)
    # Add percentage labels with dynamic positioning
    total_count = gender_counts.sum()
    for bar in bars:
        # Get the width of the bar (since it's horizontal, width is along x-axis)
        width = bar.get_width()
        percentage = (width / total_count) * 100
        # Position the text based on the percentage
        if percentage > 50:  # For high percentages, place inside the bar
            ax.text(width / 2, bar.get_y() + bar.get_height() / 2,
                    f'{percentage:.1f}%', ha='center', va='center',
                    fontsize=12, color='darkgreen', fontweight='bold')
        else:  # For low percentages, place outside the bar
            ax.text(width + 5, bar.get_y() + bar.get_height() / 2,
                    f'{percentage:.1f}%', ha='left', va='center',
                    fontsize=12, color='brown', fontweight='bold')
    # Add a title and labels
    ax.set_xlabel("Count", fontsize=14, fontweight='bold')
    ax.set_ylabel("Gender", fontsize=14, fontweight='bold')
    ax.set_title(f"Gender Distribution in {df_selected_tz.iloc[1, 12]} for {selected_week}", fontsize=16, fontweight='bold')
    # Add gridlines for style
    ax.set_facecolor('ghostwhite')
    ax.grid(True, axis='x', linestyle='--', alpha=0.6)
    # Display the plot
    plt.tight_layout()
    return plt




#3rd Column -  Top 10 Songs, Duration and Artists

####### Song
def most_played(df_selected_week):
    mps=df_selected_week['song'].value_counts().nlargest(10).reset_index()
    mps.columns = ['Song', 'Plays']  
    mps['Rank'] = mps.index + 1  
    mps = mps[['Rank', 'Song', 'Plays']]
    return mps

####### Duration
def hours_listened(df_selected_week):
    total_dur=df_selected_week.groupby('userId')['duration'].sum().sort_values(ascending=False)
#### now we find the outliers with IQR Method
    q1 = total_dur.quantile(0.25)
    q3 = total_dur.quantile(0.75)
    IQR = q3 - q1
    no_outliers = total_dur[(q1 - 1.5*IQR < total_dur) &  (total_dur < q3 + 1.5*IQR)]
#### Turn Seires into DF for better graphin
    df_no_outliers=pd.DataFrame(no_outliers)
    df_no_outliers=df_no_outliers.reset_index(drop=False)
###### Filter with new DF to have refined and unrefied.
####### Refined
    dur_refined_sum=df_no_outliers['duration'].sum()
    dur_reuni=df_no_outliers['userId'].nunique()
    dur_refined_av=dur_refined_sum/dur_reuni
    dur_refined_av=dur_refined_av.round(2)
####### Unrefined
    dur_unrefined=df_selected_week['duration'].sum()
    dur_unrefined_uni=df_selected_week['userId'].nunique()
    dur_unrefined=dur_unrefined/dur_unrefined_uni
    dur_unrefined=dur_unrefined.round(2)
######### Concat both DFs to make a nicer chart. If this doesn't work for final graph, you can silence this and
######### just use the df names in the brackets [ ] and call them individually instead.
    final_dur=pd.DataFrame({'Unrefined Duration': [dur_unrefined], 'Refined Duration': [dur_refined_av]})
################# Graph
    ax = final_dur.plot(kind='bar',stacked=True)
    ax.set_xlabel("Time Zone")
    ax.set_ylabel("Durations")
    # ax.set_title(f"in {df_selected_tz.iloc[1,12]} in {selected_week}")
    plt.legend(title="Levels")
    st.plylot(plt)
    return



#     odur=df_selected_week.groupby('userId')['duration'].sum()/60
#     odur=odur.round().sort_values(ascending=False)
#     odur_final=odur.reset_index(drop=True)
#     # odur_final=odur.drop(odur[odur['duration'] == 0].index)
    

#     total_dur=df_selected_week.groupby('userId')['duration'].sum().sort_values(ascending=False)
# ##### Find Outliers
#     q1 = total_dur.quantile(0.25)
#     q3 = total_dur.quantile(0.75)
#     IQR = q3 - q1
#     no_outliers = total_dur[(q1 - 1.5*IQR < total_dur) &  (total_dur < q3 + 1.5*IQR)]
# #### Turn Seires into DF
#     df_no_outliers=pd.DataFrame(no_outliers)
#     df_no_outliers=df_no_outliers.reset_index(drop=False)
# ###### Filter with new DF to have refined and unrefied.
# ####### Refined
#     dur_refined_sum=df_no_outliers['duration'].sum()
#     dur_reuni=df_no_outliers['userId'].nunique()
#     dur_refined_av=dur_refined_sum/dur_reuni
#     dur_refined_av=dur_refined_av.round(2)
#     dur_refined_av=dur_refined_av.reset_index(drop=True)
#     y=odur
#     x1=odur_final
#     x2=dur_refined_av
# #### stacked area chart.
#     plt.stackplot(y,x1,x2, labels=['A','B','c'])
#     plt.legend(loc='upper left')
#     plt.show()


####### Artist # GABI
def most_played_artist(df_selected_week):
    mpa=df_selected_week['artist'].value_counts()
# WordCloud 
    wc = WordCloud(background_color='black', colormap='spring', width=800, height=400).generate_from_frequencies(mpa)
    plt.figure(figsize=(10, 6))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")
    st.pyplot(plt)

#### Top User  ENDA
def leader_board(df_selected_week):
    top_boi=df_selected_week.groupby('userId')['duration']
    top_boi=top_boi.sum().sort_values(ascending=False)
    top_boi=top_boi//60
    top_boi=top_boi.reset_index(drop=False)
    top_boi=top_boi.head(6)
    best_bois=top_boi['userId'].head(6)
    best_bois=best_bois.reset_index(drop=False)
    last_boi=[]
    for i in best_bois['userId']:
        big_boi_name=df_selected_week['firstName'].loc[df_selected_week['userId']==i].head(1)
        big_boi_state=df_selected_week['state'].loc[df_selected_week['userId']==i].head(1)
        big_boi_listen=top_boi['duration'].loc[top_boi['userId']==i]
        lb_boi=pd.DataFrame({'User Id': [i], 'Name': [big_boi_name.iloc[0]], 'State': [big_boi_state.iloc[0]], 'Hours': [big_boi_listen.iloc[0]]})
        last_boi.append(lb_boi)
    boss_boi = pd.concat(last_boi, ignore_index=True)
    return boss_boi
    

##################################################### Format top text report ENDA
def text_report(df_selected_week):
    label_tz = ", ".join(df_selected_week['time_zone'].unique())
    label_wk = ", ".join(df_selected_week['week'].unique())
    if sb_wk == present:
        week_frag = "ZipSpontify is currently being"
        is_was="is"
    else:
        week_frag = f"during {label_wk} ZipSpontify was"
        is_was="was"
    if sb_tz == allPlaces:
        place_frag= f"In all time zones"
    elif len(sb_tz)==1:
        place_frag=f"For time zone {label_tz}"
    else:
        place_frag=f"For time zones {label_tz}"
    
    u_unique=df_selected_week['userId'].nunique()
    topSong=df_selected_week['song'].value_counts().head(1)
    topSong=topSong.to_string()
    durry=df_selected_week['duration'].sum()//60
    durry=durry.round()
    st.markdown(f"{place_frag} {week_frag} acessed by {u_unique} unique users. Their combined listening duration {is_was} {durry} hours")
################################################################################
#####################################################  Dashboard Main Panel
############################################################################
text_report(df_selected_week)
col = st.columns((3, 5, 2), gap='medium') #Divide the dashboard into 3 columns - inside the () are display the relative size of the columns (portion)

#####################################1st Column - Plan level and Device Type
with col[0]:
    with st.container(height=420,border=True):
##################################   PLAN LEVEL

        # st.markdown('### Account Levels')
        level_chart = paid_level(df_selected_week)

        if level_chart:
            st.pyplot(level_chart, use_container_width=True)


######################################### DEVICES
    with st.container(height=420,border=True):
        # st.markdown('## Platforms')
        donut = most_used_platform(df_selected_week)
        st.plotly_chart(donut, use_container_width=True)

#2nd Column - User Map, Gender and Summary Table
###########################################################################
with col[1]:
##########################################################################
##################################################### USER MAP
    with st.container(height=400,border=True):
        # st.markdown('### User Count per State')
        get_state_count = get_state_count(df_selected_week)

        if get_state_count:
            st.plotly_chart(get_state_count)
##################################################### WORD COUNT

    # st.markdown('#### Top Artists')
    wordcloud_chart = most_played_artist(df_selected_week)
    if wordcloud_chart:
        st.pyplot(plt)
    # st.markdown('### Gender Distribution')
    # gender_chart = get_gender(df_selected_week)

    # if gender_chart:
    #     st.pyplot(gender_chart)
    with st.expander('Artist Play Counts',expanded=False):
        mpa=df_selected_week['artist'].value_counts()
        mpa=mpa.sort_values(ascending=False).reset_index(drop=False)

        # for i in mpa['artist']:
        #     totdur=df_selected_week['duration'].loc[df_selected_week==i]
        #     totdur=totdur.sum().reset_index(drop=True)

        st.dataframe(mpa.set_index(mpa.columns[0]),use_container_width=True)
######################################################### SUMMARY TABLE

##### (TBA)

##########################################################################    
#3rd Column - Top 10 Songs, Duration and Artists
##########################################################################
with col[2]:

##################################################### TOP SONGS
    st.markdown('#### Most Played Songs')
    most_played_songs = most_played(df_selected_week)

    if most_played_songs is not None:
        st.dataframe(most_played_songs.set_index(most_played_songs.columns[0]), width=300)
        


##################################################### Leader Board
    st.markdown('#### Top Users')
    leader_board = leader_board(df_selected_week)

    if leader_board is not None:
        st.dataframe(leader_board.set_index(leader_board.columns[0]), width=300)

##################################################### DURATION
## (Broken, Commented out for now)
    # st.markdown('#### Hours Listening')
    # hours_listened = hours_listened(df_selected_week)

    # if hours_listened is not None:
    #     st.pyplot(plt)

##################################################### GENDER
## (Broken, Commented out for now )
    # get_gen=get_gender_shaded_horizontal(df_selected_week)

    # if get_gen is not None:
    #     st.table(get_gen)
    
# with st.expander('Simple Report', expanded=True):
#     st.write('''
#             -Top Ten Artist:
#             -Top Ten Songs:
#             -State with Most Users:
#             -State with Least Users:
#             -Paid Users:
#             -Free Users:
#             -''' )   
