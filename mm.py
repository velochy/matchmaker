import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Tournament matchmaker",
    #page_icon="./s-model.png",
    #initial_sidebar_state="expanded",
)

with st.spinner("Loading libraries.."):
    import pandas as pd, numpy as np
    from scipy.optimize import linear_sum_assignment

# TODO: input this from user
player_list = ['a','b','c','d','e','f']
rounds = 3

cnames = ['Name','Initial'] + sum([ [f'Round {i+1}', f'Score {i+1}', f'Tb {i+1}'] for i in range(rounds) ],[])

for cn,c in zip(cnames,st.columns(2 + 3*rounds )):
    c.write(cn)

rows = []

for p in player_list:
    cols = st.columns(2+3*rounds,vertical_alignment='bottom')
    row = [p]; cols[0].text(p); 
    row.append(cols[1].number_input(p+'|init',min_value=0, label_visibility='hidden'))
    row += sum([ [cols[2+3*i].selectbox(f'{p}|{i}|match',['Undecided']+player_list,label_visibility='hidden'), 
                  cols[3+3*i].number_input(f'{p}|{i}|score',min_value=0,label_visibility='hidden'),
                  cols[4+3*i].number_input(f'{p}|{i}|tb',min_value=0,label_visibility='hidden')
                  ] for i in range(rounds) ],[])
    rows.append(row)

df = pd.DataFrame(rows,columns=cnames)
df['Score'] = df[ [f'Score {i+1}' for i in range(rounds)] ].sum(axis=1)
df['Tiebraker'] = df[ [f'Tb {i+1}' for i in range(rounds)] ].sum(axis=1)

def mindiff(s):
    ds = np.diff(s.sort_values())
    if np.all(ds==0): return 1.0 
    return np.min(ds[np.nonzero(ds)])

# Make it so Tiebrakers are scaled to be smaller than the smallest score difference (and ditto for initial w.r.t. tiebrakers)
tb_s, i_s = mindiff(df['Score'])/(df['Tiebraker'].max()+1), mindiff(df['Tiebraker'])/(df['Initial'].max()+1)
df['Adj_score'] = df['Score'] + tb_s*(df['Tiebraker'] + i_s*df['Initial'])

#st.write(df)

def match():
            
    # Calculate the distance matrix
    score = np.array(df['Adj_score'])
    dist = (score[:,None]-score[None,:])**2
    inf = dist.max() + 10 # Effective infinity value - just larger than anything else on the table
    np.fill_diagonal(dist,inf)

    # Remove all prior pairings from consideration
    for ri in range(rounds):
        pairs = list(df.loc[df[f'Round {ri+1}'].isin(player_list),['Name',f'Round {ri+1}']].itertuples(index=False))
        for p in pairs:
            p1, p2 = player_list.index(p[0]),player_list.index(p[1])
            dist[p1,p2] = dist [p2,p1] = inf

    #st.write(dist)

    # Hungarian algorithm
    ris, cis = linear_sum_assignment(dist,maximize=False)
    match = zip(ris,cis)
    pla = np.array(player_list)
    return [ (pla[ri],pla[ci]) for ri,ci in match if ri<ci]


if st.button("Calculate matching"):
    for p1,p2 in match():
        st.text(f'{p1} - {p2}')
