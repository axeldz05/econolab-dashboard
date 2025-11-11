import os
import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask import Flask, render_template

app = Flask(__name__)

# Configuration
CSV_FOLDER = 'csvs'
COLUMNS_TO_IGNORE = ['X_cycle_time', 'X_continuous_level', 'X_cycle_time', 'X_n_steps', 'X_phase', 'X_step_duration', 'X_step_index', 'X_step_progress', 'X_triangle', 'X_within_step']

def create_plot(csv_path):
    """
    Read a CSV file and create an interactive line plot
    with time on x-axis and toggleable legend items.
    """
    try:
        # Read CSV file[citation:3][citation:9]
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        if 'time' not in df.columns:
            print(f"Warning: 'time' column not found in {csv_path}")
            return None
        
        # Melt dataframe to long format for Plotly Express[citation:7]
        value_vars = [col for col in df.columns 
            if col != 'time' and col not in COLUMNS_TO_IGNORE]
        df_long = df.melt(id_vars=['time'], value_vars=value_vars, 
                         var_name='variable', value_name='value')
        
        # Create interactive line plot[citation:7]
        fig = px.line(df_long, x='time', y='value', color='variable',
                     title=os.path.basename(csv_path),
                     labels={'value': 'Value', 'time': 'Time'})
        
        # Customize legend and layout[citation:7]
        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Value',
            legend_title='Variables',
            hovermode='x unified',
            showlegend=True
        )
        
        # Convert to HTML div
        return pio.to_html(fig, full_html=False)
        
    except Exception as e:
        print(f"Error processing {csv_path}: {str(e)}")
        return None

@app.route('/')
def index():
    """Main dashboard route"""
    plot_divs = []
    filenames = []
    
    # Process all CSV files in the csvs folder[citation:5]
    if os.path.exists(CSV_FOLDER):
        for filename in os.listdir(CSV_FOLDER):
            if filename.endswith('.csv'):
                csv_path = os.path.join(CSV_FOLDER, filename)
                plot_html = create_plot(csv_path)
                
                if plot_html:
                    plot_divs.append(plot_html)
                    filenames.append(filename)
    
    return render_template('index.html', 
                         plots=plot_divs, 
                         filenames=filenames,
                         plot_count=len(plot_divs))

if __name__ == '__main__':
    app.run(debug=True)
