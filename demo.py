from select import select
import streamlit as st
import pandas as pd
import requests
import numpy as np
import pydeck as pdk
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode


def main(): 
    file = st.sidebar.file_uploader("Upload file", type=['csv', 'xlsx', 'pickle'])
    if not file:
        st.sidebar.write("Upload a .csv or .xlsx file to get started")
        return

    data = pd.read_csv(file, encoding="euc-kr")
    st.sidebar.write("파일이름:", file.name)

    select1 = data['지방청'].drop_duplicates()
    add_selectbox = st.sidebar.selectbox("지방청 Select Box", (select1))
    
    selected_data  = data['지방청'] == add_selectbox
    data = data[selected_data]
    st.write(add_selectbox ,'의 데이터(', len(data),")")
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_pagination()
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gridOptions = gb.build()

    select_grid = AgGrid(data, 
              gridOptions=gridOptions, 
              enable_enterprise_modules=True, 
              allow_unsafe_jscode=True, 
              update_mode=GridUpdateMode.SELECTION_CHANGED)
              
    address = data['주소']
    
    count = 0
    lat = []
    lon = []
    
    for row in address:
        url = 'http://api.vworld.kr/req/address?'
        params = 'service=address&request=getcoord&version=2.0&crs=epsg:4326&refine=false&simple=false&format=json&type='
        road_type = 'road'
        address = '&address='
        keys = '&key='
        primary_key = st.secrets["primary_key"]

        r = requests.get(url+params+road_type+address+row+keys+primary_key)
        
        if r.json()['response']['status'] == 'NOT_FOUND' or r.json()['response']['status'] == 'ERROR':
            count += 1
            lat.append('')
            lon.append('')
            continue

        lon.append(float(r.json()['response']['result']['point']['x']))
        lat.append(float(r.json()['response']['result']['point']['y']))
        
        #df = df.append(pd.DataFrame([[lat, lon]], columns=['lat', 'lon']), ignore_index=True)
    st.write('검색되지 않는 주소 : ' ,count , '건')
    data['lat'] = lat
    data['lon'] = lon
    if select_grid['selected_rows'] :
        a =  list(map(lambda u: u["주소"], select_grid['selected_rows']))
        data = data[data['주소'] != '세종특별자치시 남세종로 440']
        map_insert(data)
    else :  
        map_insert(data)

def map_insert(data): 
    
    # Use pandas to calculate additional data
    # data["exits_radius"] = df["exits"].apply(lambda exits_count: math.sqrt(exits_count))
    icon_data = {
    "url": "https://img.icons8.com/plasticine/100/000000/marker.png",
    "width": 128,
    "height":128,
    "anchorY": 128
    }
    data['icon_data']= None
    for i in data.index:
        data['icon_data'][i] = icon_data
    center = [126.986,  35.189522]
    view_state = pdk.ViewState(
        longitude=center[0],
        latitude=center[1],
        zoom=6
    )
    data['lat'].replace('', np.nan, inplace=True)
    data.dropna(subset=['lat'], inplace=True)

    df = data
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/streets-v11',
        tooltip={"text":  "{지방청} {경찰서} {관서명}{구분}\n 주소 : {주소}\n lon:{lon} lat:{lat}"},
        initial_view_state=view_state,
        layers=[
            pdk.Layer(
                "IconLayer",
                data=df,
                get_position="[lon, lat]",
                get_icon="icon_data",
                get_size=4,
                pickable=True,
                size_scale=15,         
            ),
        ],
    ))

if __name__ == "__main__":
    main()
    
