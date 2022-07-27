import plotly.express as px
import pandas as pd

if __name__ == "__main__":
    csv_fname = './plots/ga_scenario3/export_run.csv'

    loc_pd = pd.read_csv(csv_fname)
    loc_pd = loc_pd[loc_pd['type'] == 0]
    fig = px.scatter_matrix(loc_pd, dimensions=[str(x) for x in range(6)], color='cluster')
    fig.update_traces(diagonal_visible=False)

    fig.show()